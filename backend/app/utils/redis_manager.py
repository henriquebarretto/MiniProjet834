import redis
from datetime import datetime
from fastapi import HTTPException

r = redis.Redis(host='redis', port=6379, decode_responses=True)

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
