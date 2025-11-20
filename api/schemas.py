"""
Pydantic Schemas and Data Models
Defines request/response models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for better type safety
class MessageType(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"

class ActionType(str, Enum):
    ASK = "ask"
    EXPLORE = "explore"
    GUIDE = "guide"

# Base models
class Source(BaseModel):
    id: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}

class Suggestion(BaseModel):
    question: str
    relevance: float
    action_type: str = "ask"

class InteractiveAction(BaseModel):
    type: str
    content: str
    metadata: Dict[str, Any] = {}

class Diagram(BaseModel):
    id: str
    title: str
    description: str
    diagram_type: str
    metadata: Dict[str, Any] = {}

class ImageData(BaseModel):
    image_filename: str
    base64_data: str
    analysis: str = ""
    relevance_score: float = 0.0
    source_document: str = ""
    metadata: Dict[str, Any] = {}

class ConversationTurn(BaseModel):
    timestamp: datetime
    user_question: str
    bot_response: str
    sources_used: List[str] = []
    user_intent: str = "general"
    topic: str = "general"

# Request models
class AskRequest(BaseModel):
    question: str = Field(..., description="User's question")
    user_id: str = Field(..., description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    include_diagrams: bool = Field(False, description="Whether to include diagrams")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

# Response models
class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    diagrams: List[Diagram] = []
    suggestions: List[Suggestion] = []
    conversation_id: str
    response_time_ms: int
    tokens_used: int = 0
    user_intent: Optional[str] = None
    confidence_score: float = 0.0
    interactive_elements: List[InteractiveAction] = []
    conversation_context: Dict[str, Any] = {}
    images: List[ImageData] = []

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    dependencies: Dict[str, str] = {}

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Authentication models
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

# LLM Service Schemas
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None

class LLMResponse(BaseModel):
    response: str = Field(..., description="Generated response text")
    tokens_used: int = Field(default=0, description="Number of tokens used")
    processing_time_ms: int = Field(default=0, description="Processing time in milliseconds")
    model_used: str = Field(..., description="Model used for generation")