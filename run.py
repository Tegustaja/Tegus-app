import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes.routes import router
from api.config import LOGGING_CONFIG, CORS_CONFIG

# Configure logging
logging.basicConfig(
    filename=LOGGING_CONFIG['filename'], 
    level=getattr(logging, LOGGING_CONFIG['level'])
)

# Create FastAPI app
app = FastAPI(
    title="Tegus API",
    description="Backend API for Tegus learning platform",
    version="1.0.0"
)

# Configure CORS with more explicit settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_CONFIG['allow_origins'],
    allow_credentials=CORS_CONFIG['allow_credentials'],
    allow_methods=CORS_CONFIG['allow_methods'],
    allow_headers=CORS_CONFIG['allow_headers'],
    expose_headers=CORS_CONFIG['expose_headers'],
    max_age=CORS_CONFIG['max_age']
)

# Include the API routes
app.include_router(router, prefix="/api")

# Root redirect to API
@app.get("/")
async def root():
    return {"message": "Tegus API", "docs": "/docs", "api": "/api"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "cors_configured": True}

if __name__ == "__main__":
    import uvicorn
    print("Starting Tegus API server...")
    print(f"CORS origins: {CORS_CONFIG['allow_origins']}")
    print(f"CORS methods: {CORS_CONFIG['allow_methods']}")
    print(f"CORS headers: {CORS_CONFIG['allow_headers']}")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

