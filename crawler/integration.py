"""
Integration script for using the e24.no crawler with the osint_comments project.

This script demonstrates how to use the crawler with the Kafka producer
from the osint_comments package to publish articles with comments to Kafka.
"""
import logging
import sys
import os
import argparse
from typing import List, Optional

# Add parent directory to path to import osint_comments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.web_scraper import E24Scraper
from crawler.crawler_service import CrawlerService
from crawler.article_repository import ArticleRepository
from crawler.models import Article

# Import from osint_comments package
try:
    from osint_comments.kafka_producer import KafkaProducer
    from osint_comments.config import Config
    KAFKA_AVAILABLE = True
except ImportError:
    print("Warning: osint_comments package not found. Kafka integration will be disabled.")
    KAFKA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crawler_integration.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Integrate e24.no crawler with osint_comments Kafka"
    )
    
    parser.add_argument(
        "--pages", 
        type=int, 
        default=3, 
        help="Number of pages to crawl (default: 3)"
    )
    
    parser.add_argument(
        "--max-articles", 
        type=int, 
        default=None, 
        help="Maximum number of articles to process (default: all)"
    )
    
    parser.add_argument(
        "--db-path", 
        type=str, 
        default="articles.db", 
        help="Path to SQLite database file (default: articles.db)"
    )
    
    parser.add_argument(
        "--cache-dir", 
        type=str, 
        default="./cache", 
        help="Directory for caching crawled articles (default: ./cache)"
    )
    
    parser.add_argument(
        "--kafka-topic", 
        type=str, 
        default="article-with-comments", 
        help="Kafka topic to publish to (default: article-with-comments)"
    )
    
    parser.add_argument(
        "--no-kafka", 
        action="store_true", 
        help="Disable Kafka integration"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    return parser


def print_articles(articles: List[Article]):
    """Print a list of articles to the console."""
    if not articles:
        print("No articles found.")
        return
    
    print(f"Found {len(articles)} articles:")
    print("-" * 80)
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Published: {article.published_date}")
        print(f"   Author: {article.author}")
        print(f"   Comments: {article.comment_count or 'Unknown'}")
        print("-" * 80)


def main():
    """Main entry point for the integration script."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create repository
    repository = ArticleRepository(db_path=args.db_path)
    
    # Create Kafka producer if available and not disabled
    kafka_producer = None
    if KAFKA_AVAILABLE and not args.no_kafka:
        try:
            # Load configuration from osint_comments
            config = Config()
            
            # Create Kafka producer
            kafka_producer = KafkaProducer(
                bootstrap_servers=config.kafka_bootstrap_servers,
                topic=args.kafka_topic
            )
            logger.info(f"Kafka producer created for topic: {args.kafka_topic}")
        except Exception as e:
            logger.error(f"Error creating Kafka producer: {e}")
            logger.info("Continuing without Kafka integration")
    
    # Create scraper and crawler service
    scraper = E24Scraper()
    crawler_service = CrawlerService(
        scraper=scraper,
        repository=repository,
        kafka_producer=kafka_producer,
        cache_dir=args.cache_dir
    )
    
    # Run crawler
    logger.info(f"Starting crawler with {args.pages} pages")
    articles = crawler_service.crawl_recent_articles(pages=args.pages)
    
    logger.info(f"Processing {len(articles)} articles")
    articles_with_comments = crawler_service.process_articles(
        articles=articles,
        max_articles=args.max_articles,
        publish_to_kafka=(kafka_producer is not None)
    )
    
    # Print results
    logger.info(f"Found {len(articles_with_comments)} articles with comments")
    print_articles(articles_with_comments)
    
    # Log Kafka status
    if kafka_producer is not None:
        logger.info(f"Articles with comments published to Kafka topic: {args.kafka_topic}")
    

if __name__ == "__main__":
    main()
