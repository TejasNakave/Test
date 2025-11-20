import httpx
import logging
from typing import List, Optional, Dict, Any
from ..config import OPENAI_API_KEY
from ..schemas import LLMResponse, ChatMessage
import time
import json
import base64
import os
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class LLMService:
    """Enhanced service for multimodal interactions with text and images"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.vision_model = "gpt-4-vision-preview"
        self.text_model = "gpt-3.5-turbo"
        self.max_tokens = 1000
        self.temperature = 0.7
        self.client = None
        
        # Dynamic paths - will be detected automatically
        self.image_folder = "extracted_images"
        self.image_metadata_file = "image_metadata.json"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=60.0)
        return self.client
    
    def _load_image_metadata(self) -> Dict:
        """Load image metadata from document_loader.py extraction"""
        try:
            if os.path.exists(self.image_metadata_file):
                with open(self.image_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading image metadata: {e}")
        return {}
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """Dynamically extract keywords from the user query"""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'show', 'me', 'what', 'how', 'can',
            'could', 'would', 'should', 'tell', 'please', 'help', 'need'
        }
        
        # Extract words and clean them
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
    
    def _calculate_image_relevance(self, query_keywords: List[str], image_info: Dict, doc_name: str) -> float:
        """Calculate relevance score for an image based on query keywords"""
        image_filename = image_info.get('image_filename', '').lower()
        doc_name_lower = doc_name.lower()
        
        # Combine searchable text
        searchable_text = f"{image_filename} {doc_name_lower}"
        
        # Calculate relevance score
        relevance_score = 0.0
        total_keywords = len(query_keywords)
        
        if total_keywords == 0:
            return 0.0
        
        # Check each keyword
        for keyword in query_keywords:
            if keyword in searchable_text:
                # Base score for keyword match
                relevance_score += 1.0
                
                # Bonus for exact filename match
                if keyword in image_filename:
                    relevance_score += 0.5
                
                # Bonus for document name match
                if keyword in doc_name_lower:
                    relevance_score += 0.3
        
        # Normalize score (0-1 range)
        normalized_score = relevance_score / total_keywords
        
        # Additional bonus for common image-related terms
        image_indicators = ['flow', 'chart', 'process', 'form', 'diagram', 'step', 'procedure']
        for indicator in image_indicators:
            if any(indicator in text for text in [query.lower() for query in query_keywords]):
                if any(indicator in searchable_text for indicator in image_indicators):
                    normalized_score += 0.2
                    break
        
        return min(normalized_score, 1.0)  # Cap at 1.0
    
    def _search_relevant_images(self, query: str, max_images: int = 3) -> List[Dict]:
        """Dynamically search for images relevant to any query"""
        image_metadata = self._load_image_metadata()
        
        if not image_metadata:
            logger.info("No image metadata found")
            return []
        
        # Extract keywords from query
        query_keywords = self._extract_keywords_from_query(query)
        logger.info(f"Extracted keywords from query: {query_keywords}")
        
        relevant_images = []
        
        # Search through all images
        for doc_name, images in image_metadata.items():
            for image in images:
                relevance_score = self._calculate_image_relevance(query_keywords, image, doc_name)
                
                if relevance_score > 0.1:  # Only include somewhat relevant images
                    image_info = image.copy()
                    image_info['relevance_score'] = relevance_score
                    image_info['document_name'] = doc_name
                    relevant_images.append(image_info)
        
        # Sort by relevance and return top results
        relevant_images.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Found {len(relevant_images)} relevant images, returning top {max_images}")
        return relevant_images[:max_images]
    
    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 for OpenAI Vision API"""
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
        return None
    
    async def _analyze_image_with_vision(self, image_path: str, query_context: str) -> Optional[str]:
        """Analyze image using OpenAI Vision API with dynamic context"""
        try:
            base64_image = self._encode_image_to_base64(image_path)
            if not base64_image:
                return None
            
            client = await self._get_client()
            
            # Dynamic prompt based on query context
            vision_prompt = f"""Analyze this image in the context of the user's question: "{query_context}"

Please describe:
1. What you see in the image (charts, diagrams, text, forms, etc.)
2. Any processes, workflows, or procedures shown
3. Key information, steps, or data presented
4. How this relates to the user's question

Focus on providing specific, relevant details that would help answer their query."""
            
            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Vision API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None
    
    async def generate_response(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        include_images: bool = True
    ) -> LLMResponse:
        """
        Generate response with optional image analysis for any topic
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating response for: {message[:50]}...")
            
            # Step 1: Search for relevant images if requested
            image_analyses = []
            if include_images:
                relevant_images = self._search_relevant_images(message)
                logger.info(f"Found {len(relevant_images)} relevant images")
                
                # Step 2: Analyze relevant images
                for image_info in relevant_images:
                    image_path = image_info.get('image_path')
                    if image_path and os.path.exists(image_path):
                        analysis = await self._analyze_image_with_vision(image_path, message)
                        if analysis:
                            image_analyses.append({
                                'filename': image_info.get('image_filename'),
                                'source_document': image_info.get('document_name'),
                                'analysis': analysis,
                                'relevance_score': image_info.get('relevance_score', 0)
                            })
            
            # Step 3: Build enhanced system prompt with image context
            enhanced_system_prompt = system_prompt or ""
            
            if image_analyses:
                enhanced_system_prompt += f"\n\nRELEVANT VISUAL CONTENT FOUND ({len(image_analyses)} images):\n"
                for i, img_analysis in enumerate(image_analyses, 1):
                    enhanced_system_prompt += f"\nImage {i}: {img_analysis['filename']}\n"
                    enhanced_system_prompt += f"Source Document: {img_analysis['source_document']}\n"
                    enhanced_system_prompt += f"Visual Analysis: {img_analysis['analysis']}\n"
                    enhanced_system_prompt += f"Relevance: {img_analysis['relevance_score']:.2f}\n"
                
                enhanced_system_prompt += "\nIMPORTANT: Use this visual information to enhance your response. Reference the images when relevant and describe their content to help the user understand the visual elements related to their question."
            
            # Step 4: Build messages array
            messages = []
            
            if enhanced_system_prompt:
                messages.append({
                    "role": "system",
                    "content": enhanced_system_prompt
                })
            
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Step 5: Generate response
            client = await self._get_client()
            
            payload = {
                "model": self.text_model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code}")
                return LLMResponse(
                    response="I apologize, but I'm having trouble generating a response right now. Please try again.",
                    tokens_used=0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    model_used=self.text_model
                )
            
            # Parse response
            response_data = response.json()
            generated_text = response_data["choices"][0]["message"]["content"]
            tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
            
            # Step 6: Enhance response with image information if found
            if image_analyses:
                generated_text += "\n\n📊 **Related Visual Content:**\n"
                for img_analysis in image_analyses:
                    generated_text += f"\n🖼️ **{img_analysis['filename']}**\n"
                    generated_text += f"📁 *From: {img_analysis['source_document']}*\n"
                    generated_text += f"📝 *Visual Content: {img_analysis['analysis']}*\n"
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Generated response in {processing_time_ms}ms with {len(image_analyses)} images analyzed")
            
            return LLMResponse(
                response=generated_text,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                model_used=self.text_model
            )
            
        except httpx.TimeoutException:
            logger.error("LLM API request timed out")
            return LLMResponse(
                response="I apologize, but my response is taking longer than expected. Please try again.",
                tokens_used=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used=self.text_model
            )
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return LLMResponse(
                response="I encountered an error while generating a response. Please try again.",
                tokens_used=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used=self.text_model
            )
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            client = await self._get_client()
            
            embeddings = []
            batch_size = 100
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                payload = {
                    "model": "text-embedding-ada-002",
                    "input": batch
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    batch_embeddings = [item["embedding"] for item in data["data"]]
                    embeddings.extend(batch_embeddings)
                else:
                    logger.error(f"Embeddings API error: {response.status_code}")
                    embeddings.extend([[0.0] * 1536 for _ in batch])
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 1536 for _ in texts]
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()
            self.client = None