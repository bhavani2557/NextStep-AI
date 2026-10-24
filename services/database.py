
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

_client = None


def collection(name="profiles"):
    global _client

    uri = os.getenv("MONGODB_URI", "").strip()

    if not uri:
        return None

    try:
        if _client is None:
            _client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000
            )

        _client.admin.command("ping")

        database_name = os.getenv(
            "MONGODB_DATABASE",
            "career_agent"
        )

        db = _client[database_name]
        return db[name]

    except PyMongoError:
        return None


def save_profile(profile: dict):
    col = collection("profiles")

    if col is None:
        return {
            "saved": False,
            "message": (
                "MongoDB is not configured or reachable. "
                "Profile remains available in this session."
            )
        }

    try:
        result = col.insert_one(profile)

        return {
            "saved": True,
            "id": str(result.inserted_id),
            "message": "Profile saved to MongoDB."
        }

    except PyMongoError as exc:
        return {
            "saved": False,
            "message": (
                f"Database save failed: "
                f"{exc.__class__.__name__}"
            )
        }


def save_chat(user_message: str, assistant_message: str):
    col = collection("chat_history")

    if col is None:
        return

    try:
        col.insert_one({
            "user_message": user_message,
            "assistant_message": assistant_message
        })

    except PyMongoError:
        pass
