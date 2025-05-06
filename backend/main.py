# backend/app/main.py

from backend.app.db.connection import Connection

def main():
    connection = Connection()

    mongo_db = connection.get_mongo_db()
    print(f"Conected to MongoDB: {mongo_db.name}")

    redis_client = connection.get_redis_client()
    print("Conected to Redis")

if __name__ == "__main__":
    main()
