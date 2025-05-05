# backend/app/db/connection.py

from pymongo import MongoClient
import redis

class Connection:
    def __init__(self, mongo_uri="mongodb://localhost:27017", redis_host="localhost", redis_port=6379, redis_db=0):
        # Conexão com MongoDB
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client["chat"]

        # Conexão com Redis
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

    def get_mongo_db(self):
        return self.mongo_db

    def get_redis_client(self):
        return self.redis_client

