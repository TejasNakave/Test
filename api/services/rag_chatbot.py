import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from ..config import settings
from ..schemas import ChatMessage, RAGResponse
from .vector_store import initialize_vectorstore
from .document_loader import DocumentLoader
from .llm_service import LLMService
from .retriever import RetrieverService
import os

logger = logging.getLogger(__name__)

class RAGChatbotService:
    """
    Enhanced RAG (Retrieval Augmented Generation) Chatbot Service
    Integrates document retrieval with LLM generation for context-aware responses
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.retriever_service = RetrieverService()
        self.document_loader = DocumentLoader()
        self.vector_store = None
        
        # RAG configuration
        self.max_context_length = settings.MAX_CONTEXT_LENGTH
        self.relevance_threshold = settings.SIMILARITY_THRESHOLD
        self.max_retrieved_chunks = settings.TOP_K_RETRIEVAL
        
        # Initialize vector store
        self._initialize_rag_system()
    
    def _initialize_rag_system(self):
        """Initialize the RAG system with document processing"""
        try:
            logger.info("Initializing RAG system...")
            
            # Initialize vector store
            self.vector_store = initialize_vectorstore(
                force_rebuild=False,
                use_openai_embeddings=True,
                openai_api_key=settings.LLM_API_KEY
            )
            
            if self.vector_store:
                info = self.vector_store.get_vectorstore_info()
                logger.info(f"RAG system initialized: {info}")
                
                # Check if we need to load documents (disabled for now to prevent startup issues)
                if False and info.get("total_documents", 0) == 0:
                    logger.info("Document auto-loading disabled for stability")
                    # self._load_initial_documents()
            else:
                logger.error("Failed to initialize vector store for RAG")
                
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
    
    def _load_initial_documents(self):
        """Load documents from the data folder if available"""
        try:
            data_folder = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            
            if os.path.exists(data_folder):
                logger.info(f"Loading documents from: {data_folder}")
                
                # Find all DOCX files
                docx_files = []
                for root, dirs, files in os.walk(data_folder):
                    for file in files:
                        if file.lower().endswith('.docx'):
                            docx_files.append(os.path.join(root, file))
                
                if docx_files:
                    logger.info(f"Found {len(docx_files)} DOCX files to process")
                    
                    # Process each document
                    for docx_file in docx_files:
                        try:
                            self.add_document_to_knowledge_base(docx_file)
                        except Exception as e:
                            logger.error(f"Error processing {docx_file}: {str(e)}")
                else:
                    logger.info("No DOCX files found in data folder")
            else:
                logger.info(f"Data folder not found: {data_folder}")
                
        except Exception as e:
            logger.error(f"Error loading initial documents: {str(e)}")
    
    async def chat_with_rag(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        use_context: bool = True
    ) -> RAGResponse:
        """
        Generate response using RAG (Retrieval Augmented Generation)
        
        Args:
            message: User message/question
            user_id: User identifier
            conversation_id: Conversation identifier
            conversation_history: Previous conversation context
            use_context: Whether to use retrieved context
            
        Returns:
            RAGResponse with generated answer and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG request: {message[:50]}...")
            
            retrieved_chunks = []
            context_used = ""
            
            if use_context and self.vector_store:
                # Retrieve relevant chunks
                retrieval_result = await self.retriever_service.retrieve_with_context(
                    query=message,
                    conversation_history=[msg.dict() for msg in conversation_history] if conversation_history else [],
                    user_id=user_id,
                    conversation_id=conversation_id,
                    top_k=self.max_retrieved_chunks
                )
                
                retrieved_chunks = retrieval_result.chunks
                
                # Build context from retrieved chunks
                if retrieved_chunks:
                    context_parts = []
                    for chunk in retrieved_chunks:
                        content = chunk.get("content", "")
                        source = chunk.get("metadata", {}).get("source", "Unknown")
                        context_parts.append(f"[Source: {source}]\n{content}")
                    
                    context_used = "\n\n".join(context_parts)
                    logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks")
                else:
                    logger.info("No relevant chunks found for query")
            
            # Prepare prompt with context
            if context_used and use_context:
                enhanced_prompt = f"""Based on the following context, please answer the user's question. If the context doesn't contain enough information to fully answer the question, say so and provide what information you can.

Context:
{context_used}

User Question: {message}

Please provide a helpful and accurate response based on the context provided."""
            else:
                enhanced_prompt = message
            
            # Generate response using LLM
            llm_response = await self.llm_service.generate_response(
                message=enhanced_prompt,
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_history=conversation_history
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create RAG response
            rag_response = RAGResponse(
                response=llm_response.response,
                retrieved_chunks=retrieved_chunks,
                context_used=bool(context_used),
                processing_time_ms=processing_time_ms,
                confidence_score=self._calculate_confidence_score(retrieved_chunks, message),
                sources=self._extract_sources(retrieved_chunks)
            )
            
            logger.info(f"RAG response generated in {processing_time_ms}ms")
            return rag_response
            
        except Exception as e:
            logger.error(f"Error in RAG chat: {str(e)}")
            
            # Fallback to regular LLM response
            try:
                fallback_response = await self.llm_service.generate_response(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history
                )
                
                return RAGResponse(
                    response=fallback_response.response,
                    retrieved_chunks=[],
                    context_used=False,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    confidence_score=0.5,
                    sources=[]
                )
            except Exception as fallback_error:
                logger.error(f"Fallback response also failed: {str(fallback_error)}")
                return RAGResponse(
                    response="I'm sorry, I'm experiencing technical difficulties. Please try again later.",
                    retrieved_chunks=[],
                    context_used=False,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    confidence_score=0.0,
                    sources=[]
                )
    
    def _calculate_confidence_score(self, chunks: List[Dict], query: str) -> float:
        """Calculate confidence score based on retrieved chunks"""
        if not chunks:
            return 0.3  # Low confidence without context
        
        # Simple confidence calculation based on similarity scores
        scores = [chunk.get("score", 0.0) for chunk in chunks]
        if scores:
            avg_score = sum(scores) / len(scores)
            return min(max(avg_score, 0.0), 1.0)
        
        return 0.5  # Medium confidence
    
    def _extract_sources(self, chunks: List[Dict]) -> List[str]:
        """Extract unique sources from retrieved chunks"""
        sources = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            source = metadata.get("source")
            if source:
                # Clean up source path
                source_name = os.path.basename(source) if os.path.sep in source else source
                sources.add(source_name)
        
        return list(sources)
    
    def add_document_to_knowledge_base(self, file_path: str) -> bool:
        """
        Add a new document to the knowledge base
        
        Args:
            file_path: Path to the document file
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Adding document to knowledge base: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            # Extract and process document
            documents = self.document_loader.load_single_document(file_path)
            
            if not documents:
                logger.warning(f"No content extracted from: {file_path}")
                return False
            
            # Add to vector store
            if self.vector_store:
                self.vector_store.add_documents(documents)
                logger.info(f"Successfully added {len(documents)} chunks from {file_path}")
                return True
            else:
                logger.error("Vector store not initialized")
                return False
                
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {str(e)}")
            return False
    
    async def get_knowledge_base_info(self) -> Dict[str, Any]:
        """Get information about the current knowledge base"""
        try:
            if self.vector_store:
                info = self.vector_store.get_vectorstore_info()
                
                # Add health check
                health_status = await self.retriever_service.health_check()
                
                return {
                    **info,
                    "health_status": health_status,
                    "retrieval_threshold": self.relevance_threshold,
                    "max_chunks": self.max_retrieved_chunks
                }
            else:
                return {
                    "total_documents": 0,
                    "health_status": False,
                    "error": "Vector store not initialized"
                }
                
        except Exception as e:
            logger.error(f"Error getting knowledge base info: {str(e)}")
            return {
                "total_documents": 0,
                "health_status": False,
                "error": str(e)
            }
    
    async def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant content
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            if not self.vector_store:
                return []
            
            retrieval_result = await self.retriever_service.retrieve(
                query=query,
                user_id="search",
                conversation_id="search",
                top_k=top_k
            )
            
            return retrieval_result.chunks
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.retriever_service.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")