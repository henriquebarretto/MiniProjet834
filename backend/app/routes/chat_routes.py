# app/routes/chat_routes.py
from fastapi import APIRouter
from typing import List
from app.db.schemas import Message, MessageInDB
from app.db.connection import connection

router = APIRouter()

#access MongoDB database
db = connection.get_mongo_db()

@router.post("/messages", response_model=MessageInDB)
async def send_message(message: Message):
    #store new message in MongoDB
    result = db["messages"].insert_one(message.dict())
    return MessageInDB(id=str(result.inserted_id), **message.dict())

@router.get("/messages/{user1}/{user2}", response_model=List[MessageInDB])
async def get_conversation(user1: str, user2: str):
    #fetch conversation between user1 and user2
    query = {
        "$or": [
            {"sender": user1, "receiver": user2},
            {"sender": user2, "receiver": user1}
        ]
    }
    messages = db["messages"].find(query).sort("timestamp", 1)
    return [MessageInDB.from_mongo(m) for m in messages]
