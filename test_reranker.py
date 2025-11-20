"""
Test suite for reranker.py

Purpose: Validate that the reranker orders items by score correctly.

✅ This ensures:
- Results are sorted descending by score
- All entries contain "text" or content
- Reranking functionality works properly
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")
sys.path.insert(0, project_root)

# Mock RerankResult schema (since it's missing from schemas.py)
class RerankResult:
    def __init__(self, reranked_chunks: List[Dict[str, Any]], rerank_time_ms: int, scores: List[float]):
        self.reranked_chunks = reranked_chunks
        self.rerank_time_ms = rerank_time_ms
        self.scores = scores

# Mock settings object that reranker expects
class MockSettings:
    LLM_API_KEY = None
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_MODEL = "gpt-3.5-turbo"
    TOP_K_RERANK = 5

# Patch the imports in the reranker module
sys.modules['api.schemas'] = Mock()
sys.modules['api.schemas'].RerankResult = RerankResult
sys.modules['api.config'] = Mock()
sys.modules['api.config'].settings = MockSettings()

# Import reranker service after mocking
from api.services.reranker import RerankerService

def test_reranker_import():
    """Test that RerankerService can be imported successfully"""
    try:
        service = RerankerService()
        print("✅ RerankerService imported successfully")
        assert service is not None
    except Exception as e:
        print(f"❌ Failed to import RerankerService: {e}")
        raise

@pytest.mark.asyncio
async def test_rerank_by_score_descending_order():
    """Test that rerank_by_score sorts results in descending order by score"""
    service = RerankerService()
    
    # Test data with different scores
    test_chunks = [
        {"content": "Low relevance content", "score": 0.3, "text": "Sample text 1"},
        {"content": "High relevance content", "score": 0.9, "text": "Sample text 2"},
        {"content": "Medium relevance content", "score": 0.6, "text": "Sample text 3"},
        {"content": "Very low relevance content", "score": 0.1, "text": "Sample text 4"},
        {"content": "Very high relevance content", "score": 0.95, "text": "Sample text 5"}
    ]
    
    try:
        result = await service._rerank_by_score(test_chunks, top_k=3)
        
        # Check that results are sorted in descending order
        scores = result.scores
        assert len(scores) == 3, f"Expected 3 results, got {len(scores)}"
        
        # Verify descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not in descending order: {scores[i]} < {scores[i + 1]}"
        
        # Verify highest scores are returned
        expected_scores = [0.95, 0.9, 0.6]
        assert scores == expected_scores, f"Expected {expected_scores}, got {scores}"
        
        # Verify all entries contain content/text
        for chunk in result.reranked_chunks:
            assert "content" in chunk or "text" in chunk, f"Chunk missing content/text: {chunk}"
        
        print("✅ Rerank by score descending order test passed")
        
    except Exception as e:
        print(f"❌ Rerank by score test failed: {e}")
        raise

@pytest.mark.asyncio
async def test_rerank_with_empty_chunks():
    """Test reranking with empty chunk list"""
    service = RerankerService()
    
    try:
        result = await service.rerank("test query", [], top_k=5)
        
        assert len(result.reranked_chunks) == 0
        assert len(result.scores) == 0
        assert result.rerank_time_ms >= 0
        
        print("✅ Empty chunks test passed")
        
    except Exception as e:
        print(f"❌ Empty chunks test failed: {e}")
        raise

@pytest.mark.asyncio
async def test_rerank_fewer_chunks_than_top_k():
    """Test reranking when we have fewer chunks than requested top_k"""
    service = RerankerService()
    
    test_chunks = [
        {"content": "Content 1", "score": 0.8, "text": "Text 1"},
        {"content": "Content 2", "score": 0.6, "text": "Text 2"}
    ]
    
    try:
        result = await service.rerank("test query", test_chunks, top_k=5)
        
        # Should return all chunks when fewer than top_k
        assert len(result.reranked_chunks) == 2
        assert len(result.scores) == 2
        
        # Should still be sorted by score
        assert result.scores[0] >= result.scores[1]
        
        print("✅ Fewer chunks than top_k test passed")
        
    except Exception as e:
        print(f"❌ Fewer chunks test failed: {e}")
        raise

@pytest.mark.asyncio
async def test_all_entries_contain_text_or_content():
    """Test that all reranked entries contain text or content fields"""
    service = RerankerService()
    
    test_chunks = [
        {"content": "Content with text", "score": 0.8, "text": "Sample text"},
        {"content": "Content only", "score": 0.7},
        {"text": "Text only", "score": 0.6},
        {"content": "Another content", "score": 0.5, "text": "Another text"}
    ]
    
    try:
        result = await service._rerank_by_score(test_chunks, top_k=4)
        
        for i, chunk in enumerate(result.reranked_chunks):
            has_content = "content" in chunk
            has_text = "text" in chunk
            
            assert has_content or has_text, f"Chunk {i} missing both content and text: {chunk}"
            
            if has_content:
                assert isinstance(chunk["content"], str), f"Content should be string: {chunk['content']}"
            if has_text:
                assert isinstance(chunk["text"], str), f"Text should be string: {chunk['text']}"
        
        print("✅ All entries contain text/content test passed")
        
    except Exception as e:
        print(f"❌ Text/content validation test failed: {e}")
        raise

@pytest.mark.asyncio
async def test_score_range_validation():
    """Test that scores are in valid range and properly assigned"""
    service = RerankerService()
    
    test_chunks = [
        {"content": "High score content", "score": 0.95, "text": "High text"},
        {"content": "Low score content", "score": 0.05, "text": "Low text"},
        {"content": "Mid score content", "score": 0.5, "text": "Mid text"}
    ]
    
    try:
        result = await service._rerank_by_score(test_chunks, top_k=3)
        
        for score in result.scores:
            assert 0.0 <= score <= 1.0, f"Score out of range [0,1]: {score}"
        
        # Verify scores match the original chunk scores
        assert result.scores == [0.95, 0.5, 0.05], f"Scores don't match expected order: {result.scores}"
        
        print("✅ Score range validation test passed")
        
    except Exception as e:
        print(f"❌ Score range validation test failed: {e}")
        raise

@pytest.mark.asyncio 
async def test_reranker_health_check():
    """Test reranker health check functionality"""
    service = RerankerService()
    
    try:
        # Without API key, should return True (score-based reranking available)
        service.llm_api_key = None
        health = await service.health_check()
        assert health == True, "Health check should return True when no API key (score-based available)"
        
        print("✅ Reranker health check test passed")
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        raise

def test_parsing_llm_rankings():
    """Test parsing of LLM ranking responses"""
    service = RerankerService()
    
    try:
        # Test normal ranking response
        rankings_text = "The most relevant passages are: 2, 0, 4, 1"
        result = service._parse_llm_rankings(rankings_text, max_index=5)
        expected = [2, 0, 4, 1]
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Test with invalid indices (should be filtered out)
        rankings_text = "Relevant: 1, 10, 2, -1, 0"  # 10 and -1 are invalid for max_index=5
        result = service._parse_llm_rankings(rankings_text, max_index=5)
        expected = [1, 2, 0]  # Invalid indices filtered out
        assert result == expected, f"Expected {expected}, got {result}"
        
        print("✅ LLM rankings parsing test passed")
        
    except Exception as e:
        print(f"❌ LLM rankings parsing test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])