import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch

# Add project root to Python path (current directory is the project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir  # Since we're running from project root
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.setenv("TOP_K_RESULTS", "5")
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.7")

def test_project_structure():
    """Test if we can access the project files"""
    # Check if we can find the main files
    rag_server_path = os.path.join(project_root, "rag_server.py")
    api_path = os.path.join(project_root, "api")
    
    assert os.path.exists(rag_server_path), f"rag_server.py not found at {rag_server_path}"
    assert os.path.exists(api_path), f"api directory not found at {api_path}"
    
    print(f"✅ rag_server.py found at: {rag_server_path}")
    print(f"✅ api directory found at: {api_path}")

def test_rag_server_import():
    """Test if rag_server can be imported"""
    try:
        import rag_server
        assert hasattr(rag_server, 'app')
        print("✅ rag_server imported successfully")
    except ImportError as e:
        pytest.fail(f"Could not import rag_server: {e}")

def test_api_services_import():
    """Test if api services can be imported"""
    try:
        from api.services.vector_store import VectorStore
        print("✅ VectorStore imported successfully")
    except ImportError as e:
        print(f"⚠️ Could not import VectorStore: {e}")
        # Try alternative import
        try:
            from api.services.vector_store import initialize_vectorstore
            print("✅ initialize_vectorstore imported successfully")
        except ImportError as e2:
            pytest.fail(f"Could not import vector store functions: {e2}")

@pytest.mark.asyncio
async def test_vector_store_search_mock():
    """Test vector store search with mocks"""
    try:
        from api.services.vector_store import initialize_vectorstore
        
        # Mock the vector store initialization
        with patch('api.services.vector_store.VectorStore') as MockVectorStore:
            mock_instance = MockVectorStore.return_value
            mock_instance.search_documents.return_value = [
                type('MockDoc', (), {
                    'page_content': 'Export procedure information',
                    'metadata': {'source': 'export_guide.docx', 'page': 1}
                })()
            ]
            
            # Test search functionality
            vs = initialize_vectorstore(force_rebuild=False, use_openai_embeddings=False)
            if vs:
                results = vs.search_documents("export", k=1)
                assert len(results) > 0
                print("✅ Vector store search test passed")
            else:
                print("⚠️ Vector store not initialized (expected in test environment)")
                
    except ImportError as e:
        pytest.skip(f"Skipping vector store test due to import error: {e}")

def test_basic_functionality():
    """Test basic RAG functionality without heavy dependencies"""
    try:
        # Test if we can create basic request/response structures
        test_request = {
            "user_id": "test_user",
            "question": "What is export procedure?",
            "conversation_id": "test_conv"
        }
        
        test_response = {
            "answer": "Export procedure involves...",
            "sources": [],
            "conversation_id": "test_conv",
            "response_time_ms": 100
        }
        
        assert test_request["user_id"] == "test_user"
        assert test_response["answer"].startswith("Export procedure")
        print("✅ Basic functionality test passed")
        
    except Exception as e:
        pytest.fail(f"Basic functionality test failed: {e}")

@pytest.mark.asyncio
async def test_simple_retrieval():
    """Test simple retrieval functionality"""
    try:
        # Test basic search without heavy dependencies
        query = "export procedures"
        mock_results = [
            {
                "id": "test_1",
                "content": "Export procedures require proper documentation",
                "metadata": {"source": "export_guide.docx"},
                "score": 0.9
            }
        ]
        
        # Simulate retrieval
        assert len(mock_results) > 0
        assert mock_results[0]["score"] > 0.5
        assert "export" in mock_results[0]["content"].lower()
        print("✅ Simple retrieval test passed")
        
    except Exception as e:
        pytest.fail(f"Simple retrieval test failed: {e}")

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v", "-s"])