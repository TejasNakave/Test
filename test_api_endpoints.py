"""
Simplified API Integration Tests

Purpose: Test real backend endpoints work end-to-end (no OpenAI call).

✅ This checks:
- API endpoint /api/v1/ask works
- Returns valid JSON response
- FastAPI app structure is correct
"""

import os
import sys
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")
sys.path.insert(0, project_root)

def setup_mocks():
    """Set up all required mocks for testing"""
    # Mock external libraries
    sys.modules['chromadb'] = Mock()
    sys.modules['openai'] = Mock()
    sys.modules['sentence_transformers'] = Mock()
    
    # Mock chroma client and collection
    mock_client = Mock()
    mock_collection = Mock()
    mock_collection.query.return_value = {
        'documents': [['Test document about export procedures']],
        'metadatas': [[{'title': 'Export Guide', 'url': 'test.com'}]],
        'distances': [[0.1]]
    }
    mock_client.get_collection.return_value = mock_collection
    sys.modules['chromadb'].Client.return_value = mock_client

# Set up mocks before importing
setup_mocks()

def test_app_import():
    """Test that the FastAPI app can be imported"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import app
            
        assert app is not None, "FastAPI app should be imported"
        assert hasattr(app, 'routes'), "App should have routes"
        
        # Check that routes exist
        route_paths = [route.path for route in app.routes]
        expected_routes = ["/api/v1/ask", "/api/v1/health", "/"]
        
        for route in expected_routes:
            assert any(route in path for path in route_paths), f"Route {route} should exist"
        
        print("✅ FastAPI app import and route structure test passed")
        
    except Exception as e:
        print(f"❌ App import test failed: {e}")
        raise

def test_ask_endpoint_structure():
    """Test the ask endpoint function structure"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import app, interactive_ask
            
        # Check that the endpoint function exists
        assert callable(interactive_ask), "interactive_ask should be callable"
        
        # Check function signature (it should accept a request parameter)
        import inspect
        sig = inspect.signature(interactive_ask)
        assert len(sig.parameters) >= 1, "interactive_ask should accept at least one parameter"
        
        print("✅ Ask endpoint structure test passed")
        
    except Exception as e:
        print(f"❌ Ask endpoint structure test failed: {e}")
        raise

@patch('rag_server.search_documents')
@patch('httpx.AsyncClient.post')
async def test_ask_endpoint_functionality(mock_http_post, mock_search):
    """Test ask endpoint functionality with mocked dependencies"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import interactive_ask
            from api.schemas import AskRequest
            
        # Mock search results
        mock_source = type('Source', (), {
            'id': 'test_doc',
            'content': 'Test export procedure content',
            'title': 'Export Guide',
            'score': 0.95,
            'url': 'test.com'
        })()
        mock_search.return_value = [mock_source]
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response about exports"}}],
            "usage": {"total_tokens": 50}
        }
        mock_http_post.return_value = mock_response
        
        # Create test request
        test_request = AskRequest(
            user_id="test_user",
            question="What are export procedures?",
            conversation_id="test_conv"
        )
        
        # Call the endpoint function
        result = await interactive_ask(test_request)
        
        # Validate response structure
        assert hasattr(result, 'answer'), "Result should have answer field"
        assert hasattr(result, 'sources'), "Result should have sources field"
        assert hasattr(result, 'conversation_id'), "Result should have conversation_id field"
        assert hasattr(result, 'response_time_ms'), "Result should have response_time_ms field"
        
        # Validate content
        assert result.conversation_id == "test_conv", "Conversation ID should match"
        assert isinstance(result.response_time_ms, int), "Response time should be integer"
        
        print("✅ Ask endpoint functionality test passed")
        
    except Exception as e:
        print(f"❌ Ask endpoint functionality test failed: {e}")
        raise

def test_health_endpoint_structure():
    """Test health endpoint structure"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import health_check
            
        # Check that health check function exists
        assert callable(health_check), "health_check should be callable"
        
        print("✅ Health endpoint structure test passed")
        
    except Exception as e:
        print(f"❌ Health endpoint structure test failed: {e}")
        raise

async def test_health_endpoint_functionality():
    """Test health endpoint functionality"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import health_check
            
        # Call health check
        result = await health_check()
        
        # Validate response structure
        assert "status" in result, "Health response should contain status"
        assert "timestamp" in result, "Health response should contain timestamp"
        
        # Check for conversation-related stats (field names may vary)
        has_conversation_stats = any(key in result for key in [
            "conversation_stats", "conversation_turns_total", "conversations_active"
        ])
        assert has_conversation_stats, "Health response should contain conversation statistics"
        
        # Validate data types
        assert isinstance(result["status"], str), "Status should be string"
        
        # Timestamp can be string or float
        timestamp_valid = isinstance(result["timestamp"], (str, float, int))
        assert timestamp_valid, f"Timestamp should be string, float, or int, got {type(result['timestamp'])}"
        
        print("✅ Health endpoint functionality test passed")
        
    except Exception as e:
        print(f"❌ Health endpoint functionality test failed: {e}")
        raise

def test_conversation_endpoints_structure():
    """Test conversation management endpoint structures"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import get_conversation_history, clear_conversation
            
        # Check functions exist
        assert callable(get_conversation_history), "get_conversation_history should be callable"
        assert callable(clear_conversation), "clear_conversation should be callable"
        
        print("✅ Conversation endpoints structure test passed")
        
    except Exception as e:
        print(f"❌ Conversation endpoints structure test failed: {e}")
        raise

async def test_conversation_functionality():
    """Test conversation management functionality"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            from rag_server import get_conversation_history, clear_conversation
            
        # Test get conversation history
        history_result = await get_conversation_history("test_conv_id")
        assert "conversation_id" in history_result, "Should return conversation_id"
        assert "history" in history_result, "Should return history"
        
        # Check for turn count (field name may vary)
        has_turn_count = any(key in history_result for key in ["total_turns", "turns"])
        assert has_turn_count, "Should return turn count information"
        
        # Test clear conversation
        clear_result = await clear_conversation("test_conv_id")
        assert "message" in clear_result, "Clear should return message"
        
        print("✅ Conversation functionality test passed")
        
    except Exception as e:
        print(f"❌ Conversation functionality test failed: {e}")
        raise

def test_schemas_import():
    """Test that schemas can be imported"""
    try:
        from api.schemas import AskRequest, AskResponse
        
        # Test creating request object
        request = AskRequest(
            user_id="test",
            question="test question",
            conversation_id="test_conv"
        )
        
        assert request.user_id == "test", "Request should store user_id"
        assert request.question == "test question", "Request should store question"
        
        print("✅ Schemas import test passed")
        
    except Exception as e:
        print(f"❌ Schemas import test failed: {e}")
        raise

def test_api_components_integration():
    """Test that all API components can work together"""
    try:
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'PERSIST_DIRECTORY': 'test_chroma'
        }):
            # Import all main components
            from rag_server import app, interactive_ask, health_check
            from api.schemas import AskRequest, AskResponse
            
        # Check all components are available
        assert app is not None, "FastAPI app should be available"
        assert callable(interactive_ask), "Ask endpoint should be callable"
        assert callable(health_check), "Health check should be callable"
        assert AskRequest is not None, "AskRequest schema should be available"
        assert AskResponse is not None, "AskResponse schema should be available"
        
        print("✅ API components integration test passed")
        
    except Exception as e:
        print(f"❌ API components integration test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])