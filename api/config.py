"""
Configuration settings for the RAG chatbot API
"""
import os
from typing import Optional

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Vector Store Configuration
PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", "chroma_db")
USE_OPENAI_EMBEDDINGS = os.getenv("USE_OPENAI_EMBEDDINGS", "true").lower() == "true"

# Document Processing Configuration
DOCUMENT_DIRECTORY = os.getenv("DOCUMENT_DIRECTORY", "documents")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# API Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Search Configuration
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# LLM Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Retrieval Configuration
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "10"))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/chatbot.log")

def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment variables"""
    return OPENAI_API_KEY if OPENAI_API_KEY else None

def validate_config() -> bool:
    """Validate essential configuration"""
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not set in environment variables")
        return False
    return True