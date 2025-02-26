"""
Command-line interface for the e24.no crawler.
"""
import argparse
import logging
import sys
import os
from typing import List, Optional
from datetime import datetime

from .web_scraper import E24Scraper
from .crawler_service import CrawlerService
from .article_repository import ArticleRepository
from .models import Article

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crawler.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(description="Crawl e24.no for articles with comments")
    
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
        "--force-recrawl", 
        action="store_true", 
        help="Force recrawling of articles that have been crawled before"
    )
    
    parser.add_argument(
        "--list-comments", 
        action="store_true", 
        help="List articles with comments from the database"
    )
    
    parser.add_argument(
        "--list-recent", 
        action="store_true", 
        help="List recent articles from the database"
    )
    
    parser.add_argument(
        "--limit", 
        type=int, 
        default=10, 
        help="Limit for listing articles (default: 10)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    return parser


def print_articles(articles: List[Article], show_content: bool = False):
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
        
        if show_content and article.content:
            print(f"   Content: {article.content[:200]}...")
        
        print("-" * 80)


def main():
    """Main entry point for the CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create repository
    repository = ArticleRepository(db_path=args.db_path)
    
    # Handle listing commands
    if args.list_comments:
        articles = repository.get_articles_with_comments(limit=args.limit)
        print_articles(articles)
        return
    
    if args.list_recent:
        articles = repository.get_recent_articles(limit=args.limit)
        print_articles(articles)
        return
    
    # Create scraper and crawler service
    scraper = E24Scraper()
    crawler_service = CrawlerService(
        scraper=scraper,
        repository=repository,
        cache_dir=args.cache_dir
    )
    
    # Run crawler
    logger.info(f"Starting crawler with {args.pages} pages")
    articles = crawler_service.crawl_recent_articles(
        pages=args.pages,
        force_recrawl=args.force_recrawl
    )
    
    logger.info(f"Processing {len(articles)} articles")
    articles_with_comments = crawler_service.process_articles(
        articles=articles,
        max_articles=args.max_articles,
        publish_to_kafka=False  # No Kafka integration in CLI mode
    )
    
    # Print results
    logger.info(f"Found {len(articles_with_comments)} articles with comments")
    print_articles(articles_with_comments)


if __name__ == "__main__":
    main()
