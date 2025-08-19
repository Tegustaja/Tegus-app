from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time
import uuid
import json
import datetime
import logging
from typing import Dict, List, Optional, Union

# Import only the essential routes that don't have problematic imports
from .auth import router as auth_router
from .subjects import router as subjects_router
from .topics import router as topics_router

# Create main router
router = APIRouter()

# Include only the essential routes
router.include_router(auth_router, tags=["Authentication"])
router.include_router(subjects_router, tags=["Subjects"])
router.include_router(topics_router, tags=["Topics"])

# Simple route for testing
@router.get("/")
async def index():
    return {"message": "Hello from FastAPI"}

# Health check endpoint
@router.get("/health")
async def health_check():
    return {"status": "healthy"} 