"""
RAG Integration Module - Connect modular API with existing RAG functionality
"""
import sys
import os
import time
from pathlib import Path

# Add the parent directory to Python path to import from api.services
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

# Import existing RAG services
try:
    from api.services.vector_store import VectorStore
    from api.services.document_loader import DocumentLoader
    from api.services.llm_service import LLMService
except ImportError as e:
    logging.warning(f"Could not import RAG services: {e}")
    # Fallback to None - will use mock functions
    VectorStore = None
    DocumentLoader = None
    LLMService = None

from api.schemas import Source, AskRequest, AskResponse

logger = logging.getLogger(__name__)

class RAGIntegration:
    """
    Integration layer between modular API and existing RAG functionality
    """
    
    def __init__(self):
        self.vector_store = None
        self.document_loader = None
        self.llm_service = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize RAG services"""
        try:
            if VectorStore:
                self.vector_store = VectorStore()
                
            if DocumentLoader:
                self.document_loader = DocumentLoader()
                
            if LLMService:
                self.llm_service = LLMService()
                
            self.is_initialized = True
            logger.info("RAG Integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG services: {e}")
            self.is_initialized = False
            
    async def search_documents(self, query: str, top_k: int = 5) -> List[Source]:
        """
        Search documents using vector store or fallback to mock
        """
        if not self.is_initialized or not self.vector_store:
            return await self._mock_search_documents(query, top_k)
            
        try:
            # Use actual vector store search
            results = await self.vector_store.search(query, top_k)
            
            sources = []
            for i, result in enumerate(results):
                source = Source(
                    id=f"doc_{i}_{hash(result.get('content', ''))[:8]}",
                    title=result.get('metadata', {}).get('source', f"Document {i+1}"),
                    content=result.get('content', ''),
                    score=result.get('score', 0.0),
                    metadata=result.get('metadata', {})
                )
                sources.append(source)
                
            return sources
            
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return await self._mock_search_documents(query, top_k)
            
    async def generate_response(
        self,
        question: str,
        sources: List[Source],
        conversation_history: Optional[List] = None,
        user_intent: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response using OpenAI service or fallback to mock
        """
        if not self.is_initialized or not self.llm_service:
            return self._mock_generate_response(question, sources, conversation_history, user_intent)
            
        try:
            # Prepare context from sources
            context = "\n\n".join([
                f"Source: {source.title}\nContent: {source.content}"
                for source in sources
            ])
            
            # Prepare conversation context if available
            conversation_context = ""
            if conversation_history:
                recent_turns = conversation_history[-3:]  # Last 3 turns
                conversation_context = "\n".join([
                    f"Previous Q: {turn.user_question}\nPrevious A: {turn.bot_response[:100]}..."
                    for turn in recent_turns
                ])
            
            # Prepare intent context
            intent_context = ""
            if user_intent:
                intent_context = f"User Intent: {user_intent.get('primary_intent', 'general')}"
                if user_intent.get('expertise_level'):
                    intent_context += f", Expertise Level: {user_intent['expertise_level']}"
            
            # Generate response using LLM service with enhanced multimodal capabilities
            system_prompt = f"""You are a knowledgeable Trade Assistant specializing in international trade, customs, and related procedures.
            
Context from relevant documents:
{context}

Conversation Context:
{conversation_context}

{intent_context}

Please provide a comprehensive, accurate response based on the context provided. If visual content is referenced, describe it clearly to help the user understand any flowcharts, forms, or procedures mentioned."""

            response = await self.llm_service.generate_response(
                message=question,
                user_id="trade_assistant_user",
                conversation_id=f"rag_{int(time.time())}",
                system_prompt=system_prompt,
                include_images=True  # Enable image analysis for comprehensive responses
            )
            
            return response.response  # Extract the text response from LLMResponse object
            
            return response.response  # Extract the text response from LLMResponse object
            
        except Exception as e:
            logger.error(f"Error in response generation: {e}")
            return self._mock_generate_response(question, sources, conversation_history, user_intent)
            
    async def get_document_count(self) -> int:
        """Get total number of documents in the vector store"""
        if not self.is_initialized or not self.vector_store:
            return 0
            
        try:
            return await self.vector_store.get_document_count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
            
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        if not self.is_initialized or not self.vector_store:
            return {
                "status": "not_initialized",
                "document_count": 0,
                "chunk_count": 0,
                "embedding_dimension": 0
            }
            
        try:
            stats = await self.vector_store.get_stats()
            return {
                "status": "active",
                "document_count": stats.get("document_count", 0),
                "chunk_count": stats.get("chunk_count", 0),
                "embedding_dimension": stats.get("embedding_dimension", 1536),
                "last_updated": stats.get("last_updated", datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "document_count": 0,
                "chunk_count": 0,
                "embedding_dimension": 0
            }
            
    async def load_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Load new documents into the vector store"""
        if not self.is_initialized or not self.document_loader or not self.vector_store:
            return {
                "success": False,
                "error": "RAG services not initialized",
                "processed_files": 0,
                "total_chunks": 0
            }
            
        try:
            # Load documents
            documents = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    docs = await self.document_loader.load_document(file_path)
                    documents.extend(docs)
                    
            if not documents:
                return {
                    "success": False,
                    "error": "No valid documents found",
                    "processed_files": 0,
                    "total_chunks": 0
                }
                
            # Add to vector store
            await self.vector_store.add_documents(documents)
            
            return {
                "success": True,
                "processed_files": len(file_paths),
                "total_chunks": len(documents),
                "message": f"Successfully loaded {len(documents)} chunks from {len(file_paths)} files"
            }
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_files": 0,
                "total_chunks": 0
            }
            
    # Mock functions for fallback
    async def _mock_search_documents(self, query: str, top_k: int = 5) -> List[Source]:
        """Mock document search when vector store is not available"""
        mock_sources = []
        
        # Generate mock sources based on query keywords
        keywords = query.lower().split()
        
        for i in range(min(top_k, 3)):
            mock_content = f"This is mock content related to your query about {', '.join(keywords[:2])}. "
            mock_content += "In a real implementation, this would be actual document content retrieved from the vector database."
            
            source = Source(
                id=f"mock_doc_{i}",
                title=f"Export Document {i+1}",
                content=mock_content,
                score=0.9 - (i * 0.1),
                metadata={
                    "source": f"mock_document_{i+1}.docx",
                    "page": i + 1,
                    "mock": True
                }
            )
            mock_sources.append(source)
            
        return mock_sources
        
    def _mock_generate_response(
        self,
        question: str,
        sources: List[Source],
        conversation_history: Optional[List] = None,
        user_intent: Optional[Dict[str, Any]] = None
    ) -> str:
        """Mock response generation when OpenAI service is not available"""
        
        # Build context awareness
        context_info = ""
        if conversation_history:
            context_info = f" (continuing our conversation about {len(conversation_history)} previous topics)"
            
        intent_info = ""
        if user_intent:
            primary_intent = user_intent.get('primary_intent', 'general')
            intent_info = f" focusing on {primary_intent}"
            
        # Generate mock response
        response = f"Based on your question: '{question}'{context_info}, I found {len(sources)} relevant documents{intent_info}.\n\n"
        
        if sources:
            response += f"According to {sources[0].title}:\n"
            response += sources[0].content[:200] + "...\n\n"
            
        response += "This is a mock response. In the full implementation, this would be an AI-generated answer "
        response += "combining information from multiple documents using RAG (Retrieval-Augmented Generation) techniques."
        
        if user_intent and user_intent.get('primary_intent') == 'export_process':
            response += "\n\n🎯 **Export Process Steps:**\n"
            response += "1. Obtain IEC (Import Export Code)\n"
            response += "2. Prepare required documents\n"
            response += "3. Apply for necessary licenses\n"
            response += "4. Complete customs formalities"
            
        return response

# Global RAG integration instance
rag_integration = RAGIntegration()

async def get_rag_integration() -> RAGIntegration:
    """Dependency function to get initialized RAG integration"""
    if not rag_integration.is_initialized:
        await rag_integration.initialize()
    return rag_integration