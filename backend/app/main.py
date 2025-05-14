from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Form,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Dict
import secrets
import sys
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Query
from jose import JWTError, jwt
import redis
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Testando a conexão
try:
    response = r.ping()  # Envia um ping para o Redis
    if response:
        print("Conexão com Redis bem-sucedida!")
except redis.ConnectionError as e:
    print(f"Erro ao conectar no Redis: {e}")

SECRET_KEY = "seu_seguro_segredo"
ALGORITHM = "HS256"


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise ValueError("Token inválido: sem 'sub'")
        return username
    except JWTError:
        raise ValueError("Token inválido")


def log_user_login(username: str):
    timestamp = datetime.utcnow().isoformat()
    r.lpush(f"logins:{username}", timestamp)
    r.set(f"online:{username}", 1)


def log_user_logout(username: str):
    timestamp = datetime.utcnow().isoformat()
    r.lpush(f"logouts:{username}", timestamp)
    r.delete(f"online:{username}")


#MONGO_URL = "mongodb://localhost:27017" #pas de replicaset
MONGO_URL = "mongodb://localhost:27017,localhost:27018,localhost:27019,localhost:27020/?replicaSet=rs0" #avec replicaset
client = AsyncIOMotorClient(MONGO_URL)
db = client["chat_db"]
messages_collection = db["messages"]

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users_db = {
    "fran": {"username": "fran", "password": "1234"},
    "sol": {"username": "sol", "password": "1234"},
    "dan": {"username": "dan", "password": "1234"},
    "rique": {"username": "rique", "password": "1234"},
}

tokens: Dict[str, str] = {}

# Histórico de mensagens: { "usuario": { "destinatario": [ {from, to, message}, ... ] } }
message_history: dict[str, dict[str, list[dict]]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_users: dict[str, WebSocket] = {}
user_conversations: dict[str, set[str]] = {}


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if user and secrets.compare_digest(user["password"], password):
        token = secrets.token_hex(16)
        tokens[token] = username
        log_user_login(username)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")


def get_username_by_token(token: str) -> str:
    username = tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


@app.get("/")
async def root():
    return {"message": "API de chat avec WebSocket opérationnelle !"}


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

    # Add the user to the connected_users dictionary
    connected_users[username] = websocket
    print(f"{username} connecté.")

    # Set the user as 'online' in Redis
    r.set(f"user:{username}", "online")

    # Fetch and send the user's message history (messages where the user is either the sender or recipient)
    cursor = messages_collection.find({"$or": [{"from": username}, {"to": username}]})
    async for msg in cursor:
        await websocket.send_text(
            json.dumps(
                {"from": msg["from"], "to": msg["to"], "message": msg["message"]}
            )
        )

    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                recipient = parsed["to"]
                message = parsed["message"]
            except (json.JSONDecodeError, KeyError):
                await websocket.send_text("⚠️ Format de message invalide.")
                continue

            msg_obj = {"from": username, "to": recipient, "message": message}

            # Store the message in MongoDB
            await messages_collection.insert_one(msg_obj)

            # Update the conversations for both the sender and recipient
            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            # If the recipient is connected, send the message to them
            if recipient in connected_users:
                msg_to_send = dict(msg_obj)
                msg_to_send.pop("_id", None)  # Remove _id if present
                await connected_users[recipient].send_text(json.dumps(msg_to_send))

    except WebSocketDisconnect:
        # When the WebSocket is disconnected, remove the user from connected_users and set them as 'offline' in Redis
        del connected_users[username]
        r.set(f"user:{username}", "offline")  # Set user status as offline
        log_user_logout(username)
        print(f"{username} déconnecté.")


@app.get("/contacts")
async def get_contacts(token: str = Header(...)):
    username = get_username_by_token(token)

    # Consulta no MongoDB para descobrir com quem o usuário trocou mensagens
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


@app.get("/users")
async def list_users(token: str = Header(...)):
    current_user = get_username_by_token(token)
    return {"users": [u for u in users_db if u != current_user]}


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


@app.get("/online-users")
def list_online_users():
    keys = r.keys("user:*")
    return [key.replace("user:", "") for key in keys]
