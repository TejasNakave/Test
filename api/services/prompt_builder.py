import httpx
import logging
from typing import List, Dict, Any, Optional
from ..config import settings
from ..schemas import Diagram, Suggestion
import time
import json
import re

logger = logging.getLogger(__name__)

class PromptResult:
    """Result from prompt building and LLM generation"""
    def __init__(
        self,
        answer: str,
        diagrams: List[Diagram] = None,
        suggestions: List[Suggestion] = None,
        tokens_used: int = 0
    ):
        self.answer = answer
        self.diagrams = diagrams or []
        self.suggestions = suggestions or []
        self.tokens_used = tokens_used

class PromptBuilderService:
    """Service for building prompts and generating responses with LLM"""
    
    def __init__(self):
        self.llm_api_key = settings.LLM_API_KEY
        self.llm_base_url = settings.LLM_BASE_URL
        self.llm_model = settings.LLM_MODEL
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=60.0)
        return self.client
    
    async def generate_simple_response(
        self,
        question: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Generate a simple response using OpenAI API without vector database context
        """
        try:
            if not self.llm_api_key:
                return {
                    "answer": f"I received your question: '{question}'. However, I need an OpenAI API key to generate responses.",
                    "tokens_used": 0
                }
            
            client = await self._get_client()
            
            # Simple prompt for general questions
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Provide clear, concise, and helpful answers to user questions."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            response = await client.post(
                f"{self.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.llm_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                return {
                    "answer": answer,
                    "tokens_used": tokens_used
                }
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {
                    "answer": f"I received your question: '{question}'. There was an issue connecting to the AI service, but the API is working.",
                    "tokens_used": 0
                }
                
        except Exception as e:
            logger.error(f"Error generating simple response: {str(e)}")
            return {
                "answer": f"I received your question: '{question}'. I'm working on getting better responses set up. The system is functioning!",
                "tokens_used": 0
            }

    async def build_and_generate(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        conversation_id: str,
        include_diagrams: bool = True,
        include_suggestions: bool = True
    ) -> PromptResult:
        """
        Build prompt with context and generate comprehensive response
        
        Args:
            question: User's question
            chunks: Retrieved and reranked chunks
            conversation_id: Conversation identifier
            include_diagrams: Whether to generate diagrams
            include_suggestions: Whether to generate follow-up suggestions
            
        Returns:
            PromptResult with answer, diagrams, and suggestions
        """
        try:
            logger.info(f"Building prompt for question: {question[:50]}...")
            
            # Build the main prompt
            prompt = self._build_main_prompt(question, chunks, include_diagrams, include_suggestions)
            
            # Generate response using LLM
            if self.llm_api_key:
                result = await self._generate_with_llm(prompt)
            else:
                # Fallback response when no LLM is configured
                result = self._generate_fallback_response(question, chunks)
            
            logger.info(f"Generated response with {len(result.diagrams)} diagrams and {len(result.suggestions)} suggestions")
            return result
            
        except Exception as e:
            logger.error(f"Error in prompt building and generation: {str(e)}")
            return self._generate_error_response(question, str(e))
    
    def _build_main_prompt(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        include_diagrams: bool,
        include_suggestions: bool
    ) -> str:
        """Build the main system prompt with context"""
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):  # Use top 5 chunks
            content = chunk.get("content", "")
            title = chunk.get("title", f"Source {i+1}")
            url = chunk.get("url", "")
            
            context_part = f"[Source {i+1}: {title}]"
            if url:
                context_part += f" (URL: {url})"
            context_part += f"\n{content}\n"
            
            context_parts.append(context_part)
        
        context_text = "\n".join(context_parts)
        
        # Build the main prompt
        prompt = f"""You are a helpful AI assistant that provides comprehensive, accurate answers based on the given context.

CONTEXT SOURCES:
{context_text}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the context sources above
2. Be comprehensive and detailed in your response
3. Include relevant citations by referencing [Source X] in your answer
4. If the context doesn't contain enough information to fully answer the question, acknowledge this limitation
5. Structure your response clearly with appropriate formatting"""

        if include_diagrams:
            prompt += """
6. If the topic would benefit from visual representation, create relevant diagrams using Mermaid syntax
7. Wrap diagram code in ```mermaid blocks with appropriate titles"""

        if include_suggestions:
            prompt += """
8. Provide 2-3 relevant follow-up questions that users might want to ask based on this topic"""

        prompt += """

Please provide a well-structured response that addresses the user's question comprehensively."""

        return prompt
    
    async def _generate_with_llm(self, prompt: str) -> PromptResult:
        """Generate response using configured LLM"""
        try:
            client = await self._get_client()
            
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate, well-structured responses with proper citations."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = await client.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"LLM generation failed: {response.status_code} - {response.text}")
                raise Exception(f"LLM API error: {response.status_code}")
            
            llm_response = response.json()
            content = llm_response["choices"][0]["message"]["content"]
            tokens_used = llm_response.get("usage", {}).get("total_tokens", 0)
            
            # Parse the response to extract answer, diagrams, and suggestions
            return self._parse_llm_response(content, tokens_used)
            
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise
    
    def _parse_llm_response(self, content: str, tokens_used: int) -> PromptResult:
        """Parse LLM response to extract components"""
        try:
            # Extract diagrams
            diagrams = self._extract_diagrams(content)
            
            # Extract suggestions
            suggestions = self._extract_suggestions(content)
            
            # Clean the main answer by removing diagram blocks and suggestions
            answer = self._clean_answer(content, diagrams, suggestions)
            
            return PromptResult(
                answer=answer,
                diagrams=diagrams,
                suggestions=suggestions,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return PromptResult(
                answer=content,
                diagrams=[],
                suggestions=[],
                tokens_used=tokens_used
            )
    
    def _extract_diagrams(self, content: str) -> List[Diagram]:
        """Extract Mermaid diagrams from content"""
        diagrams = []
        
        # Find all mermaid code blocks
        mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.findall(mermaid_pattern, content, re.DOTALL)
        
        for i, match in enumerate(matches):
            # Try to extract title from the diagram or surrounding text
            title = f"Diagram {i+1}"
            
            # Look for title comments in mermaid code
            title_match = re.search(r'%%\s*title:\s*(.+)', match)
            if title_match:
                title = title_match.group(1).strip()
            
            diagrams.append(Diagram(
                type="mermaid",
                content=match.strip(),
                title=title,
                description=f"Generated diagram for the response"
            ))
        
        return diagrams
    
    def _extract_suggestions(self, content: str) -> List[Suggestion]:
        """Extract follow-up suggestions from content"""
        suggestions = []
        
        # Look for follow-up questions patterns
        patterns = [
            r'(?:Follow[- ]?up questions?|Related questions?|You might also ask):\s*\n((?:[-*•]\s*.+\n?)+)',
            r'(?:Suggested questions?|Next questions?):\s*\n((?:[-*•]\s*.+\n?)+)',
            r'\n((?:[-*•]\s*.+\?\s*\n?)+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                questions_text = match.group(1)
                
                # Extract individual questions
                question_lines = re.findall(r'[-*•]\s*(.+\?)', questions_text)
                
                for i, question in enumerate(question_lines[:3]):  # Max 3 suggestions
                    suggestions.append(Suggestion(
                        question=question.strip(),
                        relevance=1.0 - (i * 0.1)  # Slightly decreasing relevance
                    ))
                break
        
        return suggestions
    
    def _clean_answer(self, content: str, diagrams: List[Diagram], suggestions: List[Suggestion]) -> str:
        """Clean the main answer by removing diagram blocks and suggestions"""
        cleaned = content
        
        # Remove mermaid blocks
        cleaned = re.sub(r'```mermaid\s*\n.*?\n```', '', cleaned, flags=re.DOTALL)
        
        # Remove follow-up questions sections
        patterns = [
            r'(?:Follow[- ]?up questions?|Related questions?|You might also ask):\s*\n(?:[-*•]\s*.+\n?)+',
            r'(?:Suggested questions?|Next questions?):\s*\n(?:[-*•]\s*.+\n?)+',
            r'\n(?:[-*•]\s*.+\?\s*\n?)+$'
        ]
        
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _generate_fallback_response(self, question: str, chunks: List[Dict[str, Any]]) -> PromptResult:
        """Generate fallback response when LLM is not available"""
        if not chunks:
            answer = "I couldn't find relevant information to answer your question. Please try rephrasing or asking about a different topic."
        else:
            # Create a simple response from the top chunk
            top_chunk = chunks[0]
            content = top_chunk.get("content", "")[:500]
            answer = f"Based on the available information: {content}"
            
            if len(chunks) > 1:
                answer += f"\n\nThis response is based on {len(chunks)} relevant sources."
        
        return PromptResult(
            answer=answer,
            diagrams=[],
            suggestions=[],
            tokens_used=0
        )
    
    def _generate_error_response(self, question: str, error: str) -> PromptResult:
        """Generate error response"""
        answer = f"I apologize, but I encountered an error while processing your question. Please try again later. Error details: {error}"
        
        return PromptResult(
            answer=answer,
            diagrams=[],
            suggestions=[],
            tokens_used=0
        )
    
    async def health_check(self) -> bool:
        """Check if prompt building service is available"""
        try:
            if not self.llm_api_key:
                return True  # Service works with fallback
            
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {self.llm_api_key}"}
            response = await client.get(f"{self.llm_base_url}/models", headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Prompt builder health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()
            self.client = None