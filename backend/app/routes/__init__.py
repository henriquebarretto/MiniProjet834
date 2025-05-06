# __init__.py

from .chat_routes import router as chat_router
from .user_routes import router as user_router

routers = [chat_router, user_router]
