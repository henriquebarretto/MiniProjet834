from pydantic import BaseModel
from datetime import datetime 
from bson import ObjectId
from typing import Optional

class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class config():
    orm_mode = True 


class UserInDB(User):
    id: str

    @classmethod
    def from_mongo(cls, db_item):
        db_item['id'] = str(db_item['_id']) 
        return cls(**db_item)
    
    class Config:
        orm_mode = True

class Message(BaseModel):
    sender: str
    receiver: str
    content: str
    timestamp: datetime = datetime.utcnow()

    class Config:
        orm_mode = True

class MessageInDB(Message):
    id: str  # Representando o ObjectId como uma string

    @classmethod
    def from_mongo(cls, db_item):
        db_item['id'] = str(db_item['_id'])  # Converte o ObjectId para string
        return cls(**db_item)

    class Config:
        orm_mode = True