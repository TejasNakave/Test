"""
Test script for the data-driven trade filter
Validates that the filter correctly analyzes your trade documents and restricts topics
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the data-driven filter
try:
    from api.services.data_driven_trade_filter import data_driven_filter
    print("✅ Successfully imported data-driven trade filter")
except ImportError as e:
    print(f"❌ Failed to import data-driven trade filter: {e}")
    sys.exit(1)

def test_data_analysis():
    """Test the data analysis functionality"""
    print("\n🔍 Testing Data Analysis...")
    
    summary = data_driven_filter.get_data_summary()
    
    print(f"📊 Analysis Results:")
    print(f"   • Status: {summary.get('analysis_status', 'Unknown')}")
    print(f"   • Total Documents: {summary.get('total_documents', 0)}")
    print(f"   • Key Topics: {len(summary.get('key_topics', []))}")
    print(f"   • Trade Entities: {len(summary.get('trade_entities', []))}")
    print(f"   • Coverage Areas: {len(summary.get('coverage_areas', []))}")
    
    if summary.get('key_topics'):
        print(f"   • Sample Topics: {summary['key_topics'][:5]}")
    
    if summary.get('trade_entities'):
        print(f"   • Sample Entities: {list(summary['trade_entities'])[:5]}")

def test_question_classification():
    """Test question classification against your trade data"""
    print("\n🧪 Testing Question Classification...")
    
    # Questions that SHOULD be allowed (based on your trade documents)
    trade_questions = [
        "How do I apply for IEC registration?",
        "What are the DGFT export promotion schemes?", 
        "Explain customs clearance procedures",
        "How does customs duty calculation work?",
        "What is the EPCG scheme?",
        "Tell me about advance authorization",
        "How to handle export documentation?",
        "What are the warehousing procedures?",
        "Explain HSN classification process",
        "How does customs valuation work?",
        "What are the dispute resolution procedures?",
        "Tell me about AEO certification",
        "How to start export business?",
        "What documents needed for import clearance?"
    ]
    
    # Questions that SHOULD be rejected (not in your trade data)
    non_trade_questions = [
        "What's the weather like today?",
        "Tell me a funny joke",
        "How to cook pasta?",
        "What's the latest movie?",
        "Personal relationship advice",
        "How to lose weight?",
        "What's the cricket score?",
        "Tell me about artificial intelligence"
    ]
    
    print("✅ Trade Questions (should be ACCEPTED):")
    for question in trade_questions:
        classification = data_driven_filter.classify_question(question)
        status = "✅ PASS" if classification.is_data_related else "❌ FAIL"
        confidence = f"({classification.confidence_score:.2f})"
        print(f"   {status} {confidence} - {question}")
        if classification.matched_topics:
            print(f"       📋 Topics: {classification.matched_topics[:3]}")
        if not classification.is_data_related:
            print(f"       ⚠️  Reason: {classification.reason}")
    
    print(f"\n🚫 Non-Trade Questions (should be REJECTED):")
    for question in non_trade_questions:
        classification = data_driven_filter.classify_question(question)
        status = "✅ PASS" if not classification.is_data_related else "❌ FAIL"
        confidence = f"({classification.confidence_score:.2f})"
        print(f"   {status} {confidence} - {question}")
        if classification.is_data_related:
            print(f"       ⚠️  Unexpected match: {classification.matched_topics}")

def test_document_coverage():
    """Test document coverage analysis"""
    print("\n📄 Testing Document Coverage...")
    
    if hasattr(data_driven_filter, 'document_topics'):
        print(f"📁 Document-Topic Mapping:")
        doc_topics = data_driven_filter.document_topics
        
        for i, (doc, topics) in enumerate(list(doc_topics.items())[:10]):  # Show first 10
            short_name = doc[:50] + "..." if len(doc) > 50 else doc
            print(f"   {i+1}. {short_name}")
            print(f"      Topics: {topics}")
        
        if len(doc_topics) > 10:
            print(f"   ... and {len(doc_topics) - 10} more documents")
    
    if hasattr(data_driven_filter, 'topic_document_map'):
        print(f"\n🏷️  Topic-Document Mapping:")
        topic_map = data_driven_filter.topic_document_map
        
        for topic, docs in list(topic_map.items())[:8]:  # Show first 8 topics
            print(f"   • {topic}: {len(docs)} documents")

def test_redirect_responses():
    """Test redirect response generation"""
    print("\n💬 Testing Redirect Responses...")
    
    test_questions = [
        "What's the weather like?",
        "How to cook food?",
        "Tell me about movies"
    ]
    
    for question in test_questions:
        classification = data_driven_filter.classify_question(question)
        if not classification.is_data_related:
            response = data_driven_filter.get_data_driven_redirect_response(question, classification)
            print(f"\nQuestion: {question}")
            print(f"Response Preview: {response[:200]}...")

def main():
    """Run all tests"""
    print("🚀 Data-Driven Trade Filter Test Suite")
    print("=" * 50)
    
    try:
        test_data_analysis()
        test_question_classification()
        test_document_coverage()
        test_redirect_responses()
        
        print("\n" + "=" * 50)
        print("🎉 Test Suite Completed!")
        print("\n📋 Summary:")
        
        if data_driven_filter.data_analysis:
            analysis = data_driven_filter.data_analysis
            print(f"   • Analyzed {analysis.total_documents} trade documents")
            print(f"   • Identified {len(analysis.key_topics)} key topics")
            print(f"   • Found {len(analysis.trade_entities)} trade entities")
            print(f"   • Covers {len(analysis.coverage_areas)} areas")
            
            print(f"\n🎯 Your chatbot is now restricted to:")
            for area in analysis.coverage_areas[:5]:
                print(f"   • {area}")
        
        print(f"\n🔧 Configuration saved to: {data_driven_filter.config_output_path}")
        print(f"📊 Monitor via: /api/v1/data-config/analysis-summary")
        print(f"🧪 Test questions: /api/v1/data-config/test-question")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()