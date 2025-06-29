#!/usr/bin/env python3
"""
Script to generate bulk news articles for all instruments and send them to the vector database.
Generates 10 news articles per instrument, with document_type="news" and desk="" except for 25% 
of articles which get a random desk (Desk001...Desk009).
"""

import json
import os
import sys
import random
import requests
import logging
from typing import Dict, Any, List
from datetime import datetime

# Add the parent directories to the path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
great_grandparent_dir = os.path.dirname(grandparent_dir)

sys.path.insert(0, great_grandparent_dir)
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from article_generator import NewsArticleGenerator


class BulkNewsGenerator:
    """Generates bulk news articles for all instruments and sends them to vector database."""
    
    DESK_OPTIONS = [f"Desk{str(i).zfill(3)}" for i in range(1, 10)]  # Desk001 to Desk009
    DESK_PROBABILITY = 0.25  # 25% chance of assigning a desk
    ARTICLES_PER_INSTRUMENT = 10
    
    def __init__(self, vector_db_url: str = "http://localhost:6000"):
        """
        Initialize the bulk news generator.
        
        Args:
            vector_db_url: URL of the vector database service
        """
        self.vector_db_url = vector_db_url
        self.logger = self._setup_logger()
        
        # Load news configuration
        self.news_config = self._load_news_config()
        
        # Initialize article generator
        self.article_generator = NewsArticleGenerator(self.news_config)
        
        # Load instruments
        self.instruments = self._load_instruments()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the script."""
        logger = logging.getLogger("BulkNewsGenerator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_news_config(self) -> Dict[str, Any]:
        """Load the news configuration file."""
        # Look for news config in the news_service directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "news_config.json")
        
        if not os.path.exists(config_path):
            # Try alternative paths
            alt_paths = [
                "/mcp/python/src/server/news_service/news_config.json",
                "/mcp/config/news_config.json"
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    config_path = alt_path
                    break
            else:
                raise FileNotFoundError(f"News config file not found. Tried: {config_path}, {alt_paths}")
        
        self.logger.info(f"Loading news config from: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_instruments(self) -> List[Dict[str, Any]]:
        """Load instruments from instrument.json."""
        # Look for instrument.json in the root directory
        instrument_paths = [
            "/mcp/instrument.json",
            "/mcp/python/src/server/instrument_service/instrument.json"
        ]
        
        instrument_path = None
        for path in instrument_paths:
            if os.path.exists(path):
                instrument_path = path
                break
        
        if not instrument_path:
            raise FileNotFoundError(f"Instrument file not found. Tried: {instrument_paths}")
        
        self.logger.info(f"Loading instruments from: {instrument_path}")
        
        with open(instrument_path, 'r', encoding='utf-8') as f:
            instruments = json.load(f)
        
        self.logger.info(f"Loaded {len(instruments)} instruments")
        return instruments
    
    def _get_random_desk(self) -> str:
        """
        Get a random desk assignment based on probability.
        
        Returns:
            Empty string 75% of the time, random desk 25% of the time
        """
        if random.random() < self.DESK_PROBABILITY:
            return random.choice(self.DESK_OPTIONS)
        return ""
    
    def _send_to_vector_db(self, document: str, desk: str = "") -> bool:
        """
        Send a document to the vector database.
        
        Args:
            document: The news article text to send
            desk: The desk assignment (empty string or DeskXXX)
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.vector_db_url}/add_document"
        
        payload = {
            "document": document,
            "document_type": "news",
            "desk": desk
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.debug(f"Successfully sent document to vector DB (desk: '{desk}', response: {response.status_code})")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send document to vector DB: {e}")
            return False
    
    def generate_news_for_instrument(self, instrument: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate news articles for a single instrument.
        
        Args:
            instrument: Instrument data dictionary
            
        Returns:
            List of generated articles with metadata
        """
        instrument_name = instrument.get("Instrument_Long_Name", "Unknown")
        industry = instrument.get("Industry", "General")
        
        self.logger.info(f"Generating {self.ARTICLES_PER_INSTRUMENT} articles for {instrument_name} (Industry: {industry})")
        
        articles = []
        
        for i in range(self.ARTICLES_PER_INSTRUMENT):
            try:
                self.logger.debug(f"  Generating article {i+1}/{self.ARTICLES_PER_INSTRUMENT} for {instrument_name}")
                
                # Generate article using the article generator
                article_data = self.article_generator.generate_article(
                    stock_name=instrument_name,
                    sector=industry,
                    venue="Exchange"  # Default venue
                )
                
                # Create the full article text
                headline = article_data.get("headline", "")
                article_text = article_data.get("article", "")
                publish_time = article_data.get("publish_time", datetime.now().isoformat())
                
                self.logger.debug(f"  Generated headline: {headline[:60]}...")
                
                # Combine headline and article for the document
                full_document = f"HEADLINE: {headline}\n\nARTICLE: {article_text}\n\nPUBLISH_TIME: {publish_time}"
                
                # Determine desk assignment
                desk = self._get_random_desk()
                
                # Send to vector database
                self.logger.debug(f"  Sending article {i+1} to vector DB (desk: '{desk}', doc length: {len(full_document)} chars)")
                success = self._send_to_vector_db(full_document, desk)
                
                article_info = {
                    "instrument": instrument_name,
                    "headline": headline,
                    "desk": desk,
                    "success": success,
                    "article_number": i + 1
                }
                
                articles.append(article_info)
                
                if success:
                    desk_info = f" (desk: {desk})" if desk else " (no desk)"
                    self.logger.info(f"  ✓ Article {i+1}/{self.ARTICLES_PER_INSTRUMENT} sent successfully{desk_info}")
                else:
                    self.logger.warning(f"  ✗ Article {i+1}/{self.ARTICLES_PER_INSTRUMENT} failed to send")
                    
            except Exception as e:
                self.logger.error(f"  ✗ Failed to generate article {i+1} for {instrument_name}: {e}")
                articles.append({
                    "instrument": instrument_name,
                    "headline": "ERROR",
                    "desk": "",
                    "success": False,
                    "article_number": i + 1,
                    "error": str(e)
                })
        
        # Log summary for this instrument
        successful_count = sum(1 for a in articles if a["success"])
        with_desk_count = sum(1 for a in articles if a["success"] and a["desk"])
        self.logger.info(f"Completed {instrument_name}: {successful_count}/{len(articles)} articles successful, {with_desk_count} with desk assignment")
        
        return articles
    
    def generate_all_news(self) -> Dict[str, Any]:
        """
        Generate news articles for all instruments.
        
        Returns:
            Summary statistics of the generation process
        """
        self.logger.info("=" * 60)
        self.logger.info(f"STARTING BULK NEWS GENERATION")
        self.logger.info(f"Total instruments to process: {len(self.instruments)}")
        self.logger.info(f"Articles per instrument: {self.ARTICLES_PER_INSTRUMENT}")
        self.logger.info(f"Expected total articles: {len(self.instruments) * self.ARTICLES_PER_INSTRUMENT}")
        self.logger.info(f"Desk assignment probability: {self.DESK_PROBABILITY * 100}%")
        self.logger.info(f"Vector DB URL: {self.vector_db_url}")
        self.logger.info("=" * 60)
        
        total_articles = 0
        successful_articles = 0
        failed_articles = 0
        articles_with_desk = 0
        
        start_time = datetime.now()
        
        for idx, instrument in enumerate(self.instruments, 1):
            instrument_name = instrument.get("Instrument_Long_Name", "Unknown")
            
            # Progress indicator
            progress_percent = (idx / len(self.instruments)) * 100
            self.logger.info(f"[{idx}/{len(self.instruments)}] ({progress_percent:.1f}%) Processing: {instrument_name}")
            
            articles = self.generate_news_for_instrument(instrument)
            
            # Update statistics
            for article in articles:
                total_articles += 1
                if article["success"]:
                    successful_articles += 1
                    if article["desk"]:
                        articles_with_desk += 1
                else:
                    failed_articles += 1
            
            # Log running totals every 10 instruments or at the end
            if idx % 10 == 0 or idx == len(self.instruments):
                elapsed = datetime.now() - start_time
                rate = idx / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                self.logger.info(f"Progress Update: {idx}/{len(self.instruments)} instruments processed "
                               f"({successful_articles} successful, {failed_articles} failed articles) "
                               f"- Rate: {rate:.1f} instruments/min")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        summary = {
            "total_instruments": len(self.instruments),
            "total_articles": total_articles,
            "successful_articles": successful_articles,
            "failed_articles": failed_articles,
            "articles_with_desk": articles_with_desk,
            "articles_without_desk": successful_articles - articles_with_desk,
            "desk_assignment_rate": (articles_with_desk / successful_articles * 100) if successful_articles > 0 else 0,
            "success_rate": (successful_articles / total_articles * 100) if total_articles > 0 else 0,
            "duration_seconds": duration.total_seconds(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        self.logger.info("=" * 60)
        self.logger.info("BULK NEWS GENERATION COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(f"Total instruments processed: {summary['total_instruments']}")
        self.logger.info(f"Total articles generated: {summary['total_articles']}")
        self.logger.info(f"Successful articles: {summary['successful_articles']}")
        self.logger.info(f"Failed articles: {summary['failed_articles']}")
        self.logger.info(f"Articles with desk assignment: {summary['articles_with_desk']}")
        self.logger.info(f"Articles without desk assignment: {summary['articles_without_desk']}")
        self.logger.info(f"Desk assignment rate: {summary['desk_assignment_rate']:.1f}%")
        self.logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        self.logger.info(f"Total duration: {summary['duration_seconds']:.2f} seconds")
        self.logger.info(f"Average time per instrument: {summary['duration_seconds']/summary['total_instruments']:.2f} seconds")
        self.logger.info(f"Average time per article: {summary['duration_seconds']/summary['total_articles']:.2f} seconds")
        self.logger.info("=" * 60)
        
        return summary


def main():
    """Main function to run the bulk news generation."""
    # Parse command line arguments for vector DB URL if provided
    vector_db_url = "http://localhost:6000"
    if len(sys.argv) > 1:
        vector_db_url = sys.argv[1]
    
    print("=" * 60)
    print("BULK NEWS ARTICLE GENERATOR")
    print("=" * 60)
    print(f"Vector DB URL: {vector_db_url}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        generator = BulkNewsGenerator(vector_db_url=vector_db_url)
        summary = generator.generate_all_news()
        
        # Save summary to file
        summary_file = f"/mcp/bulk_news_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to: {summary_file}")
        
        if summary['failed_articles'] > 0:
            print(f"\n⚠️  Warning: {summary['failed_articles']} articles failed to generate/send")
            print(f"📊 Overall success rate: {summary['success_rate']:.1f}%")
            sys.exit(1)
        else:
            print(f"\n✅ Success: All {summary['successful_articles']} articles generated and sent successfully!")
            print(f"📊 Desk assignment rate: {summary['desk_assignment_rate']:.1f}% (target: 25%)")
            
    except Exception as e:
        print(f"\n❌ Error running bulk news generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
