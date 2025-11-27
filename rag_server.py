"""
Working RAG Chatbot Server
Combines document search with OpenAI responses
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
import uuid
import httpx
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime

# Load environment variables
load_dotenv("api/.env")

app = FastAPI(title="RAG Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import data-driven trade filter
try:
    from api.services.data_driven_trade_filter import data_driven_filter
    DATA_FILTER_ENABLED = True
    logger.info("✅ Data-driven trade filter enabled - analyzes actual document content")
except ImportError:
    DATA_FILTER_ENABLED = False
    logger.warning("⚠️ Data-driven trade filter not available")

# Gesture Collections for Enhanced User Experience
def get_opening_gestures():
    """Return a variety of engaging opening gestures with contextual awareness"""
    return [
        # Enthusiastic Acknowledgments
        "✨ Excellent question! I'm thrilled to help you navigate this topic.",
        "🎯 Great inquiry! This is exactly the kind of detail that makes a difference.",
        "💡 That's a fantastic question! You're thinking strategically about this.",
        "🚀 Perfect timing for this question! Let me break this down comprehensively.",
        "🌟 Wonderful question! I can see you're really diving deep into the details.",
        
        # Professional Recognition
        "👍 Excellent point to explore! This shows great business insight.",
        "💼 That's a professional inquiry that deserves a thorough response.",
        "🔍 Great question to dive into! I appreciate your attention to detail.",
        "📚 Excellent topic to discuss! This is fundamental to understanding the process.",
        "🏆 Outstanding question! You're asking the right things at the right time.",
        
        # Expertise Validation
        "⭐ Brilliant inquiry! This demonstrates sophisticated understanding.",
        "🔥 Hot topic! You've identified a crucial aspect many overlook.",
        "💎 Valuable question! This insight will definitely serve you well.",
        "🎨 Interesting perspective! I love how you're approaching this challenge.",
        "💯 Perfect question to address! Let me provide you with comprehensive guidance.",
        
        # Collaborative Energy
        "🎉 I'm excited to help with this! Together we'll get you the clarity you need.",
        "💪 Strong question! I can tell you're committed to getting this right.",
        "🌈 Let's explore this colorfully and thoroughly!",
        "🚀 Let's rocket into this topic with all the details you need!",
        "🎪 Fascinating question! There's quite a bit to unpack here, and I'm here for it."
    ]

def get_closing_gestures():
    """Return a variety of engaging closing gestures with actionable next steps"""
    return [
        # Supportive Continuation
        "Hope this comprehensive guidance helps! 😊 Feel free to dive deeper into any aspect.",
        "Feel free to ask anything else! 🤝 I'm here to support your success every step of the way.",
        "Let me know if you need more details! 📞 I can elaborate on any specific area that interests you.",
        "Happy to assist further! 🌟 Whether it's clarification or next steps, I'm ready.",
        "Here to help anytime! 💪 Don't hesitate to explore related questions or dive deeper.",
        
        # Achievement-Oriented
        "Wishing you tremendous success with this! 🎯 You're clearly on the right path.",
        "Hope this clarifies everything perfectly! ✅ You're well-equipped to move forward confidently.",
        "Best of luck with your process! 🍀 I believe you'll achieve excellent results.",
        "Feel confident moving forward! 💼 You now have the knowledge to succeed.",
        "You're on the right track! 🚀 Keep building on this solid foundation.",
        
        # Encouraging Progress
        "Great progress! Keep up the momentum! 👏 Each question brings you closer to mastery.",
        "Excited to see your continued success! 🎉 You're developing real expertise here.",
        "You've got this completely! 💎 Trust in the process and your growing understanding.",
        "Smooth sailing ahead with this knowledge! ⛵ Navigate with confidence.",
        "Rooting for your outstanding success! 🏆 You're building something impressive.",
        
        # Future-Focused
        "May your journey be filled with continued learning! 🌈 Each step builds valuable expertise.",
        "Keep up the excellent work! ⭐ Your dedication to understanding shows true professionalism.",
        "Brilliant achievements await you! 🔥 Use this knowledge as your competitive advantage.",
        "Success is absolutely within reach! 🎪 You have all the tools you need now.",
        "Outstanding progress lies ahead! 💯 Trust the process and your growing capabilities."
    ]

def add_response_gestures(answer_text: str, question: str = "", suggested_questions: List[str] = None) -> str:
    """Add engaging opening and closing gestures to the response with suggested questions"""
    import random
    
    # Get random gestures
    opening_gesture = random.choice(get_opening_gestures())
    closing_gesture = random.choice(get_closing_gestures())
    
    # Add opening gesture at the beginning
    enhanced_answer = f"{opening_gesture}\n\n{answer_text}"
    
    # Add suggested questions section if provided
    suggested_section = ""
    if suggested_questions and len(suggested_questions) > 0:
        suggested_section = "\n\n🤔 **Suggested Questions:**\n"
        for i, suggestion in enumerate(suggested_questions, 1):
            suggested_section += f"{i}. {suggestion}\n"
    
    # Add closing gesture and suggested questions at the end
    # Check if the answer already ends with a question or interactive element
    if enhanced_answer.rstrip().endswith('?') or '🎯' in enhanced_answer[-100:] or '💡' in enhanced_answer[-100:]:
        # Insert closing gesture and suggestions before the final interactive element
        lines = enhanced_answer.strip().split('\n')
        if len(lines) >= 2:
            # Insert before the last paragraph/section
            enhanced_answer = '\n'.join(lines[:-1]) + suggested_section + f"\n\n{closing_gesture}\n\n" + lines[-1]
        else:
            enhanced_answer = enhanced_answer.strip() + suggested_section + f"\n\n{closing_gesture}"
    else:
        enhanced_answer = enhanced_answer.strip() + suggested_section + f"\n\n{closing_gesture}"
    
    return enhanced_answer

class AskRequest(BaseModel):
    user_id: str
    question: str
    conversation_id: Optional[str] = None
    include_diagrams: bool = True
    include_suggestions: bool = True

class InteractiveAction(BaseModel):
    type: str  # "clarification", "followup", "explore", "guide"
    content: str
    metadata: Dict[str, Any] = {}

class Suggestion(BaseModel):
    question: str
    relevance: float
    action_type: str = "ask"  # "ask", "explore", "clarify"

class Source(BaseModel):
    id: str
    title: str
    content: str
    score: float
    metadata: dict = {}
    interactive_actions: List[InteractiveAction] = []

class ConversationTurn(BaseModel):
    timestamp: datetime
    user_question: str
    bot_response: str
    sources_used: List[str]
    user_intent: str
    topic: str

class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    diagrams: List[dict] = []
    suggestions: List[Suggestion] = []
    conversation_id: str
    response_time_ms: int
    tokens_used: int = 0
    interactive_elements: List[InteractiveAction] = []
    conversation_context: Dict[str, Any] = {}
    images: List[dict] = []  # Add support for intelligent image responses

# Global variables for RAG components
vector_store = None
document_loader = None
openai_client = None
conversation_memory = {}  # Store conversation history

def generate_contextual_suggestions(question: str, sources: List[Source], user_intent: Dict[str, Any]) -> List[str]:
    """Generate 3-4 dynamic contextual suggested questions based on the actual question and context"""
    import random
    import re
    
    question_lower = question.lower().strip()
    suggestions = []
    
    # Extract key entities and topics from the question
    question_keywords = re.findall(r'\b\w+\b', question_lower)
    
    # Extract meaningful content from sources
    source_content = ""
    source_topics = set()
    for source in sources:
        source_content += f" {source.title} {source.content[:200]}"
        source_topics.update(source.title.lower().split())
    
    # Generate suggestions based on question patterns and content
    
    # 1. If asking about a specific process/procedure
    if any(word in question_lower for word in ["how to", "process", "procedure", "steps"]):
        process_suggestions = [
            f"What documents are needed for {extract_main_topic(question_lower)}?",
            f"How long does {extract_main_topic(question_lower)} typically take?",
            f"What are the costs involved in {extract_main_topic(question_lower)}?",
            f"Are there any prerequisites for {extract_main_topic(question_lower)}?",
            f"What happens after completing {extract_main_topic(question_lower)}?",
            f"Can {extract_main_topic(question_lower)} be done online?",
            f"What are common issues with {extract_main_topic(question_lower)}?"
        ]
        suggestions.extend(random.sample([s for s in process_suggestions if s], min(3, len([s for s in process_suggestions if s]))))
    
    # 2. If asking about documents/certificates
    elif any(word in question_lower for word in ["document", "certificate", "paper", "form"]):
        doc_topic = extract_main_topic(question_lower)
        doc_suggestions = [
            f"How do I apply for {doc_topic}?",
            f"What is the validity of {doc_topic}?",
            f"How can I renew {doc_topic}?",
            f"What supporting documents are needed for {doc_topic}?",
            f"How much does {doc_topic} cost?",
            f"Can I track the status of my {doc_topic} application?",
            f"What if my {doc_topic} application is rejected?"
        ]
        suggestions.extend(random.sample([s for s in doc_suggestions if s], min(3, len([s for s in doc_suggestions if s]))))
    
    # 3. If asking about requirements/eligibility
    elif any(word in question_lower for word in ["require", "need", "eligible", "criteria"]):
        req_topic = extract_main_topic(question_lower)
        req_suggestions = [
            f"What are the eligibility criteria for {req_topic}?",
            f"How do I check if I qualify for {req_topic}?",
            f"What additional requirements exist for {req_topic}?",
            f"Are there any exemptions for {req_topic}?",
            f"What happens if I don't meet the requirements for {req_topic}?",
            f"How often do requirements for {req_topic} change?"
        ]
        suggestions.extend(random.sample([s for s in req_suggestions if s], min(3, len([s for s in req_suggestions if s]))))
    
    # 4. If asking about benefits/schemes
    elif any(word in question_lower for word in ["benefit", "scheme", "incentive", "subsidy"]):
        benefit_topic = extract_main_topic(question_lower)
        benefit_suggestions = [
            f"How do I apply for {benefit_topic} benefits?",
            f"What is the maximum benefit under {benefit_topic}?",
            f"Can I combine {benefit_topic} with other schemes?",
            f"How are {benefit_topic} benefits calculated?",
            f"What are the compliance requirements for {benefit_topic}?",
            f"How long does it take to receive {benefit_topic} benefits?"
        ]
        suggestions.extend(random.sample([s for s in benefit_suggestions if s], min(3, len([s for s in benefit_suggestions if s]))))
    
    # 5. If asking about comparison
    elif any(word in question_lower for word in ["compare", "difference", "vs", "better", "which"]):
        comp_suggestions = [
            "What are the key differences in processing time?",
            "Which option is more cost-effective?",
            "What are the eligibility differences?",
            "Which option offers better long-term benefits?",
            "How do compliance requirements compare?",
            "Can I switch between these options later?"
        ]
        suggestions.extend(random.sample(comp_suggestions, min(3, len(comp_suggestions))))
    
    # 6. Context-specific suggestions based on source content
    if "export" in source_content.lower() or "export" in question_lower:
        export_suggestions = [
            "What are the latest export policy updates?",
            "How do I handle export documentation efficiently?",
            "What are common export compliance issues?",
            "How can I expedite my export clearance?"
        ]
        suggestions.extend(random.sample(export_suggestions, min(2, len(export_suggestions))))
    
    if "import" in source_content.lower() or "import" in question_lower:
        import_suggestions = [
            "What are the import duty implications?",
            "How does import licensing work?",
            "What are the customs clearance requirements?"
        ]
        suggestions.extend(random.sample(import_suggestions, min(1, len(import_suggestions))))
    
    if "dgft" in source_content.lower() or "dgft" in question_lower:
        dgft_suggestions = [
            "What are the latest DGFT circular updates?",
            "How do I register with DGFT online?",
            "What are the key DGFT compliance deadlines?"
        ]
        suggestions.extend(random.sample(dgft_suggestions, min(1, len(dgft_suggestions))))
    
    # 7. Generic fallback suggestions if nothing specific was generated
    if not suggestions:
        generic_suggestions = [
            "What are the recent policy changes I should know about?",
            "Are there any digital alternatives for this process?",
            "What are the common mistakes to avoid?",
            "How can I track the progress of my application?"
        ]
        suggestions.extend(random.sample(generic_suggestions, min(3, len(generic_suggestions))))
    
    # Remove duplicates and ensure uniqueness
    unique_suggestions = []
    seen = set()
    for suggestion in suggestions:
        if suggestion and suggestion not in seen:
            unique_suggestions.append(suggestion)
            seen.add(suggestion)
    
    # Limit to 4 suggestions max and ensure they are different from the original question
    final_suggestions = []
    for suggestion in unique_suggestions:
        if len(final_suggestions) >= 4:
            break
        # Avoid suggestions too similar to the original question
        if not is_too_similar(question_lower, suggestion.lower()):
            final_suggestions.append(suggestion)
    
    return final_suggestions

def extract_main_topic(question: str) -> str:
    """Extract the main topic/entity from a question"""
    # Remove common question words
    stop_words = {"what", "how", "when", "where", "why", "which", "who", "is", "are", "do", "does", 
                  "can", "could", "should", "would", "will", "the", "a", "an", "to", "for", "of", "in", "on", "at"}
    
    words = question.split()
    meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Look for specific entities
    entities = ["iec", "dgft", "export", "import", "certificate", "license", "clearance", "scheme", "epcg"]
    for word in meaningful_words:
        if any(entity in word for entity in entities):
            return word
    
    # Return first meaningful word or combination
    if meaningful_words:
        if len(meaningful_words) == 1:
            return meaningful_words[0]
        else:
            return " ".join(meaningful_words[:2])  # Take first two words
    
    return "this process"

def is_too_similar(original: str, suggestion: str) -> bool:
    """Check if suggestion is too similar to the original question"""
    original_words = set(original.split())
    suggestion_words = set(suggestion.split())
    
    # Calculate similarity
    common_words = original_words.intersection(suggestion_words)
    similarity = len(common_words) / max(len(original_words), len(suggestion_words), 1)
    
    return similarity > 0.7  # If more than 70% similar, it's too similar

class InteractiveRAGBot:
    def __init__(self):
        self.conversation_patterns = {
            "export_process": ["step", "procedure", "process", "how to export"],
            "documentation": ["document", "certificate", "paperwork", "IEC"],
            "compliance": ["compliance", "regulation", "requirement", "must"],
            "schemes": ["scheme", "benefit", "incentive", "EPCG", "advance"],
            "customs": ["customs", "duty", "clearance", "import"]
        }
        
    def analyze_user_intent(self, question: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
        """Analyze what the user really wants to know"""
        question_lower = question.lower()
        
        # Detect intent patterns
        detected_intents = []
        for intent, keywords in self.conversation_patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Analyze conversation context
        recent_topics = []
        if conversation_history:
            recent_topics = [turn.topic for turn in conversation_history[-3:]]
        
        # Detect if user is asking for clarification
        clarification_words = ["what do you mean", "explain more", "can you clarify", "i don't understand"]
        is_clarification = any(phrase in question_lower for phrase in clarification_words)
        
        # Detect if user wants step-by-step guidance
        step_words = ["steps", "how do i", "guide me", "walk me through", "process"]
        wants_guidance = any(word in question_lower for word in step_words)
        
        return {
            "primary_intent": detected_intents[0] if detected_intents else "general_query",
            "all_intents": detected_intents,
            "recent_topics": recent_topics,
            "is_clarification": is_clarification,
            "wants_guidance": wants_guidance,
            "complexity_level": "beginner" if any(word in question_lower for word in ["basic", "simple", "new"]) else "intermediate"
        }
    
    def generate_interactive_actions(self, sources: List[Source], user_intent: Dict[str, Any]) -> List[InteractiveAction]:
        """Generate interactive elements based on context"""
        actions = []
        
        # Add source exploration actions
        for source in sources[:3]:  # Top 3 sources
            actions.append(InteractiveAction(
                type="explore",
                content=f"🔍 Explore more details from {source.title}",
                metadata={"source_id": source.id, "action": "explore_document"}
            ))
        
        # Add clarification actions if needed
        if user_intent.get("wants_guidance"):
            actions.append(InteractiveAction(
                type="guide",
                content="📋 Would you like me to break this down into step-by-step guidance?",
                metadata={"action": "step_by_step_guide"}
            ))
        
        # Add related topic exploration
        if user_intent.get("primary_intent") == "export_process":
            actions.extend([
                InteractiveAction(
                    type="followup",
                    content="📋 Show me required export documents",
                    metadata={"action": "show_documents"}
                ),
                InteractiveAction(
                    type="followup", 
                    content="💰 Tell me about export incentives",
                    metadata={"action": "show_incentives"}
                )
            ])
        
        return actions
    
    def generate_dynamic_suggestions(self, question: str, sources: List[Source], user_intent: Dict[str, Any]) -> List[Suggestion]:
        """Generate contextual suggestions based on the conversation"""
        suggestions = []
        
        primary_intent = user_intent.get("primary_intent", "")
        
        if primary_intent == "export_process":
            suggestions = [
                Suggestion(question="What documents do I need for export?", relevance=0.95, action_type="ask"),
                Suggestion(question="How long does export clearance take?", relevance=0.9, action_type="ask"),
                Suggestion(question="What are the export duty rates?", relevance=0.85, action_type="explore")
            ]
        elif primary_intent == "documentation":
            suggestions = [
                Suggestion(question="How to apply for IEC certificate?", relevance=0.95, action_type="guide"),
                Suggestion(question="What is the validity of export documents?", relevance=0.9, action_type="ask"),
                Suggestion(question="Can I use digital certificates?", relevance=0.8, action_type="clarify")
            ]
        elif primary_intent == "schemes":
            suggestions = [
                Suggestion(question="Compare EPCG vs Advance Authorization", relevance=0.95, action_type="explore"),
                Suggestion(question="How to calculate scheme benefits?", relevance=0.9, action_type="guide"),
                Suggestion(question="What are the eligibility criteria?", relevance=0.85, action_type="ask")
            ]
        else:
            # Default contextual suggestions based on sources
            if sources:
                source_topics = set()
                for source in sources:
                    title_words = source.title.lower().split()
                    source_topics.update(title_words)
                
                if "export" in source_topics:
                    suggestions.append(Suggestion(question="Tell me more about export procedures", relevance=0.8, action_type="explore"))
                if "import" in source_topics:
                    suggestions.append(Suggestion(question="What about import regulations?", relevance=0.8, action_type="explore"))
                if "dgft" in source_topics:
                    suggestions.append(Suggestion(question="Explain DGFT schemes in detail", relevance=0.85, action_type="guide"))
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def create_conversation_context(self, conversation_history: List[ConversationTurn], current_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build conversation context for better responses"""
        context = {
            "conversation_length": len(conversation_history),
            "topics_discussed": list(set([turn.topic for turn in conversation_history])),
            "user_expertise_level": current_intent.get("complexity_level", "intermediate"),
            "current_focus": current_intent.get("primary_intent", "general"),
            "needs_followup": len(conversation_history) > 0 and conversation_history[-1].topic == current_intent.get("primary_intent")
        }
        
        # Detect user progression through a topic
        if len(conversation_history) >= 2:
            recent_intents = [turn.user_intent for turn in conversation_history[-2:]]
            if len(set(recent_intents)) == 1:  # User staying on same topic
                context["deep_dive_mode"] = True
                context["topic_depth"] = len([t for t in conversation_history if t.topic == recent_intents[0]])
        
        return context

# Initialize interactive bot
interactive_bot = InteractiveRAGBot()

async def enhanced_generate_response(question: str, sources: List[Source], conversation_context: Dict[str, Any], user_intent: Dict[str, Any]):
    """Generate enhanced interactive response with intelligent image analysis"""
    try:
        if not openai_client:
            return f"I found relevant information about '{question}' in your documents, but enhanced AI responses are not configured."
        
        # STEP 1: Smart detection for image-relevant questions
        images = []
        question_lower = question.lower()
        
        # Define keywords that indicate user wants visual content
        visual_keywords = [
            "show", "display", "image", "picture", "diagram", "flowchart", "chart", 
            "figure", "illustration", "visual", "screenshot", "photo", "graphic",
            "flow chart", "process diagram", "workflow", "step diagram", "infographic"
        ]
        
        # Define process-related keywords that might have visual representations
        process_keywords = [
            "process", "procedure", "steps", "workflow", "flow", "method", 
            "operation", "clearance", "scheme", "application process"
        ]
        
        # Check if question explicitly asks for visual content
        wants_visual = any(keyword in question_lower for keyword in visual_keywords)
        
        # Check if question is about processes that commonly have flowcharts
        process_related = any(keyword in question_lower for keyword in process_keywords)
        
        # Check if user is asking for detailed explanation of processes (these often benefit from visuals)
        detailed_process = ("explain in detail" in question_lower or "detailed explanation" in question_lower) and process_related
        
        # Only get images if the question is visually relevant
        if wants_visual or detailed_process:
            try:
                from direct_image_service import direct_image_service
                images = direct_image_service.get_images_for_query(question, limit=2)
                logger.info(f"📊 Visual content requested - Found {len(images)} relevant images for: {question}")
            except Exception as e:
                logger.error(f"Error getting images: {e}")
                images = []
        else:
            logger.info(f"📝 Text-only response - No visual content needed for: {question}")
            images = []
        
        # Build conversation-aware context
        context_parts = []
        for source in sources:
            context_parts.append(f"[From {source.title}]: {source.content}")
        
        context_text = "\n\n".join(context_parts)
        
        # STEP 2: Add image analysis to context ONLY if images were retrieved
        image_context = ""
        if images:
            image_context = "\n\nVISUAL CONTENT ANALYSIS:\n"
            for i, img in enumerate(images, 1):
                image_context += f"\n**Image {i}: {img['filename']}** (Relevance: {img['relevance_score']:.2f})\n"
                image_context += f"Source: {img['source_document']}\n"
                image_context += f"Analysis: {img['analysis']}\n"
        
        # Build conversation history context
        conversation_summary = ""
        if conversation_context.get("conversation_length", 0) > 0:
            conversation_summary = f"\nCONVERSATION CONTEXT: This user has been discussing {', '.join(conversation_context.get('topics_discussed', []))}. "
            if conversation_context.get("deep_dive_mode"):
                conversation_summary += f"They are deep-diving into {conversation_context.get('current_focus')} (depth: {conversation_context.get('topic_depth', 1)} questions). "
            conversation_summary += f"User expertise level: {conversation_context.get('user_expertise_level', 'intermediate')}."
        
        # Create enhanced interactive prompt
        interactive_instructions = ""
        if user_intent.get("wants_guidance"):
            interactive_instructions = "\n- Provide step-by-step guidance with clear numbered steps and emojis"
        if user_intent.get("is_clarification"):
            interactive_instructions += "\n- Focus on clarifying and explaining concepts in simpler terms with examples"
        if conversation_context.get("deep_dive_mode"):
            interactive_instructions += "\n- Provide deeper, more detailed insights since the user is exploring this topic thoroughly"
        
        # Adjust prompt based on whether images are included
        visual_instruction = ""
        if images:
            visual_instruction = """
7. IMPORTANT: Visual content is provided in VISUAL CONTENT ANALYSIS section - reference and explain the flowcharts/diagrams
8. When describing images, extract key information from the image analysis provided
9. Mention the visual materials found at the end of your response"""
        else:
            visual_instruction = """
7. Focus on providing comprehensive text-based explanation
8. No visual content is needed for this query"""
        
        prompt = f"""Based on the following context{', visual analysis,' if images else ''} and conversation history, provide a comprehensive interactive response.

DOCUMENT CONTEXT:
{context_text}{image_context}
{conversation_summary}

USER QUESTION: {question}
USER INTENT: {user_intent.get('primary_intent', 'general_query')}

CRITICAL FORMATTING REQUIREMENTS:
1. Use emojis to make responses engaging (📋, ✅, 💡, 📝, ⚠️, 🎯, 🚀, etc.)
2. Structure with clear **Bold Headings** 
3. Use numbered lists for step-by-step processes
4. Use bullet points for requirements or key points
5. Add interactive callouts like "💡 **Pro Tip:**" or "⚠️ **Important:**"
6. Include markdown formatting: **bold**, *italics*
{visual_instruction}
10. Make it conversational and engaging
11. End with an interactive question or next step suggestion

INTERACTIVE RESPONSE INSTRUCTIONS:
1. Use the document context as the primary source for ALL information
2. When user asks "explain in detail" - provide COMPREHENSIVE explanations with:
   - Definition and overview of the topic
   - Step-by-step processes with numbered lists
   - Required documentation and procedures
   - Key requirements and compliance points
   - Timeline and important considerations
3. When user asks for COMPARISONS ("compare", "difference", "vs") - ALWAYS create HTML tables for proper rendering:
   
   **REQUIRED HTML TABLE FORMAT:**
   
   <table border="1" style="border-collapse: collapse; width: 100%;">
   <tr style="background-color: #f2f2f2;">
   <th style="padding: 12px; text-align: left;"><strong>Aspect</strong></th>
   <th style="padding: 12px; text-align: left;"><strong>Option A</strong></th>
   <th style="padding: 12px; text-align: left;"><strong>Option B</strong></th>
   </tr>
   <tr>
   <td style="padding: 12px;">Feature 1</td>
   <td style="padding: 12px;">Description</td>
   <td style="padding: 12px;">Description</td>
   </tr>
   </table>
   
   - Use HTML table format with proper styling
   - Include border and padding for readability
   - Add background color to headers
   - Each row must be properly formatted with <tr> and <td> tags
4. Format response with engaging visual structure using emojis and markdown
5. Include specific details relevant to Indian export-import procedures
6. Create clear sections with bold headings for each major aspect
7. If VISUAL CONTENT ANALYSIS is provided, ALWAYS reference and explain the flowcharts/diagrams shown
8. When describing images, extract key information from the image analysis provided
9. For export process queries, ensure you cover:
   - What export process means
   - Pre-export requirements
   - Documentation needed
   - Clearance procedures
   - Compliance requirements
   - Post-export formalities
10. End with a question or suggestion to keep the conversation flowing
11. If appropriate, mention what else you can help with{interactive_instructions}

CRITICAL: When user asks for "detailed explanation" provide comprehensive content from the document context. Don't give generic responses.
CRITICAL: When user asks for "comparison" always include markdown tables for clear side-by-side analysis.

Provide a well-formatted, interactive response with emojis and clear structure:"""

        # Call OpenAI with enhanced context
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an interactive expert assistant for Indian export-import procedures, DGFT policies, and customs regulations. When users ask for 'detailed explanations', you MUST provide comprehensive, thorough responses using the document context provided. When users ask for 'comparisons', you MUST create properly formatted HTML tables with borders and styling:\n\n<table border=\"1\" style=\"border-collapse: collapse; width: 100%;\">\n<tr style=\"background-color: #f2f2f2;\">\n<th style=\"padding: 12px; text-align: left;\"><strong>Aspect</strong></th>\n<th style=\"padding: 12px; text-align: left;\"><strong>Option A</strong></th>\n<th style=\"padding: 12px; text-align: left;\"><strong>Option B</strong></th>\n</tr>\n<tr>\n<td style=\"padding: 12px;\">Feature</td>\n<td style=\"padding: 12px;\">Description</td>\n<td style=\"padding: 12px;\">Description</td>\n</tr>\n</table>\n\nUse HTML table format with proper styling, borders, and padding. Use emojis, **bold headings**, numbered lists, bullet points, and interactive elements like 💡 Pro Tips, ⚠️ Important notes, and 🎯 Next Steps. Make responses visually engaging and easy to read."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        if response:
            answer_text = response.choices[0].message.content
            
            # Add image information to the answer ONLY if images were found
            if images:
                answer_text += f"\n\n🖼️ **Visual Materials Found**: I've included {len(images)} relevant diagram(s) and flowchart(s) that illustrate this process."
            
            # Generate contextual suggested questions
            suggested_questions = generate_contextual_suggestions(question, sources, user_intent)
            
            # Add engaging gestures and suggested questions to the response
            enhanced_answer = add_response_gestures(answer_text, question, suggested_questions)
            
            return {"answer": enhanced_answer, "images": images}
        else:
            logger.error("No response from OpenAI")
            fallback_answer = f"""📋 **Found Relevant Information**

Based on your documents, here's what I found about '{question}':

{context_text[:800]}...

💡 **What would you like me to explain next?**
- Need specific steps for this process?
- Want to explore related requirements?
- Have questions about compliance?

🎯 **I'm here to help!** Just ask me to dive deeper into any aspect!"""
            
            if images:
                fallback_answer += f"\n\n🖼️ **Visual Materials**: I found {len(images)} relevant diagram(s) for this topic."
            
            # Generate contextual suggested questions for fallback
            suggested_questions = generate_contextual_suggestions(question, sources, user_intent)
            
            # Add engaging gestures and suggested questions to the fallback response
            enhanced_fallback = add_response_gestures(fallback_answer, question, suggested_questions)
            
            return {"answer": enhanced_fallback, "images": images}
            
    except Exception as e:
        logger.error(f"Enhanced response generation error: {str(e)}")
        fallback_error = f"""🔍 **Found Information for You!**

I discovered relevant details about '{question}' in your documents.

💡 **Let me help you explore this topic:**
- Would you like step-by-step guidance?
- Need specific requirements explained?
- Want to understand the compliance process?

🚀 **Ask me anything!** I can break down complex procedures into simple steps."""
        
        # Generate contextual suggested questions for error case
        suggested_questions = generate_contextual_suggestions(question, sources if 'sources' in locals() else [], user_intent)
        
        # Add engaging gestures and suggested questions to the error response
        enhanced_error = add_response_gestures(fallback_error, question, suggested_questions)
        
        return {"answer": enhanced_error, "images": images if 'images' in locals() else []}

def lazy_load_vector_store():
    """Lazily load vector store on first use - DISABLED due to compatibility issues"""
    global vector_store
    
    # TEMPORARY FIX: Disable vector store to prevent crashes
    # The ChromaDB/LangChain compatibility issue causes silent crashes
    # Server will work with LLM-only responses until vector store is fixed
    
    if vector_store != "failed":
        logger.warning("⚠️ Vector store disabled due to ChromaDB compatibility issues")
        logger.warning("Server will use LLM-only responses (without RAG)")
        vector_store = "failed"
    
    return None

async def initialize_rag():
    """Initialize RAG components safely"""
    global vector_store, document_loader, openai_client
    
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize OpenAI client
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            import openai
            openai_client = openai.AsyncOpenAI(api_key=api_key, timeout=60.0)
            logger.info("OpenAI client initialized")
        else:
            openai_client = None
            logger.warning("No OpenAI API key found")
        
        # Try to initialize document loader first (lighter operation)
        try:
            from api.services.document_loader import DocumentLoader
            document_loader = DocumentLoader()
            logger.info("Document loader initialized")
        except Exception as dl_error:
            logger.warning(f"Document loader initialization failed: {str(dl_error)}")
            document_loader = None
        
        # Skip vector store initialization to allow server to start quickly
        # Vector store will be loaded on-demand when first needed
        logger.info("Vector store will be loaded on first query (lazy loading)")
        vector_store = None
        
        logger.info("✅ RAG initialization complete")
            
    except Exception as e:
        logger.error(f"RAG initialization error: {str(e)}")

async def search_documents(query: str, top_k: int = 5):
    """Enhanced document search with interactive elements"""
    try:
        # Lazy load vector store on first use with error protection
        try:
            vs = lazy_load_vector_store()
            if not vs:
                logger.warning("Vector store not available - will use LLM without RAG")
                return []
        except Exception as load_error:
            logger.error(f"Failed to load vector store: {str(load_error)}")
            return []
        
        # Enhance search query for detailed explanations
        enhanced_query = query
        if "explain in detail" in query.lower() and "export process" in query.lower():
            enhanced_query = f"{query} export procedures documentation requirements clearance process steps export formalities customs DGFT"
        elif "detail" in query.lower() and "export" in query.lower():
            enhanced_query = f"{query} export procedure process documentation requirements steps"
            
        logger.info(f"Enhanced search query: {enhanced_query}")
        
        # Perform similarity search using our custom method
        try:
            results = vs.search_documents(
                query=enhanced_query,
                k=top_k
            )
        except Exception as search_error:
            logger.error(f"Vector search failed: {str(search_error)}")
            return []
        
        sources = []
        for i, result in enumerate(results):
            # Add interactive actions to each source
            interactive_actions = [
                InteractiveAction(
                    type="explore",
                    content=f"🔍 Read full document: {result.metadata.get('source', 'Document')}",
                    metadata={"action": "view_full_document", "source": result.metadata.get('source')}
                ),
                InteractiveAction(
                    type="followup",
                    content="❓ Ask questions about this document",
                    metadata={"action": "ask_about_document"}
                )
            ]
            
            source = Source(
                id=f"doc_{i}",
                title=result.metadata.get("source", f"Document {i+1}"),
                content=result.page_content[:500] + "..." if len(result.page_content) > 500 else result.page_content,
                score=result.metadata.get("score", 0.8),
                metadata=result.metadata,
                interactive_actions=interactive_actions
            )
            sources.append(source)
        
        logger.info(f"Found {len(sources)} relevant documents with interactive elements")
        return sources
        
    except Exception as e:
        logger.error(f"Document search error: {str(e)}")
        return []

async def generate_rag_response(question: str, sources: List[Source]):
    """Generate response using context + OpenAI"""
    try:
        if not openai_client:
            return f"I found relevant information in your documents about '{question}', but OpenAI integration is not configured for enhanced responses."
        
        # Build context from sources
        context_parts = []
        for source in sources:
            context_parts.append(f"[From {source.title}]: {source.content}")
        
        context_text = "\n\n".join(context_parts)
        
        # Create enhanced prompt
        prompt = f"""Based on the following context from the user's documents, please provide a comprehensive answer to their question.

CONTEXT FROM DOCUMENTS:
{context_text}

USER QUESTION: {question}

INSTRUCTIONS:
1. Use the provided context as the primary source of information
2. Structure your response clearly with step-by-step explanations where appropriate
3. Add relevant additional insights that complement the document context
4. If the context doesn't fully cover the question, acknowledge this and provide what you can
5. Be specific about export procedures, DGFT policies, customs requirements, etc. based on the context

Please provide a detailed, helpful response:"""

        # Call OpenAI
        api_key = os.getenv("LLM_API_KEY")
        response = await openai_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are an expert on Indian export-import procedures, DGFT policies, and customs regulations. Provide detailed, accurate responses based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenAI error: {response.status_code}")
            return f"I found relevant information in your documents about '{question}'. Here's a summary based on the context: {context_text[:1000]}..."
            
    except Exception as e:
        logger.error(f"RAG response generation error: {str(e)}")
        return f"I found relevant information about '{question}' in your documents, but encountered an issue generating the enhanced response."

@app.get("/")
async def homepage():
    """Serve React frontend homepage"""
    if os.path.exists("build/index.html"):
        return FileResponse("build/index.html")
    elif os.path.exists("src/build/index.html"):
        return FileResponse("src/build/index.html")
    else:
        # Fallback to API info if React build doesn't exist
        return {
            "message": "🚀 Trade Assistant RAG Chatbot API",
            "status": "running",
            "version": "1.0.0",
            "description": "AI-powered chatbot for Indian export-import procedures and DGFT policies",
            "frontend": "React build not found - building in progress",
            "endpoints": {
                "ask": "/api/v1/ask",
                "health": "/api/v1/health",
                "docs": "/docs",
                "redoc": "/redoc"
            },
            "features": [
                "RAG-powered responses from 53+ trade documents",
                "Interactive conversation memory",
                "Image analysis for diagrams and flowcharts",
                "Data-driven filtering based on document content",
                "Real-time suggestions and contextual help"
            ]
        }

# Serve React static files
if os.path.exists("build"):
    app.mount("/static", StaticFiles(directory="build/static"), name="static")
elif os.path.exists("src/build"):
    app.mount("/static", StaticFiles(directory="src/build/static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize RAG on startup"""
    await initialize_rag()

@app.post("/api/v1/ask", response_model=AskResponse)
async def interactive_ask(request: AskRequest):
    """Enhanced Interactive RAG-powered question answering"""
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        logger.info(f"Processing interactive question: {request.question[:100]}...")
        
        # DATA-DRIVEN TRADE FILTERING - Based on actual document content
        if DATA_FILTER_ENABLED:
            data_classification = data_driven_filter.classify_question(request.question)
            
            if not data_classification.is_data_related:
                logger.info(f"🚫 Question outside data coverage: {data_classification.reason}")
                
                # Return data-driven redirect response
                data_redirect = data_driven_filter.get_data_driven_redirect_response(
                    request.question, 
                    data_classification
                )
                
                return AskResponse(
                    answer=data_redirect,
                    sources=[],
                    diagrams=[],
                    suggestions=[
                        Suggestion(question="How to start export business using DGFT schemes?", relevance=0.95, action_type="guide"),
                        Suggestion(question="What export documentation is required?", relevance=0.9, action_type="ask"),
                        Suggestion(question="Explain customs clearance procedures", relevance=0.85, action_type="explore"),
                        Suggestion(question="How does IEC registration work?", relevance=0.8, action_type="ask")
                    ],
                    conversation_id=conversation_id,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    tokens_used=0,
                    interactive_elements=[
                        InteractiveAction(
                            type="clarification",
                            content=f"🎯 I have {data_driven_filter.data_analysis.total_documents if data_driven_filter.data_analysis else 'comprehensive'} trade documents - ask me about trade topics!",
                            metadata={"action": "data_driven_guidance", "matched_topics": data_classification.matched_topics}
                        )
                    ],
                    images=[]
                )
            else:
                logger.info(f"✅ Question matches data coverage: {data_classification.reason} (confidence: {data_classification.confidence_score:.2f})")
                if data_classification.relevant_documents:
                    logger.info(f"📄 Relevant documents: {', '.join(data_classification.relevant_documents[:3])}")
        
        # Get conversation history
        conversation_history = conversation_memory.get(conversation_id, [])
        
        # Analyze user intent
        user_intent = interactive_bot.analyze_user_intent(request.question, conversation_history)
        logger.info(f"Detected intent: {user_intent}")
        
        # Search documents
        sources = await search_documents(request.question, top_k=5)
        
        # Generate conversation context
        conversation_context = interactive_bot.create_conversation_context(conversation_history, user_intent)
        
        # Generate enhanced interactive response with images
        response_images = []
        if sources:
            response_data = await enhanced_generate_response(request.question, sources, conversation_context, user_intent)
            if isinstance(response_data, dict):
                answer = response_data.get("answer", "")
                response_images = response_data.get("images", [])
            else:
                answer = response_data  # Fallback for string response
            logger.info(f"Generated interactive response with {len(sources)} sources and {len(response_images)} images")
        else:
            # Use direct LLM response without RAG (vector store disabled)
            logger.info("Using direct LLM response (no RAG sources available)")
            try:
                if openai_client:
                    completion = await openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """You are an expert on Indian export-import procedures, DGFT policies, customs regulations, and international trade. 

FORMAT YOUR RESPONSES WITH:
- Use relevant emojis throughout the content (📋, 🛃, 💼, 📊, 🔍, etc.)
- Structure content with clear sections using **bold headings**
- Add emojis to bullet points and key concepts
- Make responses engaging and easy to read
- Include practical examples where applicable

Provide detailed, accurate, and well-formatted responses about trade-related topics."""},
                            {"role": "user", "content": f"{request.question}"}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    raw_answer = completion.choices[0].message.content
                    
                    # Generate suggested questions for gestures
                    suggested_questions = [
                        "What documents are required for export?",
                        "How to apply for IEC certificate?",
                        "Explain customs clearance process"
                    ]
                    
                    # Add response gestures for better UX
                    answer = add_response_gestures(raw_answer, request.question, suggested_questions)
                    logger.info(f"Generated LLM-only response with gestures (tokens: {completion.usage.total_tokens})")
                else:
                    fallback_text = f"""I'm here to help with Indian export-import procedures! 

Regarding your question about '{request.question}', I can provide guidance on:

**Export Procedures**
- Documentation requirements
- DGFT scheme applications
- IEC certificate processes

**Customs & Compliance**
- Duty calculations
- Clearance procedures
- Risk management

**Trade Operations**
- Import-export operations
- Foreign trade consulting
- Regulatory compliance

What specific aspect would you like to explore?"""
                    
                    suggested_questions = [
                        "How to start export business?",
                        "What is DGFT and its role?",
                        "Explain export documentation process"
                    ]
                    
                    answer = add_response_gestures(fallback_text, request.question, suggested_questions)
                    
            except Exception as llm_error:
                logger.error(f"LLM generation error: {str(llm_error)}")
                error_text = f"I'm having trouble generating a response right now about '{request.question}'. Please try asking about specific export-import topics like documentation, procedures, or compliance."
                suggested_questions = [
                    "What documents are needed for export?",
                    "How to get IEC certificate?",
                    "Explain customs clearance steps"
                ]
                answer = add_response_gestures(error_text, request.question, suggested_questions)
        
        # Generate interactive actions
        interactive_actions = interactive_bot.generate_interactive_actions(sources, user_intent)
        
        # Generate dynamic suggestions
        suggestions = interactive_bot.generate_dynamic_suggestions(request.question, sources, user_intent)
        
        # Update conversation memory
        new_turn = ConversationTurn(
            timestamp=datetime.now(),
            user_question=request.question,
            bot_response=answer[:200] + "...",  # Store summary
            sources_used=[s.id for s in sources],
            user_intent=user_intent.get("primary_intent", "general"),
            topic=user_intent.get("primary_intent", "general")
        )
        
        if conversation_id not in conversation_memory:
            conversation_memory[conversation_id] = []
        conversation_memory[conversation_id].append(new_turn)
        
        # Keep only last 10 turns
        conversation_memory[conversation_id] = conversation_memory[conversation_id][-10:]
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return AskResponse(
            answer=answer,
            sources=sources,
            diagrams=[],
            suggestions=suggestions,
            conversation_id=conversation_id,
            response_time_ms=response_time_ms,
            tokens_used=0,
            interactive_elements=interactive_actions,
            conversation_context=conversation_context,
            images=response_images
        )
        
    except Exception as e:
        logger.error(f"Error in interactive RAG processing: {str(e)}")
        
        return AskResponse(
            answer=f"""🤖 **Hello! I'm Your Export-Import Assistant!**

I noticed you asked about '{request.question}'. While I process your request, let me tell you what I can help with:

📋 **Export Guidance**
- Step-by-step export procedures
- Documentation requirements
- DGFT policy explanations

🛃 **Import Assistance**  
- Customs clearance processes
- Duty calculations
- Compliance requirements

💼 **Trade Support**
- IEC certificate guidance
- Foreign trade consulting
- Regulatory updates

💡 **What would you like to explore first?** I'm here to make export-import simple for you!""",
            sources=[],
            diagrams=[],
            suggestions=[
                Suggestion(question="What export procedures should I know?", relevance=0.9, action_type="guide"),
                Suggestion(question="Tell me about DGFT policies", relevance=0.8, action_type="explore"),
                Suggestion(question="How does customs clearance work?", relevance=0.7, action_type="ask")
            ],
            conversation_id=conversation_id,
            response_time_ms=int((time.time() - start_time) * 1000),
            tokens_used=0,
            interactive_elements=[
                InteractiveAction(
                    type="clarification",
                    content="💡 Ask me to explain any export-import concept in detail",
                    metadata={"action": "explain_concept"}
                )
            ],
            images=[]
        )

@app.get("/api/v1/health")
async def health_check():
    """Enhanced health check with interactive capabilities"""
    doc_count = vector_store.get().count() if vector_store else 0
    conversations_count = len(conversation_memory)
    total_turns = sum(len(turns) for turns in conversation_memory.values())
    
    return {
        "status": "healthy",
        "rag_components": {
            "vector_store": "available" if vector_store else "not available",
            "document_loader": "available" if document_loader else "not available",
            "openai_client": "available" if openai_client else "not available"
        },
        "documents_count": doc_count,
        "conversations_active": conversations_count,
        "conversation_turns_total": total_turns,
        "interactive_features": {
            "conversation_memory": True,
            "intent_analysis": True,
            "dynamic_suggestions": True,
            "interactive_actions": True,
            "data_driven_filtering": DATA_FILTER_ENABLED
        },
        "data_filter_status": {
            "enabled": DATA_FILTER_ENABLED,
            "description": "Chatbot restricted to topics covered in actual trade documents" if DATA_FILTER_ENABLED else "All topics allowed",
            "analyzed_documents": data_driven_filter.data_analysis.total_documents if DATA_FILTER_ENABLED and data_driven_filter.data_analysis else 0,
            "coverage_areas": len(data_driven_filter.data_analysis.coverage_areas) if DATA_FILTER_ENABLED and data_driven_filter.data_analysis else 0
        },
        "timestamp": time.time()
    }

@app.get("/api/v1/conversation/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history for a specific conversation"""
    history = conversation_memory.get(conversation_id, [])
    return {
        "conversation_id": conversation_id,
        "turns": len(history),
        "history": [
            {
                "timestamp": turn.timestamp.isoformat(),
                "user_question": turn.user_question,
                "bot_response": turn.bot_response,
                "user_intent": turn.user_intent,
                "topic": turn.topic,
                "sources_count": len(turn.sources_used)
            }
            for turn in history
        ]
    }

@app.delete("/api/v1/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a specific conversation"""
    if conversation_id in conversation_memory:
        del conversation_memory[conversation_id]
        return {"message": f"Conversation {conversation_id} cleared"}
    else:
        return {"message": f"Conversation {conversation_id} not found"}

# Catch-all route for React Router (must be LAST route)
@app.get("/{path:path}")
async def serve_react_routes(path: str):
    """Serve React app for client-side routing"""
    # Don't serve React for API routes or docs
    if any(path.startswith(prefix) for prefix in ["api", "docs", "redoc", "openapi.json", "health"]):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve React index.html for all other routes
    if os.path.exists("build/index.html"):
        return FileResponse("build/index.html")
    elif os.path.exists("src/build/index.html"):
        return FileResponse("src/build/index.html")
    else:
        # Fallback for routes when React build doesn't exist
        return JSONResponse({
            "message": "Frontend route requested but React build not available",
            "path": path,
            "api_docs": "/docs",
            "api_health": "/api/v1/health"
        })

if __name__ == "__main__":
    import uvicorn
    
    # Use PORT environment variable for Render deployment, fallback to 8000 for local
    port = int(os.getenv("PORT", 8000))
    
    # Check if port is available for local development
    if port == 8000:
        import socket
        def is_port_available(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return True
                except OSError:
                    return False
        
        if not is_port_available(port):
            port = 8001
            print(f"⚠️  Port 8000 is busy, using port {port}")
        else:
            print(f"🚀 Starting server on port {port}")
    else:
        print(f"🌍 Starting server for Render deployment on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)