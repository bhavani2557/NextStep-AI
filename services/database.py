
import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

_client = None
_client_uri = None


def get_setting(name, default=""):
    """Read Streamlit Cloud Secrets first, then local environment variables."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


def collection(name="profiles"):
    """Return a MongoDB collection, or None when unavailable."""
    global _client, _client_uri

    uri = get_setting("MONGODB_URI")
    if not uri:
        print("MongoDB configuration error: MONGODB_URI is missing.")
        return None

    try:
        if _client is None or _client_uri != uri:
            if _client is not None:
                _client.close()

            _client = MongoClient(
                uri,
                serverSelectionTimeoutMS=10000,
            )
            _client_uri = uri

        _client.admin.command("ping")

        database_name = get_setting(
            "MONGODB_DATABASE",
            "career_agent",
        )

        return _client[database_name][name]

    except PyMongoError as exc:
        # Log the error type without printing credentials or the URI.
        print(
            f"MongoDB connection error: {type(exc).__name__}"
        )
        return None


def save_profile(profile: dict, profile_id: str):
    """Insert or update the profile associated with this browser ID."""
    if not profile_id:
        return {
            "saved": False,
            "message": "Profile ID is missing.",
        }

    col = collection("profiles")

    if col is None:
        return {
            "saved": False,
            "message": (
                "MongoDB is not configured or reachable. "
                "Profile remains available in this session."
            ),
        }

    try:
        document = {
            **profile,
            "profile_id": profile_id,
            "updated_at": datetime.now(timezone.utc),
        }

        col.replace_one(
            {"profile_id": profile_id},
            document,
            upsert=True,
        )

        return {
            "saved": True,
            "message": "Profile saved to MongoDB.",
        }

    except PyMongoError as exc:
        print(f"MongoDB profile-save error: {type(exc).__name__}")

        return {
            "saved": False,
            "message": (
                f"Database save failed: {type(exc).__name__}"
            ),
        }


def load_profile(profile_id: str):
    """Load only the profile matching this browser's profile ID."""
    if not profile_id:
        return None

    col = collection("profiles")

    if col is None:
        return None

    try:
        document = col.find_one({"profile_id": profile_id})

        if document is None:
            return None

        document.pop("_id", None)
        document.pop("profile_id", None)
        document.pop("updated_at", None)

        return document

    except PyMongoError as exc:
        print(f"MongoDB profile-load error: {type(exc).__name__}")
        return None


def save_chat(user_message: str, assistant_message: str):
    """Save a chat exchange when MongoDB is available."""
    col = collection("chat_history")

    if col is None:
        return

    try:
        col.insert_one({
            "user_message": user_message,
            "assistant_message": assistant_message,
            "created_at": datetime.now(timezone.utc),
        })

    except PyMongoError as exc:
        print(f"MongoDB chat-save error: {type(exc).__name__}")
