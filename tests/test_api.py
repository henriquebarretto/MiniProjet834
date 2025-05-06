# test_api.py
from app.utils.redis_manager import add_user_online, get_online_users, remove_user_online

def test_add_and_remove_user():
    username = "testuser"
    add_user_online(username)
    assert username in get_online_users()
    remove_user_online(username)
    assert username not in get_online_users()
