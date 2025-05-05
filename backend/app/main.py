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
import secrets
import sys
import os

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users_db = {
    "alice": {"username": "alice", "password": "1234"},
    "bob": {"username": "bob", "password": "5678"},
}

tokens: Dict[str, str] = {}


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

    try:
        while True:
            data = await websocket.receive_text()
            for user, conn in connected_users.items():
                await conn.send_text(f"{username} : {data}")
    except WebSocketDisconnect:
        del connected_users[username]
        print(f"{username} déconnecté.")
