"""
Vector database setup and RAG retrieval system using ChromaDB.
Integrated with ChatGPT-like Proactive Chatbot backend.
"""
import os
import sys
from typing import List, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings  # Fixed import
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import logging

# Handle imports for both module and script execution
try:
    from .document_loader import DocumentLoader
except ImportError:
    # When running as script, add the parent directory to path
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(parent_dir)
    sys.path.insert(0, project_root)
    sys.path.insert(0, current_dir)
    from document_loader import DocumentLoader

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, 
                 persist_directory: str = "chroma_db",
                 use_openai_embeddings: bool = True,  # Default to True for better quality
                 openai_api_key: Optional[str] = None):
        
        self.persist_directory = persist_directory
        self.use_openai_embeddings = use_openai_embeddings
        
        # Initialize embeddings
        if use_openai_embeddings and openai_api_key:
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            logger.info("Using OpenAI embeddings")
        else:
            # Use free Hugging Face embeddings as fallback
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("Using Hugging Face embeddings")
        
        self.vectorstore = None
        self.retriever = None
    
    def create_vectorstore(self, documents: List[Document]) -> None:
        """Create and persist vector store from documents."""
        if not documents:
            logger.error("No documents provided for vector store creation")
            return
        
        logger.info(f"Creating vector store with {len(documents)} documents...")
        
        # Create ChromaDB vector store
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        logger.info(f"Vector store created and persisted to {self.persist_directory}")
    
    def load_vectorstore(self) -> bool:
        """Load existing vector store from disk."""
        if os.path.exists(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                logger.info(f"Vector store loaded from {self.persist_directory}")
                return True
            except Exception as e:
                logger.error(f"Error loading vector store: {str(e)}")
                return False
        else:
            logger.warning(f"Vector store directory {self.persist_directory} not found")
            return False
    
    def setup_retriever(self, search_type: str = "similarity", search_kwargs: dict = None) -> None:
        """Setup retriever for the vector store."""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return
        
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        # Create vector retriever
        vector_retriever = self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
        
        # Try to setup BM25 retriever for hybrid search
        try:
            doc_loader = DocumentLoader()
            documents = doc_loader.load_documents()
            
            if documents:
                # Create BM25 retriever for keyword search
                bm25_retriever = BM25Retriever.from_documents(documents)
                bm25_retriever.k = search_kwargs.get("k", 5)
                
                # Combine both retrievers for better results
                self.retriever = EnsembleRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    weights=[0.7, 0.3]  # Favor semantic search slightly
                )
                logger.info("Ensemble retriever (Vector + BM25) setup complete")
            else:
                self.retriever = vector_retriever
                logger.info("Vector retriever setup complete (no documents for BM25)")
                
        except Exception as e:
            logger.warning(f"Could not setup BM25 retriever: {str(e)}")
            self.retriever = vector_retriever
            logger.info("Vector retriever setup complete (fallback)")
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents."""
        if not self.retriever:
            logger.error("Retriever not initialized")
            return []
        
        try:
            results = self.retriever.get_relevant_documents(query)
            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results[:k]
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_vectorstore_info(self) -> dict:
        """Get information about the vector store."""
        if not self.vectorstore:
            return {"status": "not_initialized"}
        
        try:
            # Get collection info
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "status": "initialized",
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": type(self.embeddings).__name__
            }
        except Exception as e:
            logger.error(f"Error getting vectorstore info: {str(e)}")
            return {"status": "error", "error": str(e)}

def initialize_vectorstore(force_rebuild: bool = False, 
                          use_openai_embeddings: bool = True,
                          openai_api_key: Optional[str] = None) -> VectorStore:
    """Initialize vector store with documents."""
    persist_dir = "chroma_db_new" if force_rebuild else "chroma_db"
    vs = VectorStore(
        persist_directory=persist_dir,
        use_openai_embeddings=use_openai_embeddings, 
        openai_api_key=openai_api_key
    )
    
    # Try to load existing vector store
    if not force_rebuild and vs.load_vectorstore():
        logger.info("Using existing vector store")
    else:
        logger.info("Creating new vector store...")
        try:
            doc_loader = DocumentLoader()
            documents = doc_loader.load_documents()
            
            if documents:
                vs.create_vectorstore(documents)
                logger.info(f"Vector store created with {len(documents)} documents")
            else:
                logger.error("No documents found to create vector store")
                return None
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            return None
    
    # Setup retriever
    vs.setup_retriever()
    return vs

if __name__ == "__main__":
    """Test the vector store functionality."""
    import sys
    import os
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Change to project root directory for proper paths
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    os.chdir(project_root)
    
    # Add the project root to path for imports
    sys.path.insert(0, project_root)
    
    print("🚀 Initializing Vector Store...")
    print(f"📁 Working from: {os.getcwd()}")
    print("=" * 50)
    
    try:
        # Initialize vector store
        vector_store = initialize_vectorstore(
            force_rebuild=True,  # Force rebuild to avoid database schema issues
            use_openai_embeddings=False  # Use free embeddings for testing
        )
        
        if vector_store:
            print("✅ Vector store initialized successfully!")
            
            # Get info
            info = vector_store.get_vectorstore_info()
            print(f"📊 Vector Store Info:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            # Test search functionality
            print("\n🔍 Testing search functionality...")
            test_query = "What is artificial intelligence?"
            results = vector_store.search_documents(test_query, k=3)
            
            print(f"Query: '{test_query}'")
            print(f"Found {len(results)} results:")
            
            for i, doc in enumerate(results, 1):
                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                print(f"   {i}. {content_preview}")
                if hasattr(doc, 'metadata') and doc.metadata:
                    print(f"      Source: {doc.metadata.get('source', 'Unknown')}")
            
            print("\n✨ Vector store test completed successfully!")
            
        else:
            print("❌ Failed to initialize vector store")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)