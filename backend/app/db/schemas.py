#backend/app/db/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

#base structure for user
class User(BaseModel):
    id: Optional[str] = None  
    username: str             
    email: str                
    created_at: datetime = Field(default_factory=datetime.utcnow)  #automatically set to current UTC datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)  #automatically set to current UTC datetime

    class Config:
        orm_mode = True  #allows reading data from ORM objects or MongoDB-style documents

#extends the User model for database use, where 'id' is now required
class UserInDB(User):
    id: str  #required user ID (MongoDB ObjectId as string)

    @classmethod
    def from_mongo(cls, db_item):
        db_item['id'] = str(db_item['_id'])  #convert MongoDB '_id' to string and assign to 'id'
        return cls(**db_item)  #create a UserInDB instance with the updated dictionary

    class Config:
        orm_mode = True  #enables ORM mode for compatibility with database objects

#structure of a chat message
class Message(BaseModel):
    sender: str    
    receiver: str  
    content: str   
    timestamp: datetime = Field(default_factory=datetime.utcnow)  #timestamp of the message (auto-set)

    class Config:
        orm_mode = True 

#extends the Message model for database use
class MessageInDB(Message):
    id: str  # MongoDB ObjectId converted to string

    @classmethod
    def from_mongo(cls, db_item):
        db_item['id'] = str(db_item['_id'])  #convert MongoDB '_id' to string
        return cls(**db_item)  #create a MessageInDB instance with the updated dictionary

    class Config:
        orm_mode = True  #enables compatibility with database documents
