"""from fastapi import APIRouter, Depends, HTTPException

Usage Router - Analytics and usage statistics endpointsfrom ..schemas import UserRequest, UsageResponse, UsageStats, SubscriptionTier

"""from ..services.logger import LoggerService

from fastapi import APIRouter, HTTPException, Dependsfrom ..config import settings

from typing import Optional, Dict, Anyfrom datetime import datetime, timedelta

from datetime import datetime, timedeltaimport logging

import logging

router = APIRouter()

from api.schemas import UsageStats, ConversationAnalyticslogger = logging.getLogger(__name__)

from api.auth import get_optional_user

# Initialize logger service

logger = logging.getLogger(__name__)logger_service = LoggerService()



router = APIRouter(prefix="/api/v1", tags=["analytics"])@router.get("/usage", response_model=UsageResponse)

async def get_usage_stats(user_id: str) -> UsageResponse:

# Mock data storage (in production, use a proper database)    """

conversation_data = {}    Get usage statistics for a specific user including question count and quota

usage_statistics = {    """

    "total_conversations": 0,    try:

    "total_questions": 0,        logger.info(f"Getting usage stats for user {user_id}")

    "response_times": [],        

    "topics": {},        # Get user's current subscription tier (this would come from auth service)

    "user_ratings": []        # For now, defaulting to tier_1 - this should be replaced with actual auth lookup

}        subscription_tier = SubscriptionTier.TIER_1

        

@router.get("/usage/stats", response_model=UsageStats)        # Get question limits based on tier

async def get_usage_statistics(        question_limits = {

    days: int = 30,            SubscriptionTier.TIER_1: settings.TIER_1_LIMIT,

    current_user: Optional[dict] = Depends(get_optional_user)            SubscriptionTier.TIER_2: settings.TIER_2_LIMIT,

):            SubscriptionTier.TIER_3: settings.TIER_3_LIMIT

    """        }

    Get overall usage statistics        

    """        question_limit = question_limits[subscription_tier]

    try:        

        # Calculate average response time        # Calculate current period (monthly reset)

        avg_response_time = (        now = datetime.now()

            sum(usage_statistics["response_times"]) / len(usage_statistics["response_times"])        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if usage_statistics["response_times"] else 0        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)

        )        

                # Get usage stats from logger service

        # Get most common topics        usage_data = await logger_service.get_user_usage_stats(

        sorted_topics = sorted(            user_id=user_id,

            usage_statistics["topics"].items(),            start_date=current_month_start,

            key=lambda x: x[1],            end_date=now

            reverse=True        )

        )        

        most_common_topics = [topic for topic, count in sorted_topics[:5]]        questions_asked = usage_data.get("questions_count", 0)

                last_activity = usage_data.get("last_activity")

        # Calculate average user satisfaction        

        avg_satisfaction = (        # Calculate remaining questions

            sum(usage_statistics["user_ratings"]) / len(usage_statistics["user_ratings"])        if question_limit == -1:  # Unlimited for tier 3

            if usage_statistics["user_ratings"] else None            remaining_questions = -1

        )        else:

                    remaining_questions = max(0, question_limit - questions_asked)

        return UsageStats(        

            total_conversations=usage_statistics["total_conversations"],        usage_stats = UsageStats(

            total_questions=usage_statistics["total_questions"],            user_id=user_id,

            avg_response_time_ms=avg_response_time,            subscription_tier=subscription_tier,

            most_common_topics=most_common_topics,            questions_asked=questions_asked,

            user_satisfaction_avg=avg_satisfaction            question_limit=question_limit,

        )            remaining_questions=remaining_questions,

                    reset_date=next_month_start,

    except Exception as e:            last_activity=last_activity

        logger.error(f"Error getting usage statistics: {str(e)}")        )

        raise HTTPException(status_code=500, detail=str(e))        

        return UsageResponse(usage=usage_stats)

@router.get("/usage/conversations/{conversation_id}", response_model=ConversationAnalytics)        

async def get_conversation_analytics(    except Exception as e:

    conversation_id: str,        logger.error(f"Error getting usage stats for user {user_id}: {str(e)}")

    current_user: Optional[dict] = Depends(get_optional_user)        raise HTTPException(

):            status_code=500,

    """            detail=f"Failed to retrieve usage statistics: {str(e)}"

    Get analytics for a specific conversation        )

    """

    try:@router.get("/usage/{user_id}/history")

        if conversation_id not in conversation_data:async def get_usage_history(user_id: str, days: int = 30):

            raise HTTPException(status_code=404, detail="Conversation not found")    """

            Get detailed usage history for a user over specified number of days

        conversation = conversation_data[conversation_id]    """

            try:

        # Calculate conversation duration        logger.info(f"Getting {days} days of usage history for user {user_id}")

        start_time = conversation.get("start_time", datetime.now())        

        end_time = conversation.get("end_time", datetime.now())        end_date = datetime.now()

        duration = (end_time - start_time).total_seconds() / 60        start_date = end_date - timedelta(days=days)

                

        return ConversationAnalytics(        history = await logger_service.get_user_usage_history(

            conversation_id=conversation_id,            user_id=user_id,

            duration_minutes=duration,            start_date=start_date,

            question_count=conversation.get("question_count", 0),            end_date=end_date

            topics_covered=conversation.get("topics", []),        )

            user_satisfaction=conversation.get("satisfaction_rating"),        

            completion_status=conversation.get("status", "ongoing")        return {

        )            "user_id": user_id,

                    "period_days": days,

    except HTTPException:            "start_date": start_date,

        raise            "end_date": end_date,

    except Exception as e:            "history": history

        logger.error(f"Error getting conversation analytics: {str(e)}")        }

        raise HTTPException(status_code=500, detail=str(e))        

    except Exception as e:

@router.post("/usage/feedback")        logger.error(f"Error getting usage history for user {user_id}: {str(e)}")

async def record_feedback(        raise HTTPException(

    conversation_id: str,            status_code=500,

    rating: int,            detail=f"Failed to retrieve usage history: {str(e)}"

    feedback_text: Optional[str] = None,        )

    current_user: Optional[dict] = Depends(get_optional_user)

):@router.post("/usage/{user_id}/reset")

    """async def reset_user_usage(user_id: str):

    Record user feedback for a conversation    """

    """    Reset usage statistics for a user (admin function)

    try:    This would typically require admin authentication

        if rating < 1 or rating > 5:    """

            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")    try:

                logger.info(f"Resetting usage stats for user {user_id}")

        # Record the feedback        

        usage_statistics["user_ratings"].append(rating)        # This would include admin auth check in real implementation

                await logger_service.reset_user_usage(user_id)

        if conversation_id in conversation_data:        

            conversation_data[conversation_id]["satisfaction_rating"] = rating        return {

            conversation_data[conversation_id]["feedback_text"] = feedback_text            "message": f"Usage statistics reset for user {user_id}",

                    "timestamp": datetime.now()

        return {        }

            "message": "Feedback recorded successfully",        

            "conversation_id": conversation_id,    except Exception as e:

            "rating": rating        logger.error(f"Error resetting usage for user {user_id}: {str(e)}")

        }        raise HTTPException(

                    status_code=500,

    except HTTPException:            detail=f"Failed to reset usage statistics: {str(e)}"

        raise        )

    except Exception as e:

        logger.error(f"Error recording feedback: {str(e)}")@router.get("/usage/stats/summary")

        raise HTTPException(status_code=500, detail=str(e))async def get_global_usage_summary():

    """

@router.get("/usage/trends")    Get global usage summary across all users (admin function)

async def get_usage_trends(    """

    days: int = 7,    try:

    current_user: Optional[dict] = Depends(get_optional_user)        logger.info("Getting global usage summary")

):        

    """        summary = await logger_service.get_global_usage_summary()

    Get usage trends over time        

    """        return {

    try:            "timestamp": datetime.now(),

        # Mock trend data (in production, query from database)            "summary": summary

        end_date = datetime.now()        }

        start_date = end_date - timedelta(days=days)        

            except Exception as e:

        trends = {        logger.error(f"Error getting global usage summary: {str(e)}")

            "period": {        raise HTTPException(

                "start_date": start_date.isoformat(),            status_code=500,

                "end_date": end_date.isoformat(),            detail=f"Failed to retrieve global usage summary: {str(e)}"

                "days": days        )
            },
            "daily_stats": [
                {
                    "date": (start_date + timedelta(days=i)).isoformat()[:10],
                    "conversations": max(0, 10 + i * 2),
                    "questions": max(0, 25 + i * 5),
                    "avg_response_time_ms": 1500 + (i * 100)
                }
                for i in range(days)
            ],
            "top_topics": most_common_topics[:10] if 'most_common_topics' in locals() else [],
            "user_satisfaction_trend": [4.2, 4.3, 4.1, 4.4, 4.5, 4.3, 4.6][-days:]
        }
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting usage trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to update statistics (called from other parts of the application)
def update_conversation_stats(conversation_id: str, data: Dict[str, Any]):
    """Update conversation statistics"""
    if conversation_id not in conversation_data:
        conversation_data[conversation_id] = {
            "start_time": datetime.now(),
            "question_count": 0,
            "topics": [],
            "status": "ongoing"
        }
        usage_statistics["total_conversations"] += 1
    
    conversation_data[conversation_id].update(data)
    
    if "response_time_ms" in data:
        usage_statistics["response_times"].append(data["response_time_ms"])
    
    if "topic" in data:
        topic = data["topic"]
        if topic not in usage_statistics["topics"]:
            usage_statistics["topics"][topic] = 0
        usage_statistics["topics"][topic] += 1
    
    if "question" in data:
        usage_statistics["total_questions"] += 1
        conversation_data[conversation_id]["question_count"] += 1