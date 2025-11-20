# AI Coding Agent Instructions for Trade Assistant RAG Chatbot

## 🏗️ Architecture Overview

This is a **dual-architecture RAG-powered trade assistant** with two parallel implementations:

1. **Legacy Server**: `rag_server.py` - Single-file FastAPI server (working, feature-complete)
2. **Modern API**: `api/` directory - Modular microservices architecture (newer, structured)

Both serve the same React frontend (`src/`) but use different endpoints and patterns.

## 🔑 Critical Development Patterns

### Multi-Modal RAG Pipeline
- **Document Sources**: 53+ DGFT trade documents in various formats (DOCX with embedded images)
- **Vector Storage**: ChromaDB with OpenAI embeddings (`chroma_db/` directories)
- **Service Chain**: `retriever.py` → `reranker.py` → `prompt_builder.py` → `llm_service.py`
- **Image Processing**: `image_analyzer.py` extracts and analyzes embedded images using vision models

### Response Enhancement System
- **Gesture Functions**: `get_opening_gestures()` and `get_closing_gestures()` in `rag_server.py`
- **Response Wrapping**: Every API response uses `add_response_gestures()` for consistent UX
- **Proactive Features**: `proactive_service.py` analyzes user behavior patterns for ChatGPT-like suggestions

### Authentication & User Management
- **JWT-based**: See `api/auth.py` for token handling patterns
- **Optional Authentication**: Use `get_optional_user()` dependency for graceful degradation
- **Subscription Tiers**: Framework exists but currently commented out

## 🛠️ Development Workflows

### Running the Application
```bash
# Legacy server (recommended for development)
python rag_server.py

# Modern API + Frontend
python -m uvicorn api.app:app --reload

# React frontend only
cd src && npm start
```

### Testing Strategy
- **Component Tests**: Individual service tests in `test_*.py` files
- **Integration Tests**: `test_integration.sh` and `test_api_endpoints.py`
- **Manual Testing**: Use `/docs` endpoints for API testing

### Key Configuration Files
- `settings.yaml.example` - Main configuration template
- `api/config.py` - Centralized settings management
- `.env.example` - Environment variables (especially `OPENAI_API_KEY`)

## 📋 Code Conventions

### Error Handling Pattern
```python
try:
    result = await service_operation()
    enhanced_result = add_response_gestures(result, question, suggestions)
    return enhanced_result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    fallback = "I apologize, but I encountered an issue..."
    return add_response_gestures(fallback, question)
```

### Service Dependency Injection
- Use `Depends()` pattern for service injection in FastAPI routes
- Services initialized in `api/app.py` or individual modules
- Example: `rag: RAGIntegration = Depends(get_rag_integration)`

### Logging & Analytics
- **Database Logging**: `api/services/logger.py` tracks all interactions
- **Performance Metrics**: Response times, token usage, user patterns
- **SQLite Storage**: Analytics stored in `chatbot.db` (see logger service)

## 🔍 Critical Integration Points

### Vector Database Operations
- **ChromaDB Management**: Collections created/managed in `vector_store.py`
- **Embedding Strategy**: OpenAI text-embedding-ada-002 for consistency
- **Search Optimization**: Combines semantic search with keyword filtering

### Frontend-Backend Communication
- **API Client**: `src/api/apiClient.js` handles all backend communication
- **Real-time Updates**: WebSocket-ready architecture in place
- **Error Boundaries**: Graceful fallback for authentication failures

### Document Processing Pipeline
- **Image Extraction**: Automated during document ingestion
- **Metadata Preservation**: Original document structure maintained
- **Multi-format Support**: DOCX, PDF, image files all supported

## 🚨 Important Gotchas

### File Structure Confusion
- Both `rag_server.py` and `api/app.py` can serve the frontend
- Choose ONE approach per deployment to avoid port conflicts
- React build output goes to `build/` but is served from Python backend

### Environment Setup
- **OpenAI API Key**: Required for both embeddings and completions
- **ChromaDB Path**: Must be consistent between runs for persistence
- **CORS Settings**: Already configured for iframe integration

### Performance Considerations
- Vector searches can be expensive - use `top_k` parameters wisely
- LLM token limits apply - prompt building truncates intelligently
- Image analysis is slower than text - cache when possible

## 🔄 When Making Changes

1. **Gesture Updates**: Modify functions in `rag_server.py`, test with `/ask` endpoint
2. **New Services**: Add to `api/services/`, register in `api/app.py`
3. **Frontend Changes**: Build with `npm run build`, restart Python server
4. **Database Schema**: Update `logger.py` and run migration logic
5. **New Trade Documents**: Use document loader services, rebuild vector index

## 📝 Testing Your Changes
- Use `test_api_endpoints.py` for comprehensive API testing
- Frontend changes: Test in both authenticated/unauthenticated modes
- Vector operations: Verify with `test_retriever.py`
- End-to-end: Use browser dev tools with `/docs` interface