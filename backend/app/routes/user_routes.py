from fastapi import APIRouter
from app.utils.redis_manager import get_online_users

router = APIRouter()

@router.get("/online-users")
def online_users():
    return {"online_users": get_online_users()}
