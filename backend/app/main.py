# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.utils.redis_manager import add_user_online, remove_user_online
from app.routes import routers
from app.db.connection import Connection


app = FastAPI()

#store active WebSocket connections
connections = {}

#initialize MongoDB and Redis 
@app.on_event("startup")
def startup_event():
    connection = Connection()
    app.state.mongo_db = connection.get_mongo_db()
    print(f"Connected to MongoDB: {app.state.mongo_db.name}")
    
    app.state.redis_client = connection.get_redis_client()
    print("Connected to Redis")

#webSocket endpoint for real-time communication
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connections[username] = websocket
    add_user_online(username)

    try:
        while True:
            data = await websocket.receive_text()
            #handle incoming message 
    except WebSocketDisconnect:
        connections.pop(username, None)
        remove_user_online(username)


for router in routers:
    app.include_router(router)

#command to run with uvicon
#uvicorn backend.app.main:app --reload
