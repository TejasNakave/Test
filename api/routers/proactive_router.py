"""
Proactive Router - Handle proactive suggestions and user insights
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from api.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["proactive"])

# Mock data storage for user behavior
user_insights_data = {}
suggestion_templates = {
    "export_process": [
        "What documents are needed for export?",
        "How to get export license?",
        "What are export incentives?",
        "Export procedure step by step"
    ],
    "import_process": [
        "Import licensing process", 
        "Custom duty calculation",
        "Import documentation required",
        "How to clear customs for imports"
    ],
    "dgft": [
        "DGFT registration process",
        "Latest DGFT circulars", 
        "DGFT export promotion schemes",
        "How to contact DGFT office"
    ],
    "iec": [
        "IEC code application online",
        "IEC renewal procedure",
        "Documents for IEC registration",
        "IEC code fees and charges"
    ],
    "general": [
        "Foreign trade policy updates",
        "Export import procedures", 
        "Custom clearance process",
        "Trade documentation requirements"
    ]
}

@router.get("/proactive/suggestions")
async def get_proactive_suggestions(
    user_id: str = "anonymous",
    conversation_id: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get proactive suggestions based on conversation context
    Compatible with frontend apiClient.js expectations
    """
    try:
        logger.info(f"Getting proactive suggestions for user {user_id}")
        
        # Get user behavior insights
        user_behavior = user_insights_data.get(user_id, {})
        recent_topics = user_behavior.get("recent_topics", [])
        expertise_level = user_behavior.get("expertise_level", "intermediate")
        
        # Generate contextual suggestions based on recent activity
        suggestions = []
        
        if recent_topics:
            # Use recent topics to suggest related questions
            for topic in recent_topics[-2:]:  # Last 2 topics
                topic_suggestions = suggestion_templates.get(topic, suggestion_templates["general"])
                suggestions.extend(topic_suggestions[:2])  # 2 per topic
        else:
            # Default suggestions for new users
            suggestions = [
                "What is DGFT and its role in foreign trade?",
                "How do I obtain an IEC certificate?", 
                "What are the export procedures in India?",
                "Tell me about import documentation requirements"
            ]
        
        # Limit to 6 suggestions
        suggestions = suggestions[:6]
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "context": {
                    "recent_topics": recent_topics,
                    "expertise_level": expertise_level,
                    "suggestion_count": len(suggestions)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting proactive suggestions: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "suggestions": suggestion_templates["general"][:4]  # Fallback
            }
        }

@router.get("/proactive/insights/{user_id}")
async def get_user_insights(
    user_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get user behavior insights
    Compatible with frontend apiClient.js expectations
    """
    try:
        logger.info(f"Getting user insights for user {user_id}")
        
        # Get or create user insights
        if user_id not in user_insights_data:
            user_insights_data[user_id] = {
                "user_id": user_id,
                "total_questions": 0,
                "recent_topics": [],
                "expertise_level": "beginner",
                "last_activity": None,
                "preferred_question_types": [],
                "session_count": 0,
                "avg_session_duration": 0,
                "most_asked_topics": {},
                "learning_progression": "stable"
            }
        
        insights = user_insights_data[user_id]
        
        # Calculate some dynamic insights
        now = datetime.now()
        insights["last_updated"] = now.isoformat()
        
        # Determine expertise level based on activity
        total_questions = insights.get("total_questions", 0)
        if total_questions > 50:
            insights["expertise_level"] = "advanced"
        elif total_questions > 20:
            insights["expertise_level"] = "intermediate"
        else:
            insights["expertise_level"] = "beginner"
        
        # Generate recommendations
        recommendations = []
        expertise = insights["expertise_level"]
        
        if expertise == "beginner":
            recommendations = [
                "Start with basic export-import concepts",
                "Learn about DGFT and its services",
                "Understand IEC certificate importance"
            ]
        elif expertise == "intermediate":
            recommendations = [
                "Explore advanced export schemes",
                "Learn about customs procedures",
                "Study trade documentation in detail"
            ]
        else:
            recommendations = [
                "Stay updated with latest trade policies",
                "Explore niche export markets",
                "Advanced compliance strategies"
            ]
        
        return {
            "success": True,
            "data": {
                "insights": insights,
                "recommendations": recommendations,
                "analytics": {
                    "engagement_score": min(100, total_questions * 2),
                    "knowledge_areas": list(insights.get("most_asked_topics", {}).keys())[:5],
                    "learning_streak": insights.get("session_count", 0),
                    "proficiency_trend": "improving" if total_questions > 10 else "starting"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user insights: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "insights": {},
                "recommendations": [],
                "analytics": {}
            }
        }

@router.post("/proactive/insights/{user_id}/update")
async def update_user_insights(
    user_id: str,
    data: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Update user insights based on activity
    """
    try:
        logger.info(f"Updating insights for user {user_id}")
        
        if user_id not in user_insights_data:
            user_insights_data[user_id] = {
                "user_id": user_id,
                "total_questions": 0,
                "recent_topics": [],
                "expertise_level": "beginner",
                "last_activity": None,
                "preferred_question_types": [],
                "session_count": 0,
                "avg_session_duration": 0,
                "most_asked_topics": {},
                "learning_progression": "stable"
            }
        
        insights = user_insights_data[user_id]
        
        # Update based on provided data
        if "question" in data:
            insights["total_questions"] += 1
            insights["last_activity"] = datetime.now().isoformat()
        
        if "topic" in data:
            topic = data["topic"]
            if topic not in insights["most_asked_topics"]:
                insights["most_asked_topics"][topic] = 0
            insights["most_asked_topics"][topic] += 1
            
            # Update recent topics (keep last 10)
            if topic not in insights["recent_topics"]:
                insights["recent_topics"].append(topic)
                insights["recent_topics"] = insights["recent_topics"][-10:]
        
        if "session_start" in data:
            insights["session_count"] += 1
        
        return {
            "success": True,
            "message": f"Insights updated for user {user_id}",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error updating user insights: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Helper function to be called from other parts of the application
def track_user_activity(user_id: str, activity_type: str, metadata: Dict[str, Any] = None):
    """
    Track user activity for insights generation
    """
    try:
        if metadata is None:
            metadata = {}
            
        if user_id not in user_insights_data:
            user_insights_data[user_id] = {
                "user_id": user_id,
                "total_questions": 0,
                "recent_topics": [],
                "expertise_level": "beginner",
                "last_activity": None,
                "preferred_question_types": [],
                "session_count": 0,
                "avg_session_duration": 0,
                "most_asked_topics": {},
                "learning_progression": "stable"
            }
        
        insights = user_insights_data[user_id]
        insights["last_activity"] = datetime.now().isoformat()
        
        if activity_type == "question":
            insights["total_questions"] += 1
            if "topic" in metadata:
                topic = metadata["topic"]
                if topic not in insights["most_asked_topics"]:
                    insights["most_asked_topics"][topic] = 0
                insights["most_asked_topics"][topic] += 1
                
                if topic not in insights["recent_topics"]:
                    insights["recent_topics"].append(topic)
                    insights["recent_topics"] = insights["recent_topics"][-10:]
        
        logger.info(f"Tracked activity for user {user_id}: {activity_type}")
        
    except Exception as e:
        logger.error(f"Error tracking user activity: {str(e)}")