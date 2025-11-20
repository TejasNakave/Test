"""
Complex Ask Router - Advanced RAG functionality with enhanced features
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List, Dict, Any
import time
import uuid
import logging
import asyncio

from api.schemas import (
    AskRequest, AskResponse, Source, Suggestion, InteractiveAction,
    ConversationTurn, Diagram
)
from api.auth import get_optional_user
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["advanced_chat"])

# In-memory conversation storage (use database in production)
conversation_memory: Dict[str, List[ConversationTurn]] = {}

@router.post("/ask/advanced", response_model=AskResponse)
async def advanced_ask_question(
    request: AskRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Advanced RAG-powered question answering with enhanced features
    """
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        logger.info(f"Processing advanced question from user {request.user_id}: {request.question[:100]}...")
        
        # Get conversation history
        conversation_history = conversation_memory.get(conversation_id, [])
        
        # Analyze user intent (mock implementation)
        user_intent = await analyze_user_intent(request.question, conversation_history)
        
        # Perform document search (mock implementation)
        sources = await search_documents(request.question, top_k=settings.TOP_K_RESULTS)
        
        # Generate enhanced response
        answer = await generate_enhanced_response(
            request.question, 
            sources, 
            conversation_history,
            user_intent
        )
        
        # Generate interactive elements
        interactive_elements = generate_interactive_actions(sources, user_intent)
        
        # Generate contextual suggestions
        suggestions = generate_contextual_suggestions(
            request.question, 
            sources, 
            user_intent,
            conversation_history
        )
        
        # Generate diagrams if requested
        diagrams = []
        if request.include_diagrams:
            diagrams = await generate_diagrams(request.question, sources)
        
        # Update conversation memory
        conversation_turn = ConversationTurn(
            timestamp=datetime.now(),
            user_question=request.question,
            bot_response=answer[:200] + "..." if len(answer) > 200 else answer,
            sources_used=[s.id for s in sources],
            user_intent=user_intent.get("primary_intent", "general"),
            topic=user_intent.get("topic", "general")
        )
        
        if conversation_id not in conversation_memory:
            conversation_memory[conversation_id] = []
        conversation_memory[conversation_id].append(conversation_turn)
        
        # Keep only last 10 turns
        conversation_memory[conversation_id] = conversation_memory[conversation_id][-10:]
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Background task to update analytics
        background_tasks.add_task(
            update_analytics,
            conversation_id,
            request.user_id,
            user_intent,
            response_time_ms
        )
        
        return AskResponse(
            answer=answer,
            sources=sources,
            diagrams=diagrams,
            suggestions=suggestions,
            conversation_id=conversation_id,
            response_time_ms=response_time_ms,
            tokens_used=estimate_tokens(answer),
            user_intent=user_intent.get("primary_intent"),
            confidence_score=user_intent.get("confidence", 0.5),
            interactive_elements=interactive_elements,
            conversation_context={
                "conversation_length": len(conversation_history),
                "topics_discussed": list(set([turn.topic for turn in conversation_history])),
                "user_expertise_level": user_intent.get("expertise_level", "intermediate")
            }
        )
        
    except Exception as e:
        logger.error(f"Error in advanced question processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get detailed conversation context and history
    """
    try:
        if conversation_id not in conversation_memory:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation_history = conversation_memory[conversation_id]
        
        # Analyze conversation patterns
        topics = [turn.topic for turn in conversation_history]
        intents = [turn.user_intent for turn in conversation_history]
        
        context = {
            "conversation_id": conversation_id,
            "total_turns": len(conversation_history),
            "topics_discussed": list(set(topics)),
            "most_common_topic": max(set(topics), key=topics.count) if topics else None,
            "user_intents": list(set(intents)),
            "conversation_flow": [
                {
                    "turn": i + 1,
                    "timestamp": turn.timestamp.isoformat(),
                    "topic": turn.topic,
                    "intent": turn.user_intent,
                    "question_preview": turn.user_question[:100] + "..." if len(turn.user_question) > 100 else turn.user_question
                }
                for i, turn in enumerate(conversation_history)
            ],
            "expertise_progression": analyze_expertise_progression(conversation_history),
            "suggested_next_topics": suggest_next_topics(topics, intents)
        }
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Clear conversation history
    """
    try:
        if conversation_id in conversation_memory:
            del conversation_memory[conversation_id]
            return {"message": f"Conversation {conversation_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def analyze_user_intent(question: str, history: List[ConversationTurn]) -> Dict[str, Any]:
    """Analyze user intent from question and conversation history"""
    # Mock intent analysis
    intent_keywords = {
        "export_process": ["export", "procedure", "process", "how to export"],
        "documentation": ["document", "certificate", "paperwork", "IEC"],
        "compliance": ["compliance", "regulation", "requirement", "legal"],
        "schemes": ["scheme", "benefit", "incentive", "EPCG", "advance"],
        "customs": ["customs", "duty", "clearance", "import"]
    }
    
    question_lower = question.lower()
    detected_intents = []
    
    for intent, keywords in intent_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            detected_intents.append(intent)
    
    return {
        "primary_intent": detected_intents[0] if detected_intents else "general",
        "all_intents": detected_intents,
        "confidence": 0.8 if detected_intents else 0.3,
        "topic": detected_intents[0] if detected_intents else "general",
        "expertise_level": "intermediate"  # Could be inferred from history
    }

async def search_documents(query: str, top_k: int = 5) -> List[Source]:
    """Mock document search function"""
    # In production, this would use actual vector search
    mock_sources = [
        Source(
            id=f"doc_{i}",
            title=f"Export Document {i}",
            content=f"Relevant content for '{query}' from document {i}...",
            score=0.9 - (i * 0.1),
            metadata={"source": f"document_{i}.docx", "page": i + 1}
        )
        for i in range(min(top_k, 3))
    ]
    
    return mock_sources

async def generate_enhanced_response(
    question: str,
    sources: List[Source],
    history: List[ConversationTurn],
    intent: Dict[str, Any]
) -> str:
    """Generate enhanced response using context"""
    # Mock enhanced response generation
    context_info = ""
    if history:
        recent_topics = [turn.topic for turn in history[-3:]]
        context_info = f" (Building on our discussion about {', '.join(set(recent_topics))})"
    
    primary_intent = intent.get("primary_intent", "general")
    
    response = f"Based on your question about '{question}' and the {len(sources)} relevant documents I found{context_info}, here's a comprehensive answer focusing on {primary_intent}:\n\n"
    
    if sources:
        response += f"According to {sources[0].title}, "
    
    response += "This is a detailed response that would be generated using RAG techniques, combining the retrieved documents with AI-generated explanations."
    
    return response

def generate_interactive_actions(sources: List[Source], intent: Dict[str, Any]) -> List[InteractiveAction]:
    """Generate interactive actions based on sources and intent"""
    actions = []
    
    if sources:
        actions.append(InteractiveAction(
            type="explore",
            content=f"📖 Explore more from {sources[0].title}",
            metadata={"source_id": sources[0].id, "action": "view_source"}
        ))
    
    primary_intent = intent.get("primary_intent", "general")
    if primary_intent == "export_process":
        actions.append(InteractiveAction(
            type="guide",
            content="🎯 Get step-by-step export guidance",
            metadata={"action": "step_by_step_guide", "topic": "export"}
        ))
    
    actions.append(InteractiveAction(
        type="clarification",
        content="💡 Ask for more specific details",
        metadata={"action": "clarify", "suggestion": "Can you be more specific about which aspect interests you?"}
    ))
    
    return actions

def generate_contextual_suggestions(
    question: str,
    sources: List[Source],
    intent: Dict[str, Any],
    history: List[ConversationTurn]
) -> List[Suggestion]:
    """Generate contextual suggestions based on conversation context"""
    primary_intent = intent.get("primary_intent", "general")
    
    suggestions_map = {
        "export_process": [
            Suggestion(question="What documents are needed for export?", relevance=0.9, action_type="ask"),
            Suggestion(question="How to obtain IEC certificate?", relevance=0.8, action_type="explore"),
            Suggestion(question="Export procedure timeline", relevance=0.7, action_type="guide")
        ],
        "documentation": [
            Suggestion(question="IEC certificate requirements", relevance=0.9, action_type="guide"),
            Suggestion(question="Export house certificate process", relevance=0.8, action_type="ask"),
            Suggestion(question="Document verification procedures", relevance=0.7, action_type="explore")
        ],
        "schemes": [
            Suggestion(question="EPCG scheme benefits", relevance=0.9, action_type="explore"),
            Suggestion(question="Advance authorization eligibility", relevance=0.8, action_type="ask"),
            Suggestion(question="Compare different DGFT schemes", relevance=0.7, action_type="guide")
        ]
    }
    
    return suggestions_map.get(primary_intent, [
        Suggestion(question="How to start exporting?", relevance=0.8, action_type="guide"),
        Suggestion(question="Import procedures", relevance=0.7, action_type="ask"),
        Suggestion(question="Customs regulations", relevance=0.6, action_type="explore")
    ])

async def generate_diagrams(question: str, sources: List[Source]) -> List[Diagram]:
    """Generate relevant diagrams based on question and sources"""
    # Mock diagram generation
    if "process" in question.lower() or "procedure" in question.lower():
        return [
            Diagram(
                id="flow_1",
                title="Export Process Flowchart",
                description="Step-by-step export procedure visualization",
                diagram_type="flowchart",
                metadata={"generated_for": question}
            )
        ]
    return []

def estimate_tokens(text: str) -> int:
    """Estimate token count for text"""
    return len(text.split()) * 1.3  # Rough estimation

def analyze_expertise_progression(history: List[ConversationTurn]) -> Dict[str, Any]:
    """Analyze how user expertise has progressed"""
    if len(history) < 2:
        return {"level": "beginner", "progression": "insufficient_data"}
    
    # Simple mock analysis
    question_complexity = [len(turn.user_question.split()) for turn in history]
    avg_complexity = sum(question_complexity) / len(question_complexity)
    
    if avg_complexity > 15:
        return {"level": "advanced", "progression": "increasing"}
    elif avg_complexity > 10:
        return {"level": "intermediate", "progression": "steady"}
    else:
        return {"level": "beginner", "progression": "learning"}

def suggest_next_topics(topics: List[str], intents: List[str]) -> List[str]:
    """Suggest next topics based on conversation history"""
    topic_flow = {
        "export_process": ["documentation", "schemes", "compliance"],
        "documentation": ["export_process", "compliance"],
        "schemes": ["compliance", "customs"],
        "customs": ["schemes", "compliance"]
    }
    
    recent_topics = list(set(topics[-3:]))  # Last 3 unique topics
    suggestions = []
    
    for topic in recent_topics:
        suggestions.extend(topic_flow.get(topic, []))
    
    return list(set(suggestions))[:3]

async def update_analytics(
    conversation_id: str,
    user_id: str,
    intent: Dict[str, Any],
    response_time_ms: int
):
    """Background task to update analytics"""
    # This would update analytics database in production
    logger.info(f"Analytics updated for conversation {conversation_id}: intent={intent.get('primary_intent')}, response_time={response_time_ms}ms")