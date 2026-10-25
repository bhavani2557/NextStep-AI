"""MongoDB persistence helpers for NextStep AI.

Reads Streamlit Community Cloud secrets first, then local environment variables.
Never print the MongoDB URI or credentials to logs.
"""

import os
import re
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

_client = None
_client_uri = None


def get_setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets, falling back to environment variables."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        # Streamlit secrets may not exist in local development.
        pass

    return str(os.getenv(name, default) or default).strip()


def _safe_error_message(exc: Exception, uri: str = "") -> str:
    """Return useful exception detail without leaking connection credentials."""
    message = str(exc)
    if uri:
        message = message.replace(uri, "<MongoDB URI redacted>")
    # Redact credential-like values if they appear in a driver error message.
    message = re.sub(r"(mongodb(?:\+srv)?://)[^\s/@]+:[^\s/@]+@", r"\1<credentials-redacted>@", message)
    return message[:1000]


def collection(name: str = "profiles"):
    """Return the requested MongoDB collection, or None if unavailable."""
    global _client, _client_uri

    uri = get_setting("MONGODB_URI")
    if not uri:
        print("MongoDB configuration error: MONGODB_URI is missing.")
        return None

    try:
        if _client is None or _client_uri != uri:
            if _client is not None:
                _client.close()
            _client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            _client_uri = uri

        # Force a connection attempt now, so failures are logged at the point of use.
        _client.admin.command("ping")
        database_name = get_setting("MONGODB_DATABASE", "career_agent") or "career_agent"
        return _client[database_name][name]
    except PyMongoError as exc:
        detail = _safe_error_message(exc, uri)
        print(f"MongoDB connection error: {type(exc).__name__}: {detail}")
        return None
    except Exception as exc:
        detail = _safe_error_message(exc, uri)
        print(f"MongoDB unexpected connection error: {type(exc).__name__}: {detail}")
        return None


def save_profile(profile: dict, profile_id: str) -> dict:
    """Insert or update the profile associated with this browser's profile ID."""
    if not profile_id:
        print("Profile save error: profile_id is missing.")
        return {"saved": False, "message": "Profile ID is missing."}

    if not isinstance(profile, dict):
        print(f"Profile save error: expected dict, received {type(profile).__name__}.")
        return {"saved": False, "message": "Profile data is invalid."}

    col = collection("profiles")
    if col is None:
        return {
            "saved": False,
            "message": "MongoDB is not configured or reachable. Profile is only available in this session.",
        }

    try:
        document = {
            **profile,
            "profile_id": profile_id,
            "updated_at": datetime.now(timezone.utc),
        }
        result = col.replace_one({"profile_id": profile_id}, document, upsert=True)
        if result.acknowledged:
            print(
                "Profile saved to MongoDB: "
                f"matched={result.matched_count}, upserted={result.upserted_id is not None}."
            )
            return {"saved": True, "message": "Profile saved to MongoDB."}

        print("Profile save error: MongoDB did not acknowledge the write.")
        return {"saved": False, "message": "MongoDB did not confirm the profile write."}
    except PyMongoError as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB profile-save error: {type(exc).__name__}: {detail}")
        return {"saved": False, "message": f"Database save failed: {type(exc).__name__}. Check app logs."}
    except Exception as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB unexpected profile-save error: {type(exc).__name__}: {detail}")
        return {"saved": False, "message": f"Database save failed: {type(exc).__name__}. Check app logs."}


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
            print("MongoDB profile load: no profile found for this profile ID.")
            return None

        document.pop("_id", None)
        document.pop("profile_id", None)
        document.pop("updated_at", None)
        print("MongoDB profile load: profile found.")
        return document
    except PyMongoError as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB profile-load error: {type(exc).__name__}: {detail}")
        return None
    except Exception as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB unexpected profile-load error: {type(exc).__name__}: {detail}")
        return None


def save_chat(user_message: str, assistant_message: str) -> None:
    """Save a chat exchange if MongoDB is available."""
    col = collection("chat_history")
    if col is None:
        return

    try:
        col.insert_one(
            {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except PyMongoError as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB chat-save error: {type(exc).__name__}: {detail}")
    except Exception as exc:
        detail = _safe_error_message(exc, _client_uri or "")
        print(f"MongoDB unexpected chat-save error: {type(exc).__name__}: {detail}")
