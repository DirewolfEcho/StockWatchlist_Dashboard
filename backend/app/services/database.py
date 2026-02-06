"""
Database service for persistent storage using Supabase.
Falls back to local JSON file if Supabase is not configured.
"""
import os
import json
from typing import Optional
from datetime import datetime

# Check if Supabase is configured
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase not configured. Using local file storage.")
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected successfully")
        return _supabase_client
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None

def save_app_state_to_db(state_json: str) -> bool:
    """
    Save entire app state to Supabase.
    Uses a single row in 'app_state' table to store the JSON.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Upsert the state (insert or update)
        result = client.table("app_state").upsert({
            "id": 1,  # Single row for app state
            "data": state_json,
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        return True
    except Exception as e:
        print(f"❌ Failed to save to Supabase: {e}")
        return False

def load_app_state_from_db() -> Optional[str]:
    """
    Load app state from Supabase.
    Returns JSON string or None if not found.
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table("app_state").select("data").eq("id", 1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["data"]
        return None
    except Exception as e:
        print(f"❌ Failed to load from Supabase: {e}")
        return None

def is_supabase_configured() -> bool:
    """Check if Supabase environment variables are set."""
    return bool(SUPABASE_URL and SUPABASE_KEY)
