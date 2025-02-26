"""
Test script for the e24.no crawler.

This script provides a simple way to test the crawler functionality
without having to integrate it with the full osint_comments project.
"""
import logging
import sys
import os
import time
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.web_scraper import E24Scraper
from crawler.models import Article

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_get_article_list():
    """Test the get_article_list method of E24Scraper."""
    logger.info("Testing get_article_list method...")
    
    scraper = E24Scraper()
    articles = scraper.get_article_list(page=1)
    
    logger.info(f"Found {len(articles)} articles on page 1")
    
    if articles:
        logger.info("Sample articles:")
        for i, article in enumerate(articles[:5], 1):
            logger.info(f"{i}. {article.title} - {article.url}")
    else:
        logger.warning("No articles found. Check if the HTML selectors need to be updated.")
    
    return articles


def test_get_article_details(article_url: str):
    """
    Test the get_article_details method of E24Scraper.
    
    Args:
        article_url: URL of the article to test
    """
    logger.info(f"Testing get_article_details method for {article_url}...")
    
    scraper = E24Scraper()
    article = scraper.get_article_details(article_url)
    
    logger.info("Article details:")
    logger.info(f"Title: {article.title}")
    logger.info(f"Author: {article.author}")
    logger.info(f"Published date: {article.published_date}")
    logger.info(f"Has comments: {article.has_comments}")
    logger.info(f"Comment count: {article.comment_count}")
    
    if article.content:
        content_preview = article.content[:200] + "..." if len(article.content) > 200 else article.content
        logger.info(f"Content preview: {content_preview}")
    else:
        logger.warning("No content found. Check if the HTML selectors need to be updated.")
    
    return article


def test_check_for_comments(articles: List[Article]):
    """
    Test the check_for_comments functionality.
    
    Args:
        articles: List of articles to check for comments
    """
    logger.info("Testing check_for_comments functionality...")
    
    scraper = E24Scraper()
    articles_with_comments = []
    
    for i, article in enumerate(articles[:10], 1):  # Test first 10 articles
        logger.info(f"Checking article {i}/{min(10, len(articles))}: {article.title}")
        
        full_article = scraper.get_article_details(article.url)
        
        logger.info(f"Has comments: {full_article.has_comments}")
        logger.info(f"Comment count: {full_article.comment_count}")
        
        if full_article.has_comments:
            articles_with_comments.append(full_article)
        
        # Avoid overloading the server
        if i < min(10, len(articles)):
            time.sleep(1)
    
    logger.info(f"Found {len(articles_with_comments)} articles with comments out of {min(10, len(articles))} tested")
    
    if articles_with_comments:
        logger.info("Articles with comments:")
        for i, article in enumerate(articles_with_comments, 1):
            logger.info(f"{i}. {article.title} - {article.url}")
            logger.info(f"   Comment count: {article.comment_count}")
    
    return articles_with_comments


def main():
    """Main entry point for the test script."""
    logger.info("Starting e24.no crawler test")
    
    # Test get_article_list
    articles = test_get_article_list()
    
    if not articles:
        logger.error("No articles found. Aborting test.")
        return
    
    # Test get_article_details with the first article
    first_article = articles[0]
    test_get_article_details(first_article.url)
    
    # Test check_for_comments
    test_check_for_comments(articles)
    
    logger.info("Test completed")


if __name__ == "__main__":
    main()
