#!/usr/bin/env python3
"""Test script to debug image service issues"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_service():
    """Test the DirectImageService to find the bug"""
    try:
        from direct_image_service import DirectImageService
        
        service = DirectImageService()
        logger.info("DirectImageService initialized")
        
        # Test loading metadata
        metadata = service.load_image_metadata()
        logger.info(f"Loaded metadata with {len(metadata)} documents")
        
        # Print sample metadata structure
        for doc_name, images in list(metadata.items())[:2]:
            logger.info(f"Document: {doc_name}")
            logger.info(f"Images type: {type(images)}")
            if isinstance(images, list) and images:
                logger.info(f"First image keys: {images[0].keys()}")
        
        # Test extracting keywords
        query = "display the image of Export Process Flowchart"
        keywords = service.extract_keywords_from_query(query)
        logger.info(f"Extracted keywords: {keywords}")
        
        # Test searching for relevant images
        logger.info("Testing search_relevant_images...")
        relevant_images = service.search_relevant_images(query, limit=2)
        logger.info(f"Found {len(relevant_images)} relevant images")
        
        for img in relevant_images:
            logger.info(f"Image: {img.get('image_filename', 'Unknown')}, Score: {img.get('relevance_score', 0)}")
        
        # Test getting images for query
        logger.info("Testing get_images_for_query...")
        result_images = service.get_images_for_query(query, limit=1)
        logger.info(f"Final result: {len(result_images)} images")
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_service()