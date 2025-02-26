"""
Integration module for the e24.no crawler with the osint_comments project.

This module provides functionality to fetch articles with comments from e24.no
and process them using the osint_comments analysis pipeline.
"""
import logging
import sys
import os
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

# Add parent directory to path to import crawler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from crawler package
from crawler.web_scraper import E24Scraper
from crawler.crawler_service import CrawlerService
from crawler.article_repository import ArticleRepository
from crawler.models import Article as CrawlerArticle

# Import from osint_comments package
from osint_comments.kafka_producer import KafkaProducer
from osint_comments.config import Config
from osint_comments.models import Comment, Article
from osint_comments.repository import Repository

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
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the integration.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Create repository
        self.repository = Repository(self.config.db_path)
        
        # Create Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            topic="raw-comments"
        )
        
        # Create crawler components
        self.article_repository = ArticleRepository(db_path="e24_articles.db")
        self.scraper = E24Scraper()
        self.crawler_service = CrawlerService(
            scraper=self.scraper,
            repository=self.article_repository,
            kafka_producer=None,  # We'll handle Kafka publishing ourselves
            cache_dir="./e24_cache"
        )
    
    def convert_to_osint_article(self, crawler_article: CrawlerArticle) -> Article:
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
    
    def extract_comments(self, crawler_article: CrawlerArticle) -> List[Comment]:
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
    
    def process_article(self, crawler_article: CrawlerArticle) -> None:
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
    import argparse
    
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
        "--config", 
        type=str, 
        default=None, 
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Create integration
    integration = E24Integration(config_path=args.config)
    
    # Run integration
    integration.run(pages=args.pages, max_articles=args.max_articles)


if __name__ == "__main__":
    main()
