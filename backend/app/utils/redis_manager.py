import os, redis
from datetime import datetime
from fastapi import HTTPException

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

ONLINE_USERS_KEY = "online_users"

def add_user_online(username: str):
    try:
        r.sadd(ONLINE_USERS_KEY, username)
        r.hset(f"user:{username}", mapping={
            "status": "online",
            "last_seen": datetime.utcnow().isoformat()
        })
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Redis connection failed")

def remove_user_online(username: str):
    r.srem(ONLINE_USERS_KEY, username)
    r.hset(f"user:{username}", "status", "offline")

def get_online_users():
    return list(r.smembers(ONLINE_USERS_KEY))

def get_user_status(username: str):
    return r.hgetall(f"user:{username}")
