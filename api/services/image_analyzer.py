"""
Image Analyzer with OpenAI Vision API and OCR fallback
Analyzes extracted images to provide descriptions and text content.
"""

import os
import base64
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

# Optional OpenAI for image analysis
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """AI-powered image analysis using OpenAI Vision API with OCR fallback."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.analysis_cache_file = "image_analysis_cache.json"
        self.analysis_cache = {}
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI Vision API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        elif not OPENAI_AVAILABLE:
            logger.info("OpenAI not available - using OCR only for image analysis")
        else:
            logger.info("No OpenAI API key provided - using OCR only")
        
        # Load existing analysis cache
        self._load_analysis_cache()
    
    def _load_analysis_cache(self) -> None:
        """Load existing analysis results from cache."""
        try:
            if os.path.exists(self.analysis_cache_file):
                with open(self.analysis_cache_file, 'r', encoding='utf-8') as f:
                    self.analysis_cache = json.load(f)
                logger.info(f"Loaded analysis cache with {len(self.analysis_cache)} entries")
        except Exception as e:
            logger.error(f"Error loading analysis cache: {e}")
            self.analysis_cache = {}
    
    def _save_analysis_cache(self) -> None:
        """Save analysis results to cache."""
        try:
            with open(self.analysis_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving analysis cache: {e}")
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for API."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    def analyze_with_openai_vision(self, image_path: str, context: str = "") -> Dict[str, str]:
        """Analyze image using OpenAI Vision API."""
        if not self.client:
            return {"error": "OpenAI client not initialized"}
        
        try:
            # Check cache first
            cache_key = f"{image_path}:{context}"
            if cache_key in self.analysis_cache:
                logger.info(f"Using cached analysis for {os.path.basename(image_path)}")
                return self.analysis_cache[cache_key]
            
            # Encode the image
            base64_image = self._encode_image(image_path)
            if not base64_image:
                return {"error": "Failed to encode image"}
            
            # Create the prompt
            prompt = f"""Analyze this image from a DGFT (Directorate General of Foreign Trade) document.

Context: This image is from a document about {context}

Please provide a comprehensive analysis including:
1. **Content Description**: What type of content is this (form, chart, diagram, flowchart, table, etc.)
2. **Text Content**: Any visible text, labels, headings, or data
3. **Structure**: Layout, organization, and key elements
4. **Trade Information**: Any trade, export, import, or DGFT-related information
5. **Actionable Items**: Procedures, requirements, or steps mentioned
6. **Key Data**: Numbers, dates, codes, or important values

Focus on information relevant to trade procedures and DGFT operations. Be detailed and thorough."""

            # Make API call
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            result = {
                "analysis": analysis,
                "model": "gpt-4-vision-preview",
                "success": True,
                "analyzed_at": datetime.now().isoformat(),
                "context": context
            }
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            self._save_analysis_cache()
            
            return result
            
        except Exception as e:
            error_msg = f"OpenAI Vision analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def analyze_with_ocr(self, image_path: str) -> Dict[str, str]:
        """Fallback OCR analysis using pytesseract."""
        try:
            import pytesseract
            
            # Check cache first
            cache_key = f"{image_path}:ocr"
            if cache_key in self.analysis_cache:
                logger.info(f"Using cached OCR for {os.path.basename(image_path)}")
                return self.analysis_cache[cache_key]
            
            # Open and process image
            img = Image.open(image_path)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(img, config='--psm 6')
            
            # Basic analysis
            analysis = f"""**OCR Text Extraction Results**

**Extracted Text:**
{extracted_text.strip() if extracted_text.strip() else "No readable text found in image"}

**Image Properties:**
- Dimensions: {img.size[0]} x {img.size[1]} pixels
- Format: {img.format}
- Mode: {img.mode}

**Analysis Method:** Optical Character Recognition (OCR)
**Note:** This is basic text extraction. For detailed AI analysis of visual content, configure OpenAI Vision API."""
            
            result = {
                "analysis": analysis,
                "extracted_text": extracted_text.strip(),
                "model": "pytesseract-ocr",
                "success": True,
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            self._save_analysis_cache()
            
            return result
            
        except ImportError:
            return {
                "error": "pytesseract not installed. Install with: pip install pytesseract",
                "success": False
            }
        except Exception as e:
            error_msg = f"OCR analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def analyze_image(self, image_path: str, context: str = "", use_ai: bool = True) -> Dict[str, str]:
        """Analyze a single image using the best available method."""
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}", "success": False}
        
        logger.info(f"Analyzing image: {os.path.basename(image_path)}")
        
        # Try AI analysis first if available and requested
        if use_ai and self.client:
            result = self.analyze_with_openai_vision(image_path, context)
            if result.get("success"):
                return result
            else:
                logger.warning(f"AI analysis failed, falling back to OCR: {result.get('error')}")
        
        # Fallback to OCR
        return self.analyze_with_ocr(image_path)
    
    def analyze_multiple_images(self, image_list: List[Dict], use_ai: bool = True) -> Dict[str, Dict]:
        """Analyze multiple images and return results."""
        results = {}
        total = len(image_list)
        
        logger.info(f"Starting analysis of {total} images...")
        
        for i, img_info in enumerate(image_list, 1):
            image_path = img_info.get('image_path')
            image_filename = img_info.get('image_filename', os.path.basename(image_path))
            context = img_info.get('source_document', '')
            
            logger.info(f"[{i}/{total}] Analyzing: {image_filename}")
            
            # Analyze the image
            analysis_result = self.analyze_image(image_path, context, use_ai)
            
            # Add image metadata to result
            analysis_result['image_info'] = img_info
            
            # Store result
            results[image_filename] = analysis_result
            
            # Log result
            if analysis_result.get("success"):
                preview = analysis_result['analysis'][:100] + "..." if len(analysis_result['analysis']) > 100 else analysis_result['analysis']
                logger.info(f"  ✅ Success: {preview}")
            else:
                logger.error(f"  ❌ Failed: {analysis_result.get('error', 'Unknown error')}")
        
        logger.info(f"Analysis complete! Processed {total} images.")
        return results
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of all analyzed images."""
        if not self.analysis_cache:
            return {"total_analyzed": 0, "successful": 0, "failed": 0}
        
        successful = sum(1 for result in self.analysis_cache.values() if result.get("success"))
        failed = len(self.analysis_cache) - successful
        
        # Model usage statistics
        models = {}
        for result in self.analysis_cache.values():
            if result.get("success"):
                model = result.get("model", "unknown")
                models[model] = models.get(model, 0) + 1
        
        return {
            "total_analyzed": len(self.analysis_cache),
            "successful": successful,
            "failed": failed,
            "models_used": models,
            "cache_file": self.analysis_cache_file
        }
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        try:
            self.analysis_cache = {}
            if os.path.exists(self.analysis_cache_file):
                os.remove(self.analysis_cache_file)
            logger.info("Analysis cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

if __name__ == "__main__":
    # Test the image analyzer
    analyzer = ImageAnalyzer()
    
    # Get summary
    summary = analyzer.get_analysis_summary()
    print(f"Analysis Summary: {summary}")
    
    # Test with a sample image if available
    import glob
    image_files = glob.glob("extracted_images/*.png") + glob.glob("extracted_images/*.jpg")
    
    if image_files:
        test_image = image_files[0]
        print(f"\nTesting with: {test_image}")
        
        result = analyzer.analyze_image(test_image, "DGFT document test", use_ai=True)
        
        if result.get("success"):
            print("✅ Analysis successful!")
            print(f"Analysis: {result['analysis'][:200]}...")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
    else:
        print("No test images found in extracted_images folder")