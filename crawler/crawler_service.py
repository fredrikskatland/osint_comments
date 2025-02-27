"""
Service for crawling e24.no and processing articles.
"""
import logging
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from .web_scraper import E24Scraper
from .models import Article

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Service for crawling e24.no and processing articles.
    """
    
    def __init__(self, scraper: Optional[E24Scraper] = None, 
                 kafka_producer=None, 
                 repository=None,
                 cache_dir: str = "./cache"):
        """
        Initialize the crawler service.
        
        Args:
            scraper: E24Scraper instance (will create one if not provided)
            kafka_producer: Optional Kafka producer for publishing articles
            repository: Optional repository for storing articles
            cache_dir: Directory for caching crawled articles
        """
        self.scraper = scraper or E24Scraper()
        self.kafka_producer = kafka_producer
        self.repository = repository
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load cache of previously crawled articles
        self.crawled_urls = self._load_crawled_urls()
    
    def _load_crawled_urls(self) -> Dict[str, datetime]:
        """
        Load cache of previously crawled URLs.
        
        Returns:
            Dictionary mapping URLs to last crawl time
        """
        cache_file = os.path.join(self.cache_dir, "crawled_urls.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string dates back to datetime objects
                    return {url: datetime.fromisoformat(date) for url, date in data.items()}
            except Exception as e:
                logger.error(f"Error loading crawled URLs cache: {e}")
        
        return {}
    
    def _save_crawled_urls(self):
        """Save cache of crawled URLs to disk."""
        cache_file = os.path.join(self.cache_dir, "crawled_urls.json")
        try:
            # Convert datetime objects to ISO format strings
            data = {url: dt.isoformat() for url, dt in self.crawled_urls.items()}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving crawled URLs cache: {e}")
    
    def crawl_recent_articles(self, pages: int = 5, force_recrawl: bool = False) -> List[Article]:
        """
        Crawl recent articles from e24.no.
        
        Args:
            pages: Number of pages to crawl
            force_recrawl: Whether to recrawl articles that have been crawled before
            
        Returns:
            List of Article objects
        """
        logger.info(f"Starting crawl of {pages} pages from e24.no")
        all_articles = []
        
        for page in range(1, pages + 1):
            articles = self.scraper.get_article_list(page)
            all_articles.extend(articles)
            
            # Avoid overloading the server
            if page < pages:
                import time
                time.sleep(2)  # 2-second delay between page requests
        
        logger.info(f"Found {len(all_articles)} articles across {pages} pages")
        return all_articles
    
    def crawl_with_depth(self, pages: int = 1, max_related: int = 3, depth: int = 2, 
                         force_recrawl: bool = False) -> List[Article]:
        """
        Crawl articles from e24.no with depth, following related articles.
        
        Args:
            pages: Number of front pages to crawl for initial articles
            max_related: Maximum number of related articles to follow from each article
            depth: Maximum depth to crawl (1 = only start_urls, 2 = start_urls + related, etc.)
            force_recrawl: Whether to recrawl articles that have been crawled before
            
        Returns:
            List of Article objects
        """
        logger.info(f"Starting depth crawl with pages={pages}, max_related={max_related}, depth={depth}")
        
        # First, get articles from the front page(s)
        start_articles = self.crawl_recent_articles(pages=pages, force_recrawl=force_recrawl)
        start_urls = [article.url for article in start_articles]
        
        # Then, crawl with depth
        all_articles = self.scraper.crawl_with_depth(start_urls, max_related=max_related, depth=depth)
        
        # Update crawled URLs cache
        now = datetime.now()
        for article in all_articles:
            self.crawled_urls[article.url] = now
        
        # Save updated crawled URLs cache
        self._save_crawled_urls()
        
        logger.info(f"Depth crawl complete, found {len(all_articles)} articles")
        return all_articles
    
    def process_article_content(self, article: Article) -> Article:
        """
        Process an article to get its full content.
        In the new approach, we don't check for comments in the crawler.
        
        Args:
            article: Article to process
            
        Returns:
            Article with full content
        """
        if not article.content:
            logger.info(f"Processing article content: {article.title}")
            full_article = self.scraper.get_article_details(article.url)
            
            # Update article with full content
            article.content = full_article.content
            article.published_date = full_article.published_date
            article.author = full_article.author
            
            # In the new approach, we don't check for comments in the crawler
            # This is now done in the gather step using the API
            article.has_comments = False
            article.comment_count = 0
        
        return article
    
    def process_articles(self, articles: List[Article], 
                         max_articles: Optional[int] = None,
                         publish_to_kafka: bool = True) -> List[Article]:
        """
        Process articles to get full content and save to repository.
        In the new approach, we don't check for comments in the crawler.
        
        Args:
            articles: List of articles to process
            max_articles: Maximum number of articles to process (None for all)
            publish_to_kafka: Whether to publish articles to Kafka
            
        Returns:
            List of processed articles
        """
        processed_articles = []
        now = datetime.now()
        
        # Limit the number of articles if specified
        if max_articles is not None:
            articles = articles[:max_articles]
        
        logger.info(f"Processing {len(articles)} articles")
        
        for i, article in enumerate(articles):
            # Skip if already crawled recently (unless force_recrawl is True)
            if article.url in self.crawled_urls:
                logger.debug(f"Skipping already crawled article: {article.url}")
                continue
            
            logger.info(f"Processing article {i+1}/{len(articles)}: {article.title}")
            
            # Get full article details if needed
            if not article.content:
                full_article = self.scraper.get_article_details(article.url)
                
                # Update article with full details
                article.content = full_article.content
                article.published_date = full_article.published_date
                article.author = full_article.author
                
                # In the new approach, we don't check for comments in the crawler
                # This is now done in the gather step using the API
                article.has_comments = False
                article.comment_count = 0
            
            # Update crawled URLs cache
            self.crawled_urls[article.url] = now
            
            # Save to repository if available
            if self.repository:
                try:
                    self.repository.save_article(article)
                    logger.debug(f"Saved article to repository: {article.title}")
                except Exception as e:
                    logger.error(f"Error saving article to repository: {e}")
            
            processed_articles.append(article)
            
            # Publish to Kafka if enabled
            if publish_to_kafka and self.kafka_producer:
                try:
                    self.kafka_producer.send_message("articles", article.to_dict())
                    logger.debug(f"Published article to Kafka: {article.title}")
                except Exception as e:
                    logger.error(f"Error publishing article to Kafka: {e}")
            
            # Avoid overloading the server
            if i < len(articles) - 1:
                import time
                time.sleep(1)  # 1-second delay between article requests
        
        # Save updated crawled URLs cache
        self._save_crawled_urls()
        
        logger.info(f"Processed {len(processed_articles)} articles")
        return processed_articles
    
    def run_crawler(self, pages: int = 5, max_articles: Optional[int] = None) -> List[Article]:
        """
        Run the complete crawling process.
        
        Args:
            pages: Number of pages to crawl
            max_articles: Maximum number of articles to process (None for all)
            
        Returns:
            List of processed articles
        """
        articles = self.crawl_recent_articles(pages)
        return self.process_articles(articles, max_articles)
    
    def run_depth_crawler(self, pages: int = 1, max_related: int = 3, depth: int = 2, 
                          max_articles: Optional[int] = None) -> List[Article]:
        """
        Run the complete depth crawling process.
        
        Args:
            pages: Number of front pages to crawl for initial articles
            max_related: Maximum number of related articles to follow from each article
            depth: Maximum depth to crawl (1 = only start_urls, 2 = start_urls + related, etc.)
            max_articles: Maximum number of articles to process (None for all)
            
        Returns:
            List of processed articles
        """
        articles = self.crawl_with_depth(pages=pages, max_related=max_related, depth=depth)
        return self.process_articles(articles, max_articles)
