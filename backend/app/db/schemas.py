from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
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
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

class MessageInDB(Message):
    id: str  #ObjectId as string

    @classmethod
    def from_mongo(cls, db_item):
        db_item['id'] = str(db_item['_id'])  #objectId to string
        return cls(**db_item)

    class Config:
        orm_mode = True
