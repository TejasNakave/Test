"""
Proactive ChatBot Features - Makes chatbot more intelligent and helpful like ChatGPT
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re
from collections import Counter
import aiosqlite
from ..config import settings
from .logger import LoggerService
import logging

logger = logging.getLogger(__name__)

class ProactiveService:
    """Service to make chatbot proactive like ChatGPT"""
    
    def __init__(self, logger_service: LoggerService):
        self.logger = logger_service
    
    async def analyze_user_behavior_patterns(self, user_id: str) -> Dict[str, Any]:
        """✅ Analyze user behavior patterns for proactive suggestions"""
        try:
            # Get user's last 30 days of interactions
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Get detailed conversation history
            conversations = []
            async with aiosqlite.connect(self.logger.db_path) as db:
                async with db.execute("""
                    SELECT question, answer, timestamp, conversation_id, response_time_ms
                    FROM interactions 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (user_id, thirty_days_ago.isoformat())) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        conversations.append({
                            "question": row[0],
                            "answer": row[1], 
                            "timestamp": row[2],
                            "conversation_id": row[3],
                            "response_time": row[4] or 1000
                        })
            
            # Analyze patterns
            patterns = await self._analyze_conversation_patterns(conversations)
            
            return {
                "user_id": user_id,
                "total_conversations": len(conversations),
                "frequent_topics": patterns["topics"][:5],
                "question_types": patterns["question_types"],
                "preferred_complexity": patterns["complexity"],
                "activity_times": patterns["activity_times"],
                "stuck_indicators": patterns["stuck_indicators"],
                "engagement_level": patterns["engagement_level"]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user patterns: {str(e)}")
            return {
                "user_id": user_id,
                "total_conversations": 0,
                "frequent_topics": [],
                "question_types": {},
                "preferred_complexity": "medium",
                "activity_times": {"peak_hours": [], "pattern": "unknown"},
                "stuck_indicators": {"is_stuck": False, "repeated_questions": 0},
                "engagement_level": "medium",
                "error": str(e)
            }
    
    async def _analyze_conversation_patterns(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Internal method to analyze conversation patterns"""
        
        if not conversations:
            return {
                "topics": [],
                "question_types": {},
                "complexity": "medium",
                "activity_times": {"peak_hours": [], "pattern": "unknown"},
                "stuck_indicators": {"is_stuck": False, "repeated_questions": 0},
                "engagement_level": "low"
            }
        
        # Extract topics from questions
        all_questions = " ".join([c["question"].lower() for c in conversations])
        
        # Simple topic extraction (filtering common words)
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this', 'it', 'from', 'be', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'should', 'will', 'do', 'does', 'did', 'have', 'has', 'had', 'me', 'my', 'i', 'you', 'your', 'he', 'his', 'she', 'her', 'we', 'our', 'they', 'their'}
        topic_keywords = [word for word in re.findall(r'\b\w{4,}\b', all_questions) if word not in stop_words]
        topic_counter = Counter(topic_keywords)
        
        # Analyze question types
        question_types = {
            "what": len([q for q in conversations if q["question"].lower().startswith("what")]),
            "how": len([q for q in conversations if q["question"].lower().startswith("how")]),
            "why": len([q for q in conversations if q["question"].lower().startswith("why")]),
            "explain": len([q for q in conversations if "explain" in q["question"].lower()]),
            "help": len([q for q in conversations if "help" in q["question"].lower()])
        }
        
        # Analyze complexity (based on question length and response time)
        avg_question_length = sum(len(c["question"]) for c in conversations) / len(conversations)
        avg_response_time = sum(c["response_time"] for c in conversations) / len(conversations)
        
        if avg_question_length < 30:
            complexity = "simple"
        elif avg_question_length > 80:
            complexity = "complex"
        else:
            complexity = "medium"
        
        # Check for stuck indicators (repeated similar questions)
        stuck_indicators = self._detect_stuck_patterns(conversations)
        
        # Activity time analysis
        activity_times = self._analyze_activity_times(conversations)
        
        # Engagement level
        if len(conversations) > 20:
            engagement = "high"
        elif len(conversations) > 5:
            engagement = "medium"
        else:
            engagement = "low"
        
        return {
            "topics": [word for word, count in topic_counter.most_common(10) if count > 1],
            "question_types": question_types,
            "complexity": complexity,
            "activity_times": activity_times,
            "stuck_indicators": stuck_indicators,
            "engagement_level": engagement
        }
    
    def _detect_stuck_patterns(self, conversations: List[Dict]) -> Dict[str, Any]:
        """✅ Help detection when user seems stuck"""
        
        stuck_patterns = {
            "repeated_questions": 0,
            "help_requests": 0,
            "clarification_requests": 0,
            "is_stuck": False
        }
        
        if len(conversations) < 3:
            return stuck_patterns
        
        # Check for repeated similar questions
        recent_questions = [c["question"].lower() for c in conversations[:5]]
        for i, question in enumerate(recent_questions):
            question_words = set(question.split())
            for j, other_question in enumerate(recent_questions[i+1:], i+1):
                other_words = set(other_question.split())
                # Simple similarity check
                common_words = question_words & other_words
                if len(common_words) >= 3 and len(common_words) / max(len(question_words), len(other_words)) > 0.5:
                    stuck_patterns["repeated_questions"] += 1
        
        # Check for help/clarification requests
        help_keywords = ["help", "clarify", "explain better", "don't understand", "confused", "unclear", "what do you mean"]
        for conversation in conversations[:10]:  # Check recent conversations
            question_lower = conversation["question"].lower()
            for keyword in help_keywords:
                if keyword in question_lower:
                    stuck_patterns["help_requests"] += 1
                    break
        
        # Check for clarification requests
        clarification_keywords = ["can you", "could you", "please explain", "i need", "show me"]
        for conversation in conversations[:10]:
            question_lower = conversation["question"].lower()
            for keyword in clarification_keywords:
                if keyword in question_lower:
                    stuck_patterns["clarification_requests"] += 1
                    break
        
        # Determine if user is stuck
        stuck_patterns["is_stuck"] = (
            stuck_patterns["repeated_questions"] >= 2 or
            stuck_patterns["help_requests"] >= 3 or
            stuck_patterns["clarification_requests"] >= 4
        )
        
        return stuck_patterns
    
    def _analyze_activity_times(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze when user is most active"""
        hours = []
        for conv in conversations:
            try:
                # Handle different timestamp formats
                timestamp_str = conv["timestamp"]
                if isinstance(timestamp_str, str):
                    # Try to parse ISO format first
                    if 'T' in timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    continue
                hours.append(dt.hour)
            except Exception as e:
                logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
                continue
        
        if not hours:
            return {"peak_hours": [], "pattern": "unknown"}
        
        hour_counter = Counter(hours)
        peak_hours = [hour for hour, count in hour_counter.most_common(3)]
        
        # Determine pattern
        if any(9 <= hour <= 17 for hour in peak_hours):
            pattern = "business_hours"
        elif any(18 <= hour <= 23 for hour in peak_hours):
            pattern = "evening"
        elif any(0 <= hour <= 8 for hour in peak_hours):
            pattern = "early_morning"
        else:
            pattern = "varied"
        
        return {"peak_hours": peak_hours, "pattern": pattern}
    
    async def generate_proactive_suggestions(
        self, 
        user_id: str, 
        current_context: str = "",
        conversation_id: Optional[str] = None
    ) -> List[str]:
        """✅ Proactive suggestions based on user behavior"""
        
        # Get user behavior patterns
        patterns = await self.analyze_user_behavior_patterns(user_id)
        
        suggestions = []
        
        # Personalized suggestions based on patterns
        if patterns.get("frequent_topics"):
            top_topics = patterns["frequent_topics"][:2]
            for topic in top_topics:
                if topic:
                    suggestions.append(f"🔄 Want to explore more about {topic}?")
        
        # Based on question types preference
        question_types = patterns.get("question_types", {})
        max_type = max(question_types.items(), key=lambda x: x[1], default=("what", 0))[0] if question_types else "what"
        
        if max_type == "how":
            suggestions.append("⚙️ I can walk you through step-by-step processes")
        elif max_type == "what":
            suggestions.append("📚 I can explain concepts and definitions clearly")
        elif max_type == "why":
            suggestions.append("🤔 I can help you understand the reasoning behind things")
        elif max_type == "explain":
            suggestions.append("📖 I can break down complex topics into simple parts")
        
        # Activity-based suggestions
        activity_pattern = patterns.get("activity_times", {}).get("pattern")
        if activity_pattern == "business_hours":
            suggestions.append("💼 Need help with work-related tasks or analysis?")
        elif activity_pattern == "evening":
            suggestions.append("🌙 Working on personal projects or learning something new?")
        elif activity_pattern == "early_morning":
            suggestions.append("☀️ Starting your day with some research or planning?")
        
        # Engagement-based suggestions
        engagement = patterns.get("engagement_level")
        if engagement == "high":
            suggestions.append("🚀 Ready to tackle a challenging topic today?")
        elif engagement == "medium":
            suggestions.append("💡 What would you like to learn about today?")
        else:
            suggestions.append("👋 I'm here to help with any questions you have!")
        
        # Base suggestions if we need more
        base_suggestions = [
            "💡 What would you like to explore today?",
            "📚 I can help explain complex topics simply",
            "🔍 Need help analyzing or researching something?",
            "🎯 Want assistance with problem-solving?",
            "📊 I can help with data analysis or document review"
        ]
        
        # Add base suggestions if we don't have enough personalized ones
        for base in base_suggestions:
            if len(suggestions) >= 4:
                break
            if base not in suggestions:
                suggestions.append(base)
        
        return suggestions[:4]  # Return top 4
    
    async def generate_context_aware_followups(
        self, 
        question: str, 
        answer: str, 
        conversation_id: Optional[str] = None
    ) -> List[str]:
        """✅ Context-aware follow-up questions"""
        
        followups = []
        
        # Get conversation history for context
        history = []
        if conversation_id:
            try:
                history = await self.logger.get_conversation_history(conversation_id)
            except Exception as e:
                logger.warning(f"Failed to get conversation history: {e}")
                history = []
        
        # Analyze current Q&A for follow-up opportunities
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Question-type based follow-ups
        if question_lower.startswith(("what is", "what are", "what does")):
            followups.append("📝 Would you like to see examples or use cases?")
            followups.append("🔍 Want to know how this relates to other concepts?")
        elif question_lower.startswith(("how to", "how do", "how can")):
            followups.append("⚡ Need help with any specific steps?")
            followups.append("🛠️ Want to see alternative approaches?")
        elif "explain" in question_lower or "describe" in question_lower:
            followups.append("🤔 Any part you'd like me to clarify further?")
            followups.append("📊 Would a diagram or example help?")
        elif question_lower.startswith("why"):
            followups.append("🔍 Want to explore the underlying reasons?")
            followups.append("📈 Interested in seeing the broader implications?")
        
        # Content-based follow-ups
        if any(word in answer_lower for word in ["code", "programming", "python", "javascript", "software"]):
            followups.append("💻 Want to see this implemented differently?")
            followups.append("🐛 Need help debugging or testing this?")
        
        if any(word in answer_lower for word in ["data", "analysis", "statistics", "chart"]):
            followups.append("📈 Want to explore the data further?")
            followups.append("🎯 Need help interpreting the results?")
        
        if any(word in answer_lower for word in ["process", "method", "approach", "strategy"]):
            followups.append("🔄 Want to see this process in action?")
            followups.append("⚡ Need help implementing this approach?")
        
        # Conversation flow based follow-ups
        if len(history) > 1:
            followups.append("🔄 How does this connect to what we discussed earlier?")
        
        if len(history) > 5:
            followups.append("📋 Want me to summarize our discussion so far?")
        
        # Generic helpful follow-ups
        fallback_followups = [
            "❓ Any questions about what I just explained?",
            "🚀 Want to dive deeper into any specific aspect?",
            "💡 Shall we explore related topics?",
            "🎯 Need help applying this information?"
        ]
        
        # Add fallbacks if we don't have enough specific followups
        for fallback in fallback_followups:
            if len(followups) >= 3:
                break
            if fallback not in followups:
                followups.append(fallback)
        
        return followups[:3]  # Return top 3
    
    async def manage_conversation_flow(
        self, 
        user_id: str, 
        conversation_id: str,
        current_question: str
    ) -> Dict[str, Any]:
        """✅ Conversation flow management"""
        
        # Get conversation history
        try:
            history = await self.logger.get_conversation_history(conversation_id)
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            history = []
        
        # Analyze conversation flow
        flow_analysis = {
            "conversation_length": len(history),
            "topic_changes": 0,
            "user_engagement": "medium",
            "suggested_actions": [],
            "conversation_health": "good",
            "flow_stage": "continuing"
        }
        
        if len(history) == 0:
            # First interaction
            flow_analysis["flow_stage"] = "starting"
            flow_analysis["suggested_actions"].append("👋 Welcome! I'm here to help with any questions.")
            return flow_analysis
        
        # Detect topic changes
        if len(history) >= 2:
            try:
                prev_question = history[-1]["question"].lower()
                current_lower = current_question.lower()
                
                # Simple topic change detection
                prev_words = set(prev_question.split())
                current_words = set(current_lower.split())
                common_words = prev_words & current_words
                
                if len(common_words) < 2 or len(common_words) / max(len(prev_words), len(current_words)) < 0.3:
                    flow_analysis["topic_changes"] += 1
                    flow_analysis["suggested_actions"].append("🔄 I see we're exploring a new topic!")
            except Exception as e:
                logger.warning(f"Failed to analyze topic changes: {e}")
        
        # Long conversation management
        if len(history) > 15:
            flow_analysis["flow_stage"] = "extended"
            flow_analysis["suggested_actions"].append("📋 Would you like me to summarize what we've covered?")
        elif len(history) > 8:
            flow_analysis["flow_stage"] = "deep"
            flow_analysis["suggested_actions"].append("🎯 We've covered a lot - any specific area you want to focus on?")
        
        # Engagement analysis based on conversation patterns
        try:
            if len(history) >= 3:
                recent_questions = [h["question"] for h in history[-3:]]
                avg_length = sum(len(q) for q in recent_questions) / len(recent_questions)
                
                if avg_length < 20:
                    flow_analysis["user_engagement"] = "decreasing"
                    flow_analysis["suggested_actions"].append("🤔 Would you like more detailed explanations?")
                elif avg_length > 100:
                    flow_analysis["user_engagement"] = "high"
                    flow_analysis["suggested_actions"].append("🚀 Great detailed questions! Keep them coming.")
        except Exception as e:
            logger.warning(f"Failed to analyze engagement: {e}")
        
        # Check for stuck patterns
        try:
            patterns = await self.analyze_user_behavior_patterns(user_id)
            if patterns.get("stuck_indicators", {}).get("is_stuck", False):
                flow_analysis["conversation_health"] = "user_might_be_stuck"
                flow_analysis["suggested_actions"].append("🤝 Would you like me to approach this differently?")
                flow_analysis["suggested_actions"].append("💡 I can break this down into simpler steps")
        except Exception as e:
            logger.warning(f"Failed to check stuck patterns: {e}")
        
        return flow_analysis
    
    async def should_offer_proactive_help(
        self, 
        user_id: str, 
        conversation_id: str,
        current_question: str
    ) -> Dict[str, Any]:
        """Determine if and what kind of proactive help to offer"""
        
        try:
            # Analyze user patterns
            patterns = await self.analyze_user_behavior_patterns(user_id)
            
            # Manage conversation flow
            flow = await self.manage_conversation_flow(user_id, conversation_id, current_question)
            
            # Generate suggestions
            suggestions = await self.generate_proactive_suggestions(user_id, current_question, conversation_id)
            
            # Determine help type
            help_type = "guidance"
            if "help" in current_question.lower() or "explain" in current_question.lower():
                help_type = "clarification"
            elif patterns.get("stuck_indicators", {}).get("is_stuck", False):
                help_type = "unstuck"
            
            return {
                "should_offer_help": patterns.get("stuck_indicators", {}).get("is_stuck", False),
                "help_type": help_type,
                "proactive_suggestions": suggestions,
                "conversation_flow": flow,
                "user_patterns": patterns,
                "confidence": "high" if patterns.get("total_conversations", 0) > 5 else "medium"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze proactive help needs: {e}")
            return {
                "should_offer_help": False,
                "help_type": "guidance",
                "proactive_suggestions": [
                    "💡 What would you like to explore today?",
                    "📚 I can help explain topics clearly",
                    "🎯 Need assistance with anything specific?"
                ],
                "conversation_flow": {"conversation_health": "good", "suggested_actions": []},
                "user_patterns": {"engagement_level": "medium"},
                "confidence": "low",
                "error": str(e)
            }