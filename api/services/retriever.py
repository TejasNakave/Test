import logging
from typing import List, Dict, Any, Optional
from ..config import settings
from ..schemas import RetrievalResult
import time
from .vector_store import initialize_vectorstore

logger = logging.getLogger(__name__)

class RetrieverService:
    """Service for retrieving relevant chunks using integrated vector store"""
    
    def __init__(self):
        self.top_k = settings.TOP_K_RETRIEVAL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.vector_store = None
        
        # Initialize vector store with your data
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the vector store with OpenAI embeddings and your documents"""
        try:
            logger.info("Initializing vector store with your documents...")
            self.vector_store = initialize_vectorstore(
                force_rebuild=False,  # Use existing if available
                use_openai_embeddings=True,
                openai_api_key=settings.LLM_API_KEY
            )
            
            if self.vector_store:
                info = self.vector_store.get_vectorstore_info()
                logger.info(f"Vector store initialized successfully: {info}")
            else:
                logger.error("Failed to initialize vector store - will use fallback mode")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            self.vector_store = None
    
    async def retrieve(
        self, 
        query: str, 
        user_id: str, 
        conversation_id: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Retrieve top_k most relevant chunks from vector store
        
        Args:
            query: User question/query
            user_id: User identifier for logging
            conversation_id: Conversation context
            top_k: Number of chunks to retrieve (overrides default)
            filters: Additional filters for retrieval
            
        Returns:
            RetrievalResult with chunks and metadata
        """
        start_time = time.time()
        retrieval_top_k = top_k or self.top_k
        
        try:
            logger.info(f"Retrieving {retrieval_top_k} chunks for query: {query[:50]}...")
            
            # Use vector store for retrieval
            if not self.vector_store:
                logger.warning("Vector store not available, returning empty results")
                return RetrievalResult(
                    chunks=[],
                    total_results=0,
                    query_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Perform similarity search
            search_results = self.vector_store.similarity_search(
                query=query,
                k=retrieval_top_k,
                threshold=self.similarity_threshold
            )
            
            # Convert to expected format
            chunks = []
            for result in search_results:
                chunk_data = {
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "score": result.metadata.get("score", 1.0)
                }
                chunks.append(chunk_data)
            
            query_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Retrieved {len(chunks)} chunks in {query_time_ms}ms")
            
            return RetrievalResult(
                chunks=chunks,
                total_results=len(chunks),
                query_time_ms=query_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            return RetrievalResult(
                chunks=[],
                total_results=0,
                query_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def retrieve_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, Any]],
        user_id: str,
        conversation_id: str,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve chunks with conversation context for better relevance
        
        Args:
            query: Current user question
            conversation_history: Previous conversation turns
            user_id: User identifier
            conversation_id: Conversation identifier
            top_k: Number of chunks to retrieve
            
        Returns:
            RetrievalResult with contextually relevant chunks
        """
        try:
            # Build enhanced query with conversation context
            context_queries = []
            
            # Add recent conversation turns as context
            if conversation_history:
                recent_turns = conversation_history[-3:]  # Last 3 turns
                for turn in recent_turns:
                    if "question" in turn:
                        context_queries.append(turn["question"])
            
            # Combine current query with context
            enhanced_query = query
            if context_queries:
                context_text = " ".join(context_queries)
                enhanced_query = f"{query} Context: {context_text}"
            
            logger.info(f"Enhanced query with context: {enhanced_query[:100]}...")
            
            return await self.retrieve(
                query=enhanced_query,
                user_id=user_id,
                conversation_id=conversation_id,
                top_k=top_k
            )
            
        except Exception as e:
            logger.error(f"Error in contextual retrieval: {str(e)}")
            # Fallback to regular retrieval
            return await self.retrieve(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id,
                top_k=top_k
            )
    
    async def health_check(self) -> bool:
        """Check if vector store is accessible"""
        try:
            if not self.vector_store:
                return False
            
            # Test basic functionality
            info = self.vector_store.get_vectorstore_info()
            return info.get("total_documents", 0) > 0
        except Exception as e:
            logger.error(f"Vector store health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Clean up resources"""
        # No cleanup needed for vector store
        pass