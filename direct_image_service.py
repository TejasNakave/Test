#!/usr/bin/env python3
"""
Direct Image Service - Smart Multimodal Image Processing
Handles intelligent image filtering, analysis, and display based on user queries
"""
import json
import base64
import os
from typing import List, Dict, Any, Optional
import logging
import openai
import re

logger = logging.getLogger(__name__)

class DirectImageService:
    """Smart image service with intelligent filtering and OpenAI Vision analysis"""
    
    def __init__(self):
        self.image_folder = "extracted_images"
        self.image_metadata_file = "image_metadata.json"
        # Initialize OpenAI client for image analysis
        # Try both environment variable names for compatibility
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key, timeout=30.0)
        else:
            self.openai_client = None
            logger.warning("No OpenAI API key found. Image analysis will be limited.")
    
    def load_image_metadata(self) -> Dict:
        """Load image metadata from JSON file"""
        try:
            if os.path.exists(self.image_metadata_file):
                with open(self.image_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading image metadata: {e}")
        return {}
    
    def extract_keywords_from_query(self, query: str) -> List[str]:
        """Extract and clean keywords from user query"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'me', 'my', 'show', 'display', 'what', 'is', 'are', 'can', 'could', 'would', 'should', 'its'}
        
        # Extract words and filter
        words = query.lower().replace('?', '').replace(',', '').replace('.', '').split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        logger.info(f"Extracted keywords: {keywords}")
        return keywords
    
    def calculate_smart_relevance(self, image_data: Dict, keywords: List[str], user_query: str, analysis_text: str = "") -> float:
        """Calculate intelligent relevance score with precise import/export filtering using AI analysis"""
        score = 0.0
        query_lower = user_query.lower()
        filename = image_data.get('image_filename', '').lower()
        doc_name = image_data.get('source_document', '').lower()
        description = image_data.get('description', '').lower()
        
        # Combine all searchable text INCLUDING the AI analysis
        searchable_text = f"{filename} {doc_name} {description} {analysis_text.lower()}"
        
        # SMART IMPORT/EXPORT FILTERING
        query_has_import = 'import' in query_lower and 'export' not in query_lower
        query_has_export = 'export' in query_lower and 'import' not in query_lower
        query_has_both = 'import' in query_lower and 'export' in query_lower
        
        # Enhanced detection using AI analysis
        analysis_lower = analysis_text.lower()
        image_has_import = (
            'import' in searchable_text or 
            'importing' in analysis_lower or 
            'consignment clearance' in analysis_lower or
            'customs clearance for import' in analysis_lower or
            'inward' in analysis_lower
        )
        image_has_export = (
            'export' in searchable_text or 
            'exporting' in analysis_lower or 
            'shipping' in analysis_lower or
            'customs clearance for export' in analysis_lower or
            'outward' in analysis_lower
        )
        
        # If AI analysis mentions specific process, use that for precise filtering
        if analysis_text:
            if 'import process' in analysis_lower or 'import procedure' in analysis_lower:
                image_has_import = True
                if 'export' not in analysis_lower:
                    image_has_export = False
            elif 'export process' in analysis_lower or 'export procedure' in analysis_lower:
                image_has_export = True
                if 'import' not in analysis_lower:
                    image_has_import = False
        
        # Precise filtering logic
        if query_has_import and not query_has_export:
            # User wants ONLY import
            if image_has_import and not image_has_export:
                score += 0.9  # Perfect match - import only
            elif image_has_import and image_has_export:
                score += 0.3  # Mixed content, much lower score
            elif not image_has_import:
                score += 0.1  # Not relevant
        elif query_has_export and not query_has_import:
            # User wants ONLY export  
            if image_has_export and not image_has_import:
                score += 0.9  # Perfect match - export only
            elif image_has_export and image_has_import:
                score += 0.3  # Mixed content, much lower score
            elif not image_has_export:
                score += 0.1  # Not relevant
        elif query_has_both:
            # User wants both import and export
            if image_has_import and image_has_export:
                score += 0.9  # Perfect match - both
            elif image_has_import or image_has_export:
                score += 0.7  # Partial match
        
        # Specific process matching
        process_keywords = {
            'flowchart': 0.8, 'diagram': 0.7, 'process': 0.6, 'procedure': 0.6,
            'clearance': 0.7, 'svb': 0.8, 'fta': 0.8, 'customs': 0.6,
            'dgft': 0.7, 'valuation': 0.6, 'journey': 0.5
        }
        
        for keyword in keywords:
            if keyword in process_keywords:
                if keyword in searchable_text:
                    score += process_keywords[keyword]
        
        # Boost for exact keyword matches
        for keyword in keywords:
            if keyword in searchable_text:
                score += 0.3
        
        # Boost for document title relevance
        if any(keyword in doc_name for keyword in keywords):
            score += 0.4
        
        return min(score, 1.0)
    
    def search_relevant_images(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant images using smart filtering"""
        metadata = self.load_image_metadata()
        if not metadata:
            logger.warning("No image metadata found")
            return []
        
        keywords = self.extract_keywords_from_query(query)
        scored_images = []
        
        # Iterate through each document and its images
        for document_name, images_list in metadata.items():
            if not isinstance(images_list, list):
                continue
                
            for img_data in images_list:
                # Add document name to image data for context
                img_data_with_context = dict(img_data)
                img_data_with_context['source_document'] = document_name
                
                relevance_score = self.calculate_smart_relevance(img_data_with_context, keywords, query)
                if relevance_score > 0.3:  # Only include reasonably relevant images
                    img_data_with_context['relevance_score'] = relevance_score
                    img_data_with_context['image_id'] = f"{document_name}_{img_data.get('image_filename', '')}"
                    scored_images.append(img_data_with_context)
        
        # Sort by relevance score (highest first)
        scored_images.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top results
        result = scored_images[:limit]
        logger.info(f"Found {len(result)} relevant images from {len(metadata)} documents, returning top {limit}")
        return result
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                return base64_data
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
        return None
    
    def analyze_image_with_openai(self, base64_data: str, image_filename: str, user_query: str) -> str:
        """Analyze image content using OpenAI Vision API for intelligent description"""
        try:
            if not self.openai_client:
                return f"Image analysis not available (API key not configured). Image: {image_filename}"
            
            # Create simplified analysis prompt for faster response
            analysis_prompt = f"""Analyze this trade flowchart. User query: "{user_query}"

Answer in this exact format:
PROCESS TYPE: [IMPORT/EXPORT/BOTH]
DESCRIPTION: [Brief 1-2 sentence description of what this flowchart shows]
RELEVANCE: [How this relates to the user's query about "{user_query}"]

Key: 
- IMPORT = goods coming INTO country (customs clearance, consignment clearance)
- EXPORT = goods going OUT of country (shipping, export procedures)
- Look for directional flow, shipping vs clearance terminology

Be concise and specific about import vs export."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Updated model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_data}",
                                    "detail": "low"  # Use low detail for faster processing
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,  # Reduced for faster response
                temperature=0.1,  # More deterministic
                timeout=8  # Shorter timeout
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"Successfully analyzed image: {image_filename}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_filename}: {e}")
            # Provide a quick fallback description based on filename and user query
            query_lower = user_query.lower()
            filename_lower = image_filename.lower()
            
            # Quick relevance check for fallback
            if 'export' in query_lower and 'import' not in query_lower:
                if 'export' in filename_lower and 'import' not in filename_lower:
                    return f"PROCESS TYPE: EXPORT\nDESCRIPTION: Export process flowchart showing trade procedures.\nRELEVANCE: Directly matches your query about export processes."
                elif 'export' in filename_lower and 'import' in filename_lower:
                    return f"PROCESS TYPE: BOTH\nDESCRIPTION: Combined export and import operations flowchart.\nRELEVANCE: Contains export information relevant to your query."
            elif 'import' in query_lower and 'export' not in query_lower:
                if 'import' in filename_lower and 'export' not in filename_lower:
                    return f"PROCESS TYPE: IMPORT\nDESCRIPTION: Import process flowchart showing customs clearance procedures.\nRELEVANCE: Directly matches your query about import processes."
            
            # Generic fallback
            return f"PROCESS TYPE: BOTH\nDESCRIPTION: Trade process diagram showing import/export procedures.\nRELEVANCE: Contains information related to trade operations."
    
    def get_images_for_query(self, query: str, limit: int = 3) -> List[Dict]:
        """Get images with base64 data and intelligent analysis for a query"""
        # First, get all potentially relevant images (broader search)
        metadata = self.load_image_metadata()
        if not metadata:
            logger.warning("No image metadata found")
            return []
        
        keywords = self.extract_keywords_from_query(query)
        candidate_images = []
        
        # Get candidates that match basic criteria
        for document_name, images_list in metadata.items():
            if not isinstance(images_list, list):
                continue
                
            for img_data in images_list:
                # Basic relevance check (filename, doc name matching keywords)
                filename = img_data.get('image_filename', '').lower()
                doc_name = document_name.lower()
                
                basic_match = any(keyword in filename or keyword in doc_name for keyword in keywords)
                if basic_match or 'flowchart' in filename or 'diagram' in filename:
                    img_data_with_context = dict(img_data)
                    img_data_with_context['source_document'] = document_name
                    candidate_images.append(img_data_with_context)
        
        # Now analyze each candidate with OpenAI and calculate precise relevance
        analyzed_images = []
        
        # Limit to top candidates to avoid timeout
        top_candidates = candidate_images[:4]  # Process max 4 images to avoid timeout
        
        for image_info in top_candidates:
            image_path = image_info.get('image_path')
            if image_path and os.path.exists(image_path):
                try:
                    base64_data = self.encode_image_to_base64(image_path)
                    if base64_data:
                        # Analyze the image content using OpenAI Vision API with timeout protection
                        detailed_analysis = self.analyze_image_with_openai(
                            base64_data, 
                            image_info.get('image_filename'), 
                            query
                        )
                        
                        # Calculate relevance based on actual image content analysis
                        relevance_score = self.calculate_smart_relevance(
                            image_info, keywords, query, detailed_analysis
                        )
                        
                        if relevance_score > 0.4:  # Slightly lower threshold for better results
                            analyzed_images.append({
                                'filename': image_info.get('image_filename'),
                                'source_document': image_info.get('source_document'),
                                'base64_data': base64_data,
                                'analysis': detailed_analysis,
                                'relevance_score': relevance_score,
                                'description': image_info.get('description', 'Trade process diagram')
                            })
                except Exception as e:
                    logger.warning(f"Failed to process image {image_info.get('image_filename')}: {e}")
                    continue  # Skip failed images and continue with others
        
        # Sort by relevance score (highest first) and limit results
        analyzed_images.sort(key=lambda x: x['relevance_score'], reverse=True)
        result_images = analyzed_images[:limit]
        
        logger.info(f"Prepared {len(result_images)} images with intelligent analysis for query: {query}")
        return result_images

# Global instance
direct_image_service = DirectImageService()