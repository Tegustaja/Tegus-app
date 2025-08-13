"""
Database configuration and connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    # For Supabase, we'll use the connection string format
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Build from Supabase components
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        # Extract host from Supabase URL and build PostgreSQL connection
        host = supabase_url.replace("https://", "").replace("http://", "").replace("http://", "").replace(".supabase.co", "")
        
        # For Supabase, the database is typically 'postgres'
        user = "postgres"  # or your specific user
        password = supabase_key  # or your specific password
        database = "postgres"  # or your specific database name
        
        return f"postgresql://{user}:{password}@{host}.supabase.co:5432/{database}"
    
    # Fallback to local development
    return "postgresql://postgres:password@localhost:5432/tegus_dev"

# Lazy engine creation to avoid import errors
_engine = None
_SessionLocal = None

def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        SQLALCHEMY_DATABASE_URL = get_database_url()
        _engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine

def get_session_local():
    """Get or create SessionLocal class"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# Dependency to get database session
def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
