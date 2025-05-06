from backend.app.db.schemas import UserInDB
from backend.app.db.connection import Connection
from bson import ObjectId

class UserModel:

    def __init__(self):
        self.connection= Connection()
        self.db = self.connection.get_mongo_db()
        self.collection = self.db["users"]


    def create_user(self, user_data: UserInDB):
        user_dict = user_data.dict(exclude_unset=True)
        result = self.collection.insert_one(user_dict)
        user_data.id = str(result.inserted_id)
        return user_data
    
    def get_user(self, user_id: str):
        if not ObjectId.is_valid(user_id):
            raise ValueError("ID inválido para o usuário")

        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserInDB.from_mongo(user)
        return None