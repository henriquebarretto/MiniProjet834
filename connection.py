from pymongo import MongoClient
import redis 
#from app.config import MONGODB_URI, MONGODB_DB

def connect_mongodb():
    uri = "mongodb://localhost:27017" 
    client = MongoClient(uri)
    db = client["chat"]
    #
    #client = MongoClient(MONGODB_URI)
    #db = client[MONGODB_DB]
    return db

def connect_redis():
    r = redis.StrictRedis(host='localhost', port = 6379, db=0, decode_responses=True)
    return r

if __name__ == "__main__":
    db = connect_mongodb()
    print(f"Connect to the database {db.name}")
    redis = connect_redis()
    print("Connected to Redis")
