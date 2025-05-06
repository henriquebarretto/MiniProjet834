# tests/test_redis_tracking.py

import pytest
import redis
from datetime import datetime
from backend.app.utils.redis_manager import (
    r,
    ONLINE_USERS_KEY,
    add_user_online,
    remove_user_online,
    get_online_users,
    get_user_status,
)

@pytest.fixture(autouse=True)
def clean_redis():
    # Before each test, clear all keys in Redis
    r.flushdb()
    yield
    r.flushdb()

def test_add_and_get_online_user():
    # Should be empty initially
    assert get_online_users() == []

    # Add a user
    add_user_online("alice")
    online = get_online_users()
    assert "alice" in online

    # Check the hash for status and last_seen
    status = get_user_status("alice")
    assert status["status"] == "online"
    # last_seen should be present and in ISO8601 format
    datetime.fromisoformat(status["last_seen"])

def test_remove_user_online():
    add_user_online("bob")
    assert "bob" in get_online_users()

    # Remove bob
    remove_user_online("bob")
    assert "bob" not in get_online_users()

    status = get_user_status("bob")
    # Even if not in the set, the hash should be created/updated to 'offline'
    assert status["status"] == "offline"

def test_multiple_users():
    add_user_online("alice")
    add_user_online("bob")
    users = set(get_online_users())
    assert users == {"alice", "bob"}

    # Remove one user
    remove_user_online("alice")
    assert set(get_online_users()) == {"bob"}

def test_redis_connection_failure(monkeypatch):
    # Simulate a connection failure in add_user_online
    monkeypatch.setattr(r, "sadd", lambda *args, **kwargs: (_ for _ in ()).throw(redis.exceptions.ConnectionError()))
    with pytest.raises(Exception) as exc:
        add_user_online("charlie")
    assert "Redis connection failed" in str(exc.value)
