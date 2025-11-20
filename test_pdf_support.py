"""
Test script to verify PDF support in the enhanced document loader
"""
import logging
import os
from api.services.document_loader import DocumentLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_pdf_support():
    """Test PDF loading capabilities"""
    print("🔬 Testing Enhanced Document Loader with PDF Support")
    print("=" * 60)
    
    # Initialize document loader
    loader = DocumentLoader("data")
    
    # Check PDF support status
    pdf_available = loader.is_pdf_support_available()
    print(f"📄 PDF Support Available: {'✅ Yes' if pdf_available else '❌ No'}")
    
    # Show supported formats
    supported_formats = loader.get_supported_formats()
    print(f"📋 Supported Formats: {', '.join(supported_formats)}")
    
    # Get file information
    file_info = loader.get_file_info()
    print(f"\n📊 File Statistics:")
    for key, value in file_info.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Load documents
    print(f"\n🔄 Loading documents...")
    documents = loader.load_documents()
    
    if documents:
        print(f"✅ Successfully loaded {len(documents)} document chunks")
        
        # Show document breakdown by file type
        file_types = {}
        for doc in documents:
            file_type = doc.metadata.get('file_type', 'unknown')
            source = doc.metadata.get('source', 'unknown')
            
            if file_type not in file_types:
                file_types[file_type] = {'count': 0, 'files': set()}
            
            file_types[file_type]['count'] += 1
            file_types[file_type]['files'].add(source)
        
        print(f"\n📈 Document Breakdown:")
        for file_type, info in file_types.items():
            files_list = ', '.join(list(info['files'])[:3])  # Show first 3 files
            if len(info['files']) > 3:
                files_list += f" and {len(info['files']) - 3} more..."
            print(f"   {file_type.upper()}: {info['count']} chunks from {len(info['files'])} files")
            print(f"      Files: {files_list}")
        
        # Show sample content
        print(f"\n📖 Sample Content (first chunk):")
        sample_doc = documents[0]
        sample_content = sample_doc.page_content[:200]
        print(f"   Source: {sample_doc.metadata.get('source', 'unknown')}")
        print(f"   Content: {sample_content}...")
        
    else:
        print("⚠️ No documents loaded")
    
    print(f"\n🎉 Test completed!")

if __name__ == "__main__":
    test_pdf_support()