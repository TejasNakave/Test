"""
Usage Router - Clean implementation matching frontend apiClient.js expectations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from api.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["usage"])

# Mock data storage (in production, use proper database)
user_usage_data = {}

@router.get("/usage/{user_id}")
async def get_user_usage_stats(
    user_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get usage statistics for a specific user
    Compatible with frontend apiClient.js expectations
    """
    try:
        logger.info(f"Getting usage stats for user {user_id}")
        
        # Get or create user usage data
        if user_id not in user_usage_data:
            user_usage_data[user_id] = {
                "user_id": user_id,
                "questions_asked": 0,
                "conversations_started": 0,
                "total_response_time_ms": 0,
                "avg_response_time_ms": 0,
                "last_activity": None,
                "most_asked_topics": [],
                "satisfaction_rating": None,
                "subscription_tier": "free",
                "quota_used": 0,
                "quota_limit": 100,
                "reset_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
        
        usage_data = user_usage_data[user_id]
        
        # Calculate dynamic stats
        if usage_data["questions_asked"] > 0:
            usage_data["avg_response_time_ms"] = (
                usage_data["total_response_time_ms"] / usage_data["questions_asked"]
            )
        
        # Determine subscription tier benefits
        tier_limits = {
            "free": 100,
            "basic": 500,
            "premium": -1  # unlimited
        }
        
        tier = usage_data.get("subscription_tier", "free")
        usage_data["quota_limit"] = tier_limits.get(tier, 100)
        
        # Calculate remaining quota
        if usage_data["quota_limit"] == -1:
            remaining_quota = -1  # unlimited
        else:
            remaining_quota = max(0, usage_data["quota_limit"] - usage_data["quota_used"])
        
        usage_data["remaining_quota"] = remaining_quota
        
        return {
            "success": True,
            "data": {
                "usage": usage_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats for user {user_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "usage": {
                    "user_id": user_id,
                    "questions_asked": 0,
                    "conversations_started": 0,
                    "last_activity": None,
                    "quota_used": 0,
                    "quota_limit": 100,
                    "remaining_quota": 100
                }
            }
        }

@router.post("/usage/{user_id}/update")
async def update_user_usage(
    user_id: str,
    usage_update: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Update usage statistics for a user
    """
    try:
        logger.info(f"Updating usage stats for user {user_id}")
        
        # Initialize user data if not exists
        if user_id not in user_usage_data:
            user_usage_data[user_id] = {
                "user_id": user_id,
                "questions_asked": 0,
                "conversations_started": 0,
                "total_response_time_ms": 0,
                "avg_response_time_ms": 0,
                "last_activity": None,
                "most_asked_topics": [],
                "satisfaction_rating": None,
                "subscription_tier": "free",
                "quota_used": 0,
                "quota_limit": 100,
                "reset_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
        
        usage_data = user_usage_data[user_id]
        
        # Update based on provided data
        if "question_asked" in usage_update:
            usage_data["questions_asked"] += 1
            usage_data["quota_used"] += 1
            usage_data["last_activity"] = datetime.now().isoformat()
        
        if "conversation_started" in usage_update:
            usage_data["conversations_started"] += 1
        
        if "response_time_ms" in usage_update:
            response_time = usage_update["response_time_ms"]
            usage_data["total_response_time_ms"] += response_time
            
            # Recalculate average
            if usage_data["questions_asked"] > 0:
                usage_data["avg_response_time_ms"] = (
                    usage_data["total_response_time_ms"] / usage_data["questions_asked"]
                )
        
        if "topic" in usage_update:
            topic = usage_update["topic"]
            if topic not in usage_data["most_asked_topics"]:
                usage_data["most_asked_topics"].append(topic)
                # Keep only last 10 topics
                usage_data["most_asked_topics"] = usage_data["most_asked_topics"][-10:]
        
        if "satisfaction_rating" in usage_update:
            usage_data["satisfaction_rating"] = usage_update["satisfaction_rating"]
        
        return {
            "success": True,
            "message": f"Usage stats updated for user {user_id}",
            "data": {
                "usage": usage_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating usage stats for user {user_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/usage/{user_id}/summary")
async def get_user_usage_summary(
    user_id: str,
    days: int = 30,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get usage summary for a specific time period
    """
    try:
        logger.info(f"Getting {days} day usage summary for user {user_id}")
        
        if user_id not in user_usage_data:
            return {
                "success": True,
                "data": {
                    "summary": {
                        "user_id": user_id,
                        "period_days": days,
                        "total_questions": 0,
                        "total_conversations": 0,
                        "avg_daily_questions": 0,
                        "most_active_day": None,
                        "engagement_score": 0
                    }
                }
            }
        
        usage_data = user_usage_data[user_id]
        
        # Calculate summary metrics
        total_questions = usage_data.get("questions_asked", 0)
        total_conversations = usage_data.get("conversations_started", 0)
        avg_daily_questions = total_questions / days if days > 0 else 0
        
        # Calculate engagement score (0-100)
        engagement_score = min(100, (total_questions * 2) + (total_conversations * 5))
        
        summary = {
            "user_id": user_id,
            "period_days": days,
            "total_questions": total_questions,
            "total_conversations": total_conversations,
            "avg_daily_questions": round(avg_daily_questions, 2),
            "avg_response_time_ms": usage_data.get("avg_response_time_ms", 0),
            "most_asked_topics": usage_data.get("most_asked_topics", [])[-5:],  # Last 5 topics
            "engagement_score": round(engagement_score, 1),
            "subscription_tier": usage_data.get("subscription_tier", "free"),
            "quota_utilization": round(
                (usage_data.get("quota_used", 0) / usage_data.get("quota_limit", 100)) * 100, 1
            ) if usage_data.get("quota_limit", 100) > 0 else 0
        }
        
        return {
            "success": True,
            "data": {
                "summary": summary
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage summary for user {user_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.delete("/usage/{user_id}/reset")
async def reset_user_usage(
    user_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Reset usage statistics for a user (admin function)
    """
    try:
        logger.info(f"Resetting usage stats for user {user_id}")
        
        if user_id in user_usage_data:
            # Reset counters but keep user preferences
            user_data = user_usage_data[user_id]
            user_data.update({
                "questions_asked": 0,
                "conversations_started": 0,
                "total_response_time_ms": 0,
                "avg_response_time_ms": 0,
                "quota_used": 0,
                "reset_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "last_reset": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "message": f"Usage statistics reset for user {user_id}",
            "data": {
                "user_id": user_id,
                "reset_timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting usage for user {user_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Helper function to be called from other parts of the application
def track_usage_event(user_id: str, event_type: str, metadata: Dict[str, Any] = None):
    """
    Track usage events for analytics
    """
    try:
        if metadata is None:
            metadata = {}
            
        # Initialize user data if not exists
        if user_id not in user_usage_data:
            user_usage_data[user_id] = {
                "user_id": user_id,
                "questions_asked": 0,
                "conversations_started": 0,
                "total_response_time_ms": 0,
                "avg_response_time_ms": 0,
                "last_activity": None,
                "most_asked_topics": [],
                "satisfaction_rating": None,
                "subscription_tier": "free",
                "quota_used": 0,
                "quota_limit": 100,
                "reset_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
        
        usage_data = user_usage_data[user_id]
        usage_data["last_activity"] = datetime.now().isoformat()
        
        if event_type == "question":
            usage_data["questions_asked"] += 1
            usage_data["quota_used"] += 1
            
            if "response_time_ms" in metadata:
                usage_data["total_response_time_ms"] += metadata["response_time_ms"]
                usage_data["avg_response_time_ms"] = (
                    usage_data["total_response_time_ms"] / usage_data["questions_asked"]
                )
            
            if "topic" in metadata:
                topic = metadata["topic"]
                if topic not in usage_data["most_asked_topics"]:
                    usage_data["most_asked_topics"].append(topic)
                    usage_data["most_asked_topics"] = usage_data["most_asked_topics"][-10:]
        
        elif event_type == "conversation_start":
            usage_data["conversations_started"] += 1
        
        elif event_type == "feedback":
            if "rating" in metadata:
                usage_data["satisfaction_rating"] = metadata["rating"]
        
        logger.info(f"Tracked usage event for user {user_id}: {event_type}")
        
    except Exception as e:
        logger.error(f"Error tracking usage event: {str(e)}")