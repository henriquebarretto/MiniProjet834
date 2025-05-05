from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

# Autoriser les requêtes CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En développement seulement ; en production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stocker les connexions WebSocket par nom d'utilisateur
connected_users: dict[str, WebSocket] = {}

@app.get("/")
async def root():
    return {"message": "API de chat avec WebSocket opérationnelle !"}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connected_users[username] = websocket
    print(f"{username} s'est connecté.")

    try:
        while True:
            # Recevoir un message texte de l'utilisateur
            data = await websocket.receive_text()
            print(f"Message reçu de {username} : {data}")

            # Envoyer le message à tous les autres utilisateurs connectés
            for user, conn in connected_users.items():
                    await conn.send_text(f"{username} : {data}")

    except WebSocketDisconnect:
        # Supprimer l'utilisateur déconnecté
        del connected_users[username]
        print(f"{username} s'est déconnecté.")
