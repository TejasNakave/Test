"""
Data-Driven Configuration API Router
Provides endpoints to monitor and manage the data-driven trade filter
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

try:
    from api.services.data_driven_trade_filter import data_driven_filter
    FILTER_AVAILABLE = True
except ImportError:
    FILTER_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-config", tags=["Data Configuration"])

class DataAnalysisResponse(BaseModel):
    status: str
    total_documents: int
    key_topics: List[str]
    coverage_areas: List[str]
    document_categories: Dict[str, int]
    trade_entities: List[str]

class QuestionTestRequest(BaseModel):
    question: str

@router.get("/analysis-summary", response_model=DataAnalysisResponse)
async def get_data_analysis_summary():
    """Get summary of the current data analysis"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        summary = data_driven_filter.get_data_summary()
        
        return DataAnalysisResponse(
            status=summary.get("analysis_status", "unknown"),
            total_documents=summary.get("total_documents", 0),
            key_topics=summary.get("key_topics", []),
            coverage_areas=summary.get("coverage_areas", []),
            document_categories=summary.get("document_categories", {}),
            trade_entities=summary.get("trade_entities", [])
        )
    except Exception as e:
        logger.error(f"Error getting data analysis summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis summary: {str(e)}")

@router.post("/reanalyze")
async def trigger_data_reanalysis(background_tasks: BackgroundTasks):
    """Trigger reanalysis of the trade data"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        # Trigger reanalysis in background
        background_tasks.add_task(data_driven_filter._analyze_data_content)
        
        return {
            "message": "Data reanalysis triggered successfully", 
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Error triggering data reanalysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger reanalysis: {str(e)}")

@router.post("/test-question")
async def test_question_classification(request: QuestionTestRequest):
    """Test how a question would be classified against the data"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        classification = data_driven_filter.classify_question(request.question)
        
        return {
            "question": request.question,
            "is_data_related": classification.is_data_related,
            "confidence_score": classification.confidence_score,
            "matched_topics": classification.matched_topics,
            "relevant_documents": classification.relevant_documents,
            "reason": classification.reason,
            "coverage_gap": classification.coverage_gap,
            "recommendation": "Question allowed" if classification.is_data_related else "Question would be redirected"
        }
    except Exception as e:
        logger.error(f"Error testing question classification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test question: {str(e)}")

@router.get("/document-topics")
async def get_document_topics():
    """Get mapping of documents to topics"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        return {
            "document_topics": data_driven_filter.document_topics,
            "topic_document_map": dict(data_driven_filter.topic_document_map),
            "total_documents": len(data_driven_filter.document_topics),
            "total_topics": len(data_driven_filter.topic_document_map)
        }
    except Exception as e:
        logger.error(f"Error getting document topics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document topics: {str(e)}")

@router.get("/coverage-gaps")
async def identify_coverage_gaps():
    """Identify potential gaps in data coverage"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        # Common trade topics that might not be covered
        expected_topics = [
            'iec_registration', 'export_procedures', 'import_procedures', 
            'customs_clearance', 'dgft_schemes', 'duty_calculations',
            'hsn_classification', 'export_incentives', 'trade_agreements',
            'compliance_requirements', 'documentation', 'licensing',
            'valuation_procedures', 'dispute_resolution'
        ]
        
        analysis = data_driven_filter.data_analysis
        if not analysis:
            return {"status": "No analysis available"}
        
        covered_topics = set(analysis.key_topics)
        missing_topics = [topic for topic in expected_topics if topic not in covered_topics]
        
        return {
            "total_expected_topics": len(expected_topics),
            "covered_topics": len(covered_topics),
            "coverage_percentage": (len(covered_topics) / len(expected_topics)) * 100,
            "missing_topics": missing_topics,
            "well_covered_topics": analysis.key_topics,
            "recommendations": [
                f"Consider adding documentation for: {topic}" for topic in missing_topics[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Error identifying coverage gaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to identify coverage gaps: {str(e)}")

@router.get("/filter-stats")
async def get_filter_statistics():
    """Get statistics about the data-driven filter performance"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        analysis = data_driven_filter.data_analysis
        if not analysis:
            return {"status": "No analysis available"}
        
        # Calculate statistics
        confidence_stats = {}
        if analysis.confidence_keywords:
            confidence_values = list(analysis.confidence_keywords.values())
            confidence_stats = {
                "average_confidence": sum(confidence_values) / len(confidence_values),
                "high_confidence_topics": len([v for v in confidence_values if v >= 0.8]),
                "medium_confidence_topics": len([v for v in confidence_values if 0.5 <= v < 0.8]),
                "low_confidence_topics": len([v for v in confidence_values if v < 0.5])
            }
        
        return {
            "filter_status": "active",
            "data_analysis_complete": True,
            "total_documents_analyzed": analysis.total_documents,
            "unique_topics_identified": len(analysis.key_topics),
            "trade_entities_found": len(analysis.trade_entities),
            "coverage_areas": len(analysis.coverage_areas),
            "confidence_statistics": confidence_stats,
            "document_distribution": {
                category: len(docs) 
                for category, docs in analysis.document_categories.items()
            }
        }
    except Exception as e:
        logger.error(f"Error getting filter statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get filter statistics: {str(e)}")

@router.get("/sample-questions")
async def get_sample_questions_for_data():
    """Generate sample questions based on the analyzed data"""
    if not FILTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data-driven filter not available")
    
    try:
        analysis = data_driven_filter.data_analysis
        if not analysis:
            return {"status": "No analysis available"}
        
        # Generate sample questions based on actual data topics
        sample_questions = []
        
        topic_questions = {
            'dgft': "What are the latest DGFT policy updates and schemes?",
            'export': "How do I complete export clearance procedures?",
            'import': "What are the import licensing requirements?",
            'customs': "How is customs duty calculated for my goods?",
            'certification': "What certifications do I need for export?",
            'valuation': "How does customs valuation work for imports?",
            'classification': "How do I find the correct HSN code?",
            'schemes': "Which export promotion schemes can I apply for?",
            'compliance': "What are the trade compliance requirements?",
            'documentation': "What documents are needed for export?"
        }
        
        # Generate questions based on covered topics
        for topic in analysis.key_topics:
            if topic in topic_questions:
                sample_questions.append({
                    "topic": topic,
                    "question": topic_questions[topic],
                    "document_count": len(data_driven_filter.topic_document_map.get(topic, [])),
                    "confidence": analysis.confidence_keywords.get(topic, 0.5)
                })
        
        # Add entity-based questions
        for entity in list(analysis.trade_entities)[:5]:
            sample_questions.append({
                "topic": f"entity_{entity}",
                "question": f"Tell me about {entity} and its role in trade",
                "document_count": "multiple",
                "confidence": 0.8
            })
        
        return {
            "total_sample_questions": len(sample_questions),
            "questions_by_topic": sample_questions,
            "recommendation": "These questions should receive comprehensive answers based on your data"
        }
    except Exception as e:
        logger.error(f"Error generating sample questions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate sample questions: {str(e)}")