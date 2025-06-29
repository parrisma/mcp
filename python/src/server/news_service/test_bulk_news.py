#!/usr/bin/env python3
"""
Test script to verify the bulk news generation functionality without actually sending to vector DB.
"""

import json
import os
import sys

# Add the parent directories to the path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
great_grandparent_dir = os.path.dirname(grandparent_dir)

sys.path.insert(0, great_grandparent_dir)
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from generate_bulk_news import BulkNewsGenerator


def test_article_generation():
    """Test article generation for a few instruments without sending to vector DB."""
    
    class TestBulkNewsGenerator(BulkNewsGenerator):
        """Test version that doesn't actually send to vector DB."""
        
        def __init__(self):
            """Initialize without vector DB connection."""
            self.logger = self._setup_logger()
            self.news_config = self._load_news_config()
            
            from article_generator import NewsArticleGenerator
            self.article_generator = NewsArticleGenerator(self.news_config)
            
            self.instruments = self._load_instruments()[:5]  # Only test first 5 instruments
        
        def _send_to_vector_db(self, document: str, desk: str = "") -> bool:
            """Mock method that just logs instead of sending."""
            self.logger.info(f"MOCK SEND - Document length: {len(document)} chars, Desk: '{desk}'")
            self.logger.info(f"MOCK SEND - Document preview: {document[:200]}...")
            return True
    
    try:
        generator = TestBulkNewsGenerator()
        print(f"Loaded {len(generator.instruments)} test instruments")
        print(f"Testing with first few instruments...")
        
        # Test article generation for first instrument
        test_instrument = generator.instruments[0]
        print(f"\nTesting article generation for: {test_instrument['Instrument_Long_Name']}")
        
        articles = generator.generate_news_for_instrument(test_instrument)
        
        print(f"\nGenerated {len(articles)} articles:")
        for i, article in enumerate(articles, 1):
            desk_info = f" (Desk: {article['desk']})" if article['desk'] else " (No desk)"
            print(f"  Article {i}: {article['headline'][:50]}...{desk_info}")
        
        # Count desk assignments
        with_desk = sum(1 for a in articles if a['desk'])
        without_desk = len(articles) - with_desk
        desk_rate = (with_desk / len(articles)) * 100
        
        print(f"\nDesk assignment statistics:")
        print(f"  With desk: {with_desk}")
        print(f"  Without desk: {without_desk}")
        print(f"  Desk assignment rate: {desk_rate:.1f}%")
        print(f"  Expected rate: ~25%")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_article_generation()
    if success:
        print("\n✅ Test completed successfully!")
        print("You can now run the full bulk generation with:")
        print("python /mcp/python/src/server/news_service/generate_bulk_news.py")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
