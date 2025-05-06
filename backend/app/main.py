from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi import status
from typing import Dict
import secrets
import sys
import os
import json

from app.utils.redis_manager import add_user_online, remove_user_online
from app.routes import routers
from app.db.connection import Connection

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock user DB
users_db = {
    "alice": {"username": "alice", "password": "1234"},
    "bob": {"username": "bob", "password": "5678"},
}

tokens: Dict[str, str] = {}
connected_users: dict[str, WebSocket] = {}
pending_messages: dict[str, list[str]] = {}
user_conversations: dict[str, set[str]] = {}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB + Redis
@app.on_event("startup")
def startup_event():
    connection = Connection()
    app.state.mongo_db = connection.get_mongo_db()
    app.state.redis_client = connection.get_redis_client()
    print("✅ Mongo & Redis conectados")

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
    add_user_online(username)

    for msg in pending_messages.get(username, []):
        await websocket.send_text(msg)
    pending_messages[username] = []

    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                recipient = parsed["to"]
                message = parsed["message"]
            except:
                await websocket.send_text("⚠️ Format de message invalide.")
                continue

            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            msg_to_send = f"{username} : {message}"
            if recipient in connected_users:
                await connected_users[recipient].send_text(msg_to_send)
            else:
                pending_messages.setdefault(recipient, []).append(msg_to_send)

    except WebSocketDisconnect:
        del connected_users[username]
        remove_user_online(username)

@app.get("/contacts")
async def get_contacts(token: str = Header(...)):
    username = get_username_by_token(token)
    return {"contacts": list(user_conversations.get(username, set()))}

@app.get("/users")
async def list_users(token: str = Header(...)):
    current_user = get_username_by_token(token)
    return {"users": [u for u in users_db if u != current_user]}

# Inclui rotas de outras partes do sistema
for router in routers:
    app.include_router(router)
