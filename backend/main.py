# backend/app/main.py

from backend.app.db.connection import Connection

def main():
    connection = Connection()

    mongo_db = connection.get_mongo_db()
    print(f"Conectado ao MongoDB: {mongo_db.name}")

    redis_client = connection.get_redis_client()
    print("Conectado ao Redis")

if __name__ == "__main__":
    main()
