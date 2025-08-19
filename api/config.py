import os
from dotenv import load_dotenv, find_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(find_dotenv())

# API Configuration
API_KEY = os.getenv("FLASK_API_KEY", "default-keasdfalsfjadsfkdakfkdsy")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create centralized Supabase client
if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase_client = None
    print("Warning: SUPABASE_URL and SUPABASE_KEY not set. Supabase functionality will be disabled.")

# Logging Configuration
LOGGING_CONFIG = {
    'filename': 'logs/record.log',
    'level': 'DEBUG'
}

# CORS Configuration
CORS_CONFIG = {
    'allow_origins': [
        "http://localhost:3000",      # React development server
        "http://localhost:8081",      # Expo development server
        "http://localhost:19006",     # Expo web
        "http://127.0.0.1:3000",     # React development server (IP)
        "http://127.0.0.1:8081",     # Expo development server (IP)
        "http://127.0.0.1:19006",    # Expo web (IP)
        "exp://localhost:8081",       # Expo development
        "exp://127.0.0.1:8081",      # Expo development (IP)
        "*"                           # Allow all origins in development
    ],
    'allow_credentials': True,
    'allow_methods': ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    'allow_headers': [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    'expose_headers': ["Content-Length", "Content-Range"],
    'max_age': 86400,  # 24 hours
} 