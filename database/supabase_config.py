"""
Supabase configuration and client management
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# Load environment variables
load_dotenv()

def get_supabase_url() -> Optional[str]:
    """Get Supabase URL from environment variables"""
    return os.getenv("SUPABASE_URL")

def get_supabase_key() -> Optional[str]:
    """Get Supabase anon key from environment variables"""
    return os.getenv("SUPABASE_KEY")

def get_supabase_service_key() -> Optional[str]:
    """Get Supabase service key from environment variables"""
    return os.getenv("SUPABASE_SERVICE_KEY")

def get_supabase_client() -> Client:
    """Create and return a Supabase client"""
    supabase_url = get_supabase_url()
    supabase_key = get_supabase_key()
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_KEY "
            "environment variables."
        )
    
    return create_client(supabase_url, supabase_key)

def get_supabase_service_client() -> Client:
    """Create and return a Supabase client with service key (for admin operations)"""
    supabase_url = get_supabase_url()
    supabase_service_key = get_supabase_service_key()
    
    if not supabase_url or not supabase_service_key:
        raise ValueError(
            "Missing Supabase service configuration. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_KEY environment variables."
        )
    
    return create_client(supabase_url, supabase_service_key)

def test_supabase_connection() -> bool:
    """Test if Supabase connection is working"""
    try:
        client = get_supabase_client()
        # Try to access a simple endpoint to test connection
        response = client.auth.get_user()
        return True
    except Exception as e:
        print(f"Supabase connection test failed: {e}")
        return False

def get_supabase_config_info() -> dict:
    """Get Supabase configuration information (without sensitive data)"""
    return {
        "url_configured": bool(get_supabase_url()),
        "key_configured": bool(get_supabase_key()),
        "service_key_configured": bool(get_supabase_service_key()),
        "connection_test": test_supabase_connection()
    }
