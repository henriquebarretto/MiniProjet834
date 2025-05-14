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

#MONGO_URL = "mongodb://localhost:27017" #pas de replicaset
MONGO_URL = "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0" #avec replicaset
client = AsyncIOMotorClient(MONGO_URL)
db = client["chat_db"]
messages_collection = db["messages"]

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users_db = {
    "alice": {"username": "alice", "password": "1234"},
    "bob": {"username": "bob", "password": "1234"},
    "dan": {"username": "dan", "password": "1234"},
    "henrique": {"username": "henrique", "password": "1234"},
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

    connected_users[username] = websocket
    print(f"{username} connecté.")

    # Buscar mensagens onde o usuário é remetente ou destinatário
    cursor = messages_collection.find({"$or": [{"from": username}, {"to": username}]})
    async for msg in cursor:
        await websocket.send_text(
            json.dumps(
                {"from": msg["from"], "to": msg["to"], "message": msg["message"]}
            )
        )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                recipient = parsed["to"]
                message = parsed["message"]
            except (json.JSONDecodeError, KeyError):
                await websocket.send_text("⚠️ Format de message invalide.")
                continue

            msg_obj = {"from": username, "to": recipient, "message": message}

            await messages_collection.insert_one(msg_obj)

            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            if recipient in connected_users:
                msg_to_send = dict(msg_obj)
                msg_to_send.pop("_id", None)  # Remove _id se estiver presente
                await connected_users[recipient].send_text(json.dumps(msg_to_send))

    except WebSocketDisconnect:
        del connected_users[username]
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
