"""
Test script to verify document search functionality
"""
import os
import sys
sys.path.append('api/services')

from vector_store import VectorStore
from document_loader import DocumentLoader

def test_search():
    print("Testing document search...")
    
    # Test document loading
    doc_loader = DocumentLoader()
    documents = doc_loader.load_documents()
    print(f"✅ Loaded {len(documents)} document chunks")
    
    # Test vector store
    vector_store = VectorStore(use_openai_embeddings=False)  # Use free embeddings for test
    vector_store.create_vectorstore(documents)
    
    # Test search queries
    test_queries = [
        "Import Policy",
        "import procedures", 
        "customs clearance",
        "export documentation",
        "DGFT schemes"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            results = vector_store.search(query, k=3)
            if results:
                print(f"   Found {len(results)} results:")
                for i, doc in enumerate(results[:2]):
                    print(f"   {i+1}. {doc.metadata.get('source', 'Unknown')}")
                    print(f"      Content preview: {doc.page_content[:100]}...")
            else:
                print("   ❌ No results found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_search()