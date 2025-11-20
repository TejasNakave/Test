"""
FastAPI Application Entry Point
Alternative to rag_server.py for modular API structure
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from . import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description="Modular RAG-powered chatbot API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RAG Chatbot API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-10-03T00:00:00Z",
        "version": "1.0.0"
    }

# Import and include routers
try:
    from .routers.ask_router_updated import router as ask_router
    app.include_router(ask_router)
    logger.info("Ask router included successfully")
except ImportError as e:
    logger.warning(f"Could not import ask router: {e}")

try:
    from .routers.health_router import router as health_router
    app.include_router(health_router)
    logger.info("Health router included successfully")
except ImportError as e:
    logger.warning(f"Could not import health router: {e}")

try:
    from .routers.proactive_router import router as proactive_router
    app.include_router(proactive_router)
    logger.info("Proactive router included successfully")
except ImportError as e:
    logger.warning(f"Could not import proactive router: {e}")

try:
    from .routers.usage_router_clean import router as usage_router
    app.include_router(usage_router)
    logger.info("Usage router included successfully")
except ImportError as e:
    logger.warning(f"Could not import usage router: {e}")

try:
    from .routers.data_config_router import router as data_config_router
    app.include_router(data_config_router)
    logger.info("Data configuration router included successfully")
except ImportError as e:
    logger.warning(f"Could not import data configuration router: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )