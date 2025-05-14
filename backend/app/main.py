# Importation des modules FastAPI nécessaires pour gérer les routes HTTP, WebSockets et la sécurité
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Form,
    Header,
)
# Middleware pour gérer les politiques CORS (Cross-Origin Resource Sharing)
from fastapi.middleware.cors import CORSMiddleware
# Outil d'authentification basé sur OAuth2
from fastapi.security import OAuth2PasswordBearer
from typing import Dict
import secrets  # Utilisé pour générer des jetons sécurisés
import sys
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient  # Client MongoDB asynchrone
from fastapi import Query
from jose import JWTError, jwt  # Pour décoder les tokens JWT
import redis  # Pour la gestion du cache et des statuts utilisateurs
from datetime import datetime  # Pour les horodatages

# Connexion au serveur Redis local
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Test de la connexion à Redis
try:
    response = r.ping()  # Envoie un ping pour vérifier si Redis répond
    if response:
        print("Redis ça marche!")
except redis.ConnectionError as e:
    print(f"Redis ne peut pas se connectée {e}")

# Clé secrète et algorithme pour les tokens JWT
SECRET_KEY = "seu_seguro_segredo"
ALGORITHM = "HS256"

# Fonction pour décoder un token JWT
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise ValueError("Token invalide: sem 'sub'")
        return username
    except JWTError:
        raise ValueError("Token invalide")

# Enregistre un horodatage de connexion de l'utilisateur dans Redis
def log_user_login(username: str):
    timestamp = datetime.utcnow().isoformat()
    r.lpush(f"logins:{username}", timestamp)
    r.set(f"online:{username}", 1)

# Enregistre un horodatage de déconnexion de l'utilisateur dans Redis
def log_user_logout(username: str):
    timestamp = datetime.utcnow().isoformat()
    r.lpush(f"logouts:{username}", timestamp)
    r.delete(f"online:{username}")

# Connexion à MongoDB (avec réplica set activé)
#MONGO_URL = "mongodb://localhost:27017" #pas de replicaset
MONGO_URL = "mongodb://localhost:27017,localhost:27018,localhost:27019,localhost:27020/?replicaSet=rs0" #avec replicaset
client = AsyncIOMotorClient(MONGO_URL)
db = client["chat_db"]
messages_collection = db["messages"]  # Collection MongoDB pour les messages

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Base de données fictive des utilisateurs
users_db = {
    "fran": {"username": "fran", "password": "1234"},
    "sol": {"username": "sol", "password": "1234"},
    "dan": {"username": "dan", "password": "1234"},
    "rique": {"username": "rique", "password": "1234"},
}

tokens: Dict[str, str] = {}  # Stockage des tokens actifs

# Historique des messages par utilisateur
message_history: dict[str, dict[str, list[dict]]] = {}

# Middleware CORS pour autoriser les connexions depuis n'importe quelle origine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_users: dict[str, WebSocket] = {}  # Utilisateurs actuellement connectés
user_conversations: dict[str, set[str]] = {}  # Conversations actives par utilisateur

# Endpoint POST pour la connexion utilisateur
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if user and secrets.compare_digest(user["password"], password):
        token = secrets.token_hex(16)
        tokens[token] = username
        log_user_login(username)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Récupère le nom d'utilisateur associé à un token
def get_username_by_token(token: str) -> str:
    username = tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

# Endpoint racine, simple message de bienvenue
@app.get("/")
async def root():
    return {"message": "API de chat avec WebSocket opérationnelle !"}

# Endpoint WebSocket pour gérer les connexions de chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    token = websocket.query_params.get("token")

    try:
        username = get_username_by_token(token)
    except HTTPException:
        await websocket.send_text("❌ Token invalide.")
        await websocket.close()
        return

    # Ajout de l'utilisateur dans le dictionnaire des utilisateurs connectés
    connected_users[username] = websocket

    # Marque l'utilisateur comme "en ligne" dans Redis
    r.set(f"user:{username}", "online")

    print(f"{username} connecté.")

    # Envoie l'historique des messages de l'utilisateur à la connexion
    cursor = messages_collection.find({"$or": [{"from": username}, {"to": username}]})
    async for msg in cursor:
        await websocket.send_text(
            json.dumps(
                {"from": msg["from"], "to": msg["to"], "message": msg["message"]}
            )
        )

    try:
        while True:
            # Réception des nouveaux messages du client
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                recipient = parsed["to"]
                message = parsed["message"]
            except (json.JSONDecodeError, KeyError):
                await websocket.send_text("⚠️ Format de message invalide.")
                continue

            msg_obj = {"from": username, "to": recipient, "message": message}

            # Enregistrement du message dans MongoDB
            await messages_collection.insert_one(msg_obj)

            # Mise à jour des conversations des deux utilisateurs
            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            # Envoie du message au destinataire s'il est connecté
            if recipient in connected_users:
                msg_to_send = dict(msg_obj)
                msg_to_send.pop("_id", None)  # Supprime _id si présent
                await connected_users[recipient].send_text(json.dumps(msg_to_send))

    except WebSocketDisconnect:
        # Gestion de la déconnexion du WebSocket
        del connected_users[username]
        r.set(f"user:{username}", "offline")  # Marque l'utilisateur comme "hors ligne"
        log_user_logout(username)
        print(f"{username} déconnecté.")

# Endpoint pour obtenir la liste des contacts avec lesquels l'utilisateur a échangé des messages
@app.get("/contacts")
async def get_contacts(token: str = Header(...)):
    username = get_username_by_token(token)

    # Pipeline d'agrégation pour extraire les contacts uniques
    pipeline = [
        {"$match": {"$or": [{"from": username}, {"to": username}]}},
        {
            "$project": {
                "contact": {"$cond": [{"$eq": ["$from", username]}, "$to", "$from"]}
            }
        },
        {"$group": {"_id": "$contact"}},
    ]
    results = await messages_collection.aggregate(pipeline).to_list(length=None)
    contacts = [doc["_id"] for doc in results]

    return {"contacts": contacts}

# Endpoint pour lister les utilisateurs (hors utilisateur actuel)
@app.get("/users")
async def list_users(token: str = Header(...)):
    current_user = get_username_by_token(token)
    return {"users": [u for u in users_db if u != current_user]}

# Endpoint pour supprimer la conversation entre l'utilisateur actuel et un autre utilisateur
@app.delete("/chat/{target_user}")
async def delete_chat(target_user: str, token: str = Header(...)):
    username = get_username_by_token(token)
    await messages_collection.delete_many(
        {
            "$or": [
                {"from": username, "to": target_user},
                {"from": target_user, "to": username},
            ]
        }
    )
    return {"status": "ok", "message": f"Conversation avec {target_user} supprimée."}

# Endpoint pour lister les utilisateurs actuellement "en ligne" dans Redis
@app.get("/online-users")
def list_online_users():
    keys = r.keys("user:*")
    return [key.replace("user:", "") for key in keys]
