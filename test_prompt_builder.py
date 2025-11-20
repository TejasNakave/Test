"""
Test suite for prompt_builder.py

Purpose: Confirm the prompt includes both user query and retrieved context.

✅ This confirms:
- Query text is present
- Context is embedded
- Prompt isn't empty or malformed
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

# Mock PromptResult, Diagram, and Suggestion classes
class PromptResult:
    def __init__(self, answer: str, diagrams: List = None, suggestions: List = None, tokens_used: int = 0):
        self.answer = answer
        self.diagrams = diagrams or []
        self.suggestions = suggestions or []
        self.tokens_used = tokens_used

class Diagram:
    def __init__(self, id: str, title: str, description: str, diagram_type: str, metadata: Dict = None):
        self.id = id
        self.title = title
        self.description = description
        self.diagram_type = diagram_type
        self.metadata = metadata or {}

class Suggestion:
    def __init__(self, question: str, relevance: float, action_type: str = "ask"):
        self.question = question
        self.relevance = relevance
        self.action_type = action_type

# Mock settings object that prompt_builder expects
class MockSettings:
    LLM_API_KEY = "test-api-key"
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_MODEL = "gpt-3.5-turbo"

# Patch the imports in the prompt_builder module
sys.modules['api.schemas'] = Mock()
sys.modules['api.schemas'].Diagram = Diagram
sys.modules['api.schemas'].Suggestion = Suggestion
sys.modules['api.config'] = Mock()
sys.modules['api.config'].settings = MockSettings()

# Import prompt_builder service after mocking
from api.services.prompt_builder import PromptBuilderService

def test_prompt_builder_import():
    """Test that PromptBuilderService can be imported successfully"""
    try:
        service = PromptBuilderService()
        print("✅ PromptBuilderService imported successfully")
        assert service is not None
        assert hasattr(service, '_build_main_prompt')
    except Exception as e:
        print(f"❌ Failed to import PromptBuilderService: {e}")
        raise

def test_build_main_prompt_contains_query():
    """Test that the built prompt contains the user query"""
    service = PromptBuilderService()
    
    test_question = "What is machine learning?"
    test_chunks = [
        {
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            "title": "ML Introduction",
            "url": "https://example.com/ml-intro"
        }
    ]
    
    try:
        prompt = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=True,
            include_suggestions=True
        )
        
        # Check that prompt is not empty
        assert prompt is not None and len(prompt.strip()) > 0, "Prompt should not be empty"
        
        # Check that user query is present in the prompt
        assert test_question in prompt, f"User query '{test_question}' not found in prompt"
        
        print("✅ Prompt contains user query test passed")
        
    except Exception as e:
        print(f"❌ Prompt query test failed: {e}")
        raise

def test_build_main_prompt_contains_context():
    """Test that the built prompt contains retrieved context"""
    service = PromptBuilderService()
    
    test_question = "How does neural network training work?"
    test_chunks = [
        {
            "content": "Neural network training involves adjusting weights through backpropagation algorithm.",
            "title": "Neural Network Training",
            "url": "https://example.com/nn-training"
        },
        {
            "content": "Gradient descent is used to minimize the loss function during training.",
            "title": "Gradient Descent",
            "url": "https://example.com/gradient-descent"
        }
    ]
    
    try:
        prompt = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=False,
            include_suggestions=False
        )
        
        # Check that context from chunks is embedded
        for i, chunk in enumerate(test_chunks):
            content = chunk["content"]
            title = chunk["title"]
            
            assert content in prompt, f"Chunk content '{content}' not found in prompt"
            assert title in prompt, f"Chunk title '{title}' not found in prompt"
            assert f"Source {i+1}" in prompt, f"Source reference 'Source {i+1}' not found in prompt"
        
        # Check that CONTEXT SOURCES section exists
        assert "CONTEXT SOURCES:" in prompt, "CONTEXT SOURCES section not found in prompt"
        
        print("✅ Prompt contains context test passed")
        
    except Exception as e:
        print(f"❌ Prompt context test failed: {e}")
        raise

def test_prompt_structure_and_formatting():
    """Test that the prompt has proper structure and isn't malformed"""
    service = PromptBuilderService()
    
    test_question = "Explain deep learning concepts"
    test_chunks = [
        {
            "content": "Deep learning uses multiple layers of neural networks to model complex patterns in data.",
            "title": "Deep Learning Basics",
            "url": "https://example.com/deep-learning"
        }
    ]
    
    try:
        prompt = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=True,
            include_suggestions=True
        )
        
        # Check for key structural elements
        assert "USER QUESTION:" in prompt, "USER QUESTION section not found"
        assert "INSTRUCTIONS:" in prompt, "INSTRUCTIONS section not found"
        assert "CONTEXT SOURCES:" in prompt, "CONTEXT SOURCES section not found"
        
        # Check that prompt contains instructions for citations
        assert "Source" in prompt, "Source citation instructions not found"
        
        # Check for diagram instructions when enabled
        assert "mermaid" in prompt.lower(), "Mermaid diagram instructions not found"
        
        # Check for suggestions instructions when enabled
        assert "follow-up" in prompt.lower(), "Follow-up suggestions instructions not found"
        
        # Ensure prompt is well-formed (not just fragments)
        lines = prompt.split('\n')
        assert len(lines) > 5, "Prompt should have multiple lines of content"
        
        print("✅ Prompt structure and formatting test passed")
        
    except Exception as e:
        print(f"❌ Prompt structure test failed: {e}")
        raise

def test_prompt_with_empty_chunks():
    """Test prompt building with empty chunks list"""
    service = PromptBuilderService()
    
    test_question = "What is artificial intelligence?"
    test_chunks = []
    
    try:
        prompt = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=False,
            include_suggestions=False
        )
        
        # Should still contain the question even with no context
        assert test_question in prompt, "Question should be present even with empty chunks"
        assert "USER QUESTION:" in prompt, "USER QUESTION section should be present"
        
        # Context section should still exist but be empty
        assert "CONTEXT SOURCES:" in prompt, "CONTEXT SOURCES section should exist"
        
        print("✅ Empty chunks test passed")
        
    except Exception as e:
        print(f"❌ Empty chunks test failed: {e}")
        raise

def test_prompt_with_multiple_chunks():
    """Test prompt building with multiple context chunks"""
    service = PromptBuilderService()
    
    test_question = "How do transformers work in NLP?"
    test_chunks = [
        {
            "content": "Transformers use self-attention mechanisms to process sequential data.",
            "title": "Transformer Architecture",
            "url": "https://example.com/transformers"
        },
        {
            "content": "BERT is a transformer model that uses bidirectional encoding.",
            "title": "BERT Model",
            "url": "https://example.com/bert"
        },
        {
            "content": "GPT models are transformer-based language models that generate text.",
            "title": "GPT Models",
            "url": "https://example.com/gpt"
        },
        {
            "content": "Attention mechanisms allow models to focus on relevant parts of input.",
            "title": "Attention Mechanisms",
            "url": "https://example.com/attention"
        },
        {
            "content": "Positional encoding helps transformers understand sequence order.",
            "title": "Positional Encoding",
            "url": "https://example.com/positional"
        },
        {
            "content": "This chunk should be excluded as only top 5 are used.",
            "title": "Extra Chunk",
            "url": "https://example.com/extra"
        }
    ]
    
    try:
        prompt = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=True,
            include_suggestions=True
        )
        
        # Should contain first 5 chunks but not the 6th
        for i in range(5):
            chunk = test_chunks[i]
            assert chunk["content"] in prompt, f"Chunk {i+1} content should be included"
            assert chunk["title"] in prompt, f"Chunk {i+1} title should be included"
            assert f"Source {i+1}" in prompt, f"Source {i+1} reference should be present"
        
        # 6th chunk should not be included (only top 5 used)
        assert test_chunks[5]["content"] not in prompt, "6th chunk should be excluded"
        
        print("✅ Multiple chunks test passed")
        
    except Exception as e:
        print(f"❌ Multiple chunks test failed: {e}")
        raise

def test_prompt_diagram_instructions():
    """Test that diagram instructions are included when requested"""
    service = PromptBuilderService()
    
    test_question = "Explain neural network architecture"
    test_chunks = [{"content": "Test content", "title": "Test", "url": ""}]
    
    try:
        # Test with diagrams enabled
        prompt_with_diagrams = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=True,
            include_suggestions=False
        )
        
        assert "mermaid" in prompt_with_diagrams.lower(), "Mermaid instructions should be present when diagrams enabled"
        assert "visual representation" in prompt_with_diagrams.lower(), "Visual representation instruction should be present"
        
        # Test with diagrams disabled
        prompt_without_diagrams = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=False,
            include_suggestions=False
        )
        
        assert "mermaid" not in prompt_without_diagrams.lower(), "Mermaid instructions should not be present when diagrams disabled"
        
        print("✅ Diagram instructions test passed")
        
    except Exception as e:
        print(f"❌ Diagram instructions test failed: {e}")
        raise

def test_prompt_suggestions_instructions():
    """Test that suggestion instructions are included when requested"""
    service = PromptBuilderService()
    
    test_question = "What is machine learning?"
    test_chunks = [{"content": "Test content", "title": "Test", "url": ""}]
    
    try:
        # Test with suggestions enabled
        prompt_with_suggestions = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=False,
            include_suggestions=True
        )
        
        assert "follow-up" in prompt_with_suggestions.lower(), "Follow-up instructions should be present when suggestions enabled"
        
        # Test with suggestions disabled
        prompt_without_suggestions = service._build_main_prompt(
            question=test_question,
            chunks=test_chunks,
            include_diagrams=False,
            include_suggestions=False
        )
        
        assert "follow-up" not in prompt_without_suggestions.lower(), "Follow-up instructions should not be present when suggestions disabled"
        
        print("✅ Suggestions instructions test passed")
        
    except Exception as e:
        print(f"❌ Suggestions instructions test failed: {e}")
        raise

@pytest.mark.asyncio
async def test_generate_simple_response():
    """Test simple response generation without context"""
    service = PromptBuilderService()
    
    # Test without API key
    service.llm_api_key = None
    
    try:
        result = await service.generate_simple_response("Hello", "test-conv-id")
        
        assert "answer" in result, "Result should contain answer field"
        assert "tokens_used" in result, "Result should contain tokens_used field"
        assert "Hello" in result["answer"], "Answer should reference the original question"
        
        print("✅ Simple response generation test passed")
        
    except Exception as e:
        print(f"❌ Simple response generation test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])