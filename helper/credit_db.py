import json
from motor.motor_asyncio import AsyncIOMotorClient

import os

# Try to get MongoDB URI from environment variables first (For Koyeb/Docker)
MONGO_URI = os.getenv("DATABASE_URI")
DB_NAME = os.getenv("DATABASE_NAME", "file_share_bot")

# If environment variable is missing, fallback to setup.json
if not MONGO_URI:
    try:
        with open("setup.json", "r") as f:
            data = json.load(f)
            config = data[0]
            MONGO_URI = config["db_uri"]
            DB_NAME = config.get("db_name", "file_share_bot")
    except Exception:
        MONGO_URI = "mongodb://localhost:27017" # Dummy fallback

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

credit_col = db["credits"]


class CreditDB:

    # Get user credit count
    async def get(self, user_id):
        data = await credit_col.find_one({"_id": user_id})
        return data["credits"] if data else 0

    # Add credits
    async def add(self, user_id, amount=3):
        await credit_col.update_one(
            {"_id": user_id},
            {"$inc": {"credits": amount}},
            upsert=True
        )

    # Deduct 1 credit
    async def use(self, user_id):
        await credit_col.update_one(
            {"_id": user_id},
            {"$inc": {"credits": -1}}
        )

    # Reset user credits to zero
    async def reset(self, user_id):
        await credit_col.update_one(
            {"_id": user_id},
            {"$set": {"credits": 0}},
            upsert=True
        )


credit_db = CreditDB()
