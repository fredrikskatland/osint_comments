"""
Integration module for the e24.no crawler with the osint_comments project.

This module provides functionality to fetch articles with comments from e24.no
and process them using the osint_comments analysis pipeline.
"""
import logging
import sys
import os
import argparse
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

# Import from crawler package
import crawler.web_scraper
import crawler.crawler_service
import crawler.article_repository
import crawler.models

# Import from osint_comments package
from .kafka_producer import KafkaProducer
from . import config
from .models import Comment, Article
from .repository import Repository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E24Integration:
    """
    Integration class for the e24.no crawler with the osint_comments project.
    """
    
    def __init__(self, db_path: str = "osint_comments.db", kafka_bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the integration.
        
        Args:
            db_path: Path to the SQLite database file
            kafka_bootstrap_servers: Kafka bootstrap servers
        """
        # Create repository
        self.db_path = db_path
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        
        # Set up SQLAlchemy engine and session
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from .models import Base
        
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create repository
        self.repository = Repository(session)
        
        # Create Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            topic="raw-comments"
        )
        
        # Create crawler components
        self.article_repository = crawler.article_repository.ArticleRepository(db_path="e24_articles.db")
        self.scraper = crawler.web_scraper.E24Scraper()
        self.crawler_service = crawler.crawler_service.CrawlerService(
            scraper=self.scraper,
            repository=self.article_repository,
            kafka_producer=None,  # We'll handle Kafka publishing ourselves
            cache_dir="./e24_cache"
        )
    
    def convert_to_osint_article(self, crawler_article: crawler.models.Article) -> Article:
        """
        Convert a crawler Article to an osint_comments Article.
        
        Args:
            crawler_article: Article from the crawler
            
        Returns:
            Article for osint_comments
        """
        return Article(
            url=crawler_article.url,
            title=crawler_article.title,
            source="e24.no",
            published_date=crawler_article.published_date,
            author=crawler_article.author,
            content=crawler_article.content
        )
    
    def extract_comments(self, crawler_article: crawler.models.Article) -> List[Comment]:
        """
        Extract comments from a crawler Article.
        
        This is a placeholder method. In a real implementation, you would
        need to extract the actual comments from the article page.
        
        Args:
            crawler_article: Article from the crawler
            
        Returns:
            List of comments
        """
        # This is a placeholder. In a real implementation, you would
        # need to extract the actual comments from the article page.
        # For now, we'll just create a dummy comment.
        if not crawler_article.has_comments:
            return []
        
        # Create a dummy comment
        comment = Comment(
            article_url=crawler_article.url,
            content="This is a placeholder comment. In a real implementation, you would extract the actual comments.",
            author="Unknown",
            timestamp=datetime.now(),
            source="e24.no"
        )
        
        return [comment]
    
    def process_article(self, crawler_article: crawler.models.Article) -> None:
        """
        Process an article from the crawler.
        
        Args:
            crawler_article: Article from the crawler
        """
        # Convert to osint_comments Article
        article = self.convert_to_osint_article(crawler_article)
        
        # Save article to repository
        self.repository.save_article(article)
        
        # Extract comments
        comments = self.extract_comments(crawler_article)
        
        # Save comments to repository and publish to Kafka
        for comment in comments:
            # Save comment to repository
            self.repository.save_comment(comment)
            
            # Publish comment to Kafka
            self.kafka_producer.send_message(comment.to_dict())
            
        logger.info(f"Processed article: {article.title} with {len(comments)} comments")
    
    def run(self, pages: int = 3, max_articles: Optional[int] = None) -> None:
        """
        Run the integration.
        
        Args:
            pages: Number of pages to crawl
            max_articles: Maximum number of articles to process
        """
        logger.info(f"Starting e24.no integration with {pages} pages")
        
        # Crawl articles
        articles = self.crawler_service.crawl_recent_articles(pages=pages)
        
        # Process articles
        articles_with_comments = self.crawler_service.process_articles(
            articles=articles,
            max_articles=max_articles,
            publish_to_kafka=False  # We'll handle Kafka publishing ourselves
        )
        
        # Process articles with comments
        for article in articles_with_comments:
            self.process_article(article)
        
        logger.info(f"Processed {len(articles_with_comments)} articles with comments")


def main():
    """Main entry point for the integration."""
    parser = argparse.ArgumentParser(
        description="Integrate e24.no crawler with osint_comments"
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
        default="osint_comments.db", 
        help="Path to SQLite database file (default: osint_comments.db)"
    )
    
    parser.add_argument(
        "--kafka-servers", 
        type=str, 
        default="localhost:9092", 
        help="Kafka bootstrap servers (default: localhost:9092)"
    )
    
    args = parser.parse_args()
    
    # Create integration
    integration = E24Integration(
        db_path=args.db_path,
        kafka_bootstrap_servers=args.kafka_servers
    )
    
    # Run integration
    integration.run(pages=args.pages, max_articles=args.max_articles)


if __name__ == "__main__":
    main()
