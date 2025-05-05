import unittest
from backend.app.models.user import UserModel
from backend.app.db.schemas import UserInDB
from bson import ObjectId
from unittest.mock import MagicMock

class TestUserModel(unittest.TestCase):

    def test_create_and_get_user(self):
        user_model = UserModel()

        
        fake_object_id = ObjectId()
        fake_id_str = str(fake_object_id)

        
        new_user = UserInDB(id=fake_id_str, username="testuser", email="testuser@example.com")
        
        
        user_model.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=fake_object_id))
        
        # Criar o usuário
        created_user = user_model.create_user(new_user)

        self.assertEqual(created_user.username, "testuser")
        self.assertEqual(created_user.email, "testuser@example.com")
        self.assertEqual(created_user.id, fake_id_str)

        # Simular retorno do banco ao buscar esse ID
        user_model.collection.find_one = MagicMock(return_value={
            "_id": fake_object_id,
            "username": "testuser",
            "email": "testuser@example.com"
        })

        # Buscar o usuário com o mesmo id
        fetched_user = user_model.get_user(fake_id_str)

        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.username, "testuser")
        self.assertEqual(fetched_user.email, "testuser@example.com")

if __name__ == "__main__":
    unittest.main()
