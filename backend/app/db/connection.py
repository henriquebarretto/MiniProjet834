# app/db/connection.py
from pymongo import MongoClient
import redis
import motor.motor_asyncio

class Connection:
    def __init__(self, mongo_uri="mongodb://localhost:27017", redis_host="localhost", redis_port=6379, redis_db=0):
        #initialize MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client["chat"]
        #initialize redis connection
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

    @staticmethod
    def get_mongo_db():
        #return MongoDB database instance
        client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
        db = client["chat_db"] #mongoDB database "chat_db"
        return db

    def get_redis_client(self):
        #return the Redis client instance
        return self.redis_client

#global instancy
connection = Connection()
