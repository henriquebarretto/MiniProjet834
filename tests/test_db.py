# tests/test_connection.py

import unittest
from backend.app.db.connection import Connection

class TestConnection(unittest.TestCase):

    def test_mongo_connection(self):
        connection = Connection()
        mongo_db = connection.get_mongo_db()
        self.assertIsNotNone(mongo_db)
        self.assertEqual(mongo_db.name, "chat")

    def test_redis_connection(self):
        connection = Connection()
        redis_client = connection.get_redis_client()
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        self.assertEqual(value, "test_value")

if __name__ == "__main__":
    unittest.main()
