from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Form,
)
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi import status
from typing import Dict
from fastapi import Header
import secrets
import sys
import os
import json

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users_db = {
    "alice": {"username": "alice", "password": "1234"},
    "bob": {"username": "bob", "password": "5678"},
}

tokens: Dict[str, str] = {}

# Armazena mensagens pendentes: {"bob": ["alice: Olá", ...]}
pending_messages: dict[str, list[str]] = {}


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


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Autoriser les requêtes CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # En développement seulement ; en production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stocker les connexions WebSocket par nom d'utilisateur
connected_users: dict[str, WebSocket] = {}

# Histórico de conversas: {"alice": {"bob", "carol"}, ...}
user_conversations: dict[str, set[str]] = {}


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

    # Enviar mensagens pendentes (se houver)
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
            except (json.JSONDecodeError, KeyError):
                await websocket.send_text("⚠️ Format de message invalide.")
                continue

            # Armazena que 'username' conversou com 'recipient'
            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            # Envia para o destinatário se ele estiver online
            msg_to_send = f"{username} : {message}"

            # Atualiza o histórico
            user_conversations.setdefault(username, set()).add(recipient)
            user_conversations.setdefault(recipient, set()).add(username)

            # Envia ou armazena
            if recipient in connected_users:
                await connected_users[recipient].send_text(msg_to_send)
            else:
                pending_messages.setdefault(recipient, []).append(msg_to_send)

    except WebSocketDisconnect:
        del connected_users[username]
        print(f"{username} déconnecté.")


@app.get("/contacts")
async def get_contacts(token: str = Header(...)):
    username = get_username_by_token(token)
    contacts = list(user_conversations.get(username, set()))
    return {"contacts": contacts}


@app.get("/users")
async def list_users(token: str = Header(...)):
    current_user = get_username_by_token(token)
    return {"users": [u for u in users_db if u != current_user]}
