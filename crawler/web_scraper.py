"""
Web scraper for e24.no to extract articles and check for comments.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple, Set
import logging
from datetime import datetime
import re
from .models import Article

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class E24Scraper:
    """
    Scraper for e24.no to extract articles and check for comments.
    """
    BASE_URL = "https://e24.no"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,nb;q=0.8",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.visited_urls = set()  # Keep track of visited URLs to avoid duplicates
    
    def get_article_list(self, page: int = 1) -> List[Article]:
        """
        Fetch a list of articles from the main page or category pages.
        
        Args:
            page: Page number to fetch (for pagination)
            
        Returns:
            List of Article objects with basic information
        """
        url = f"{self.BASE_URL}"
        if page > 1:
            url = f"{url}/page/{page}"
        
        logger.info(f"Fetching article list from {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Based on the observed structure of e24.no
            # The articles appear to be in a grid layout with timestamps and titles
            
            # First, try to handle cookie consent if present
            cookie_button = soup.select_one('button:contains("Godta alle"), button:contains("Accept all")')
            if cookie_button:
                logger.info("Cookie consent dialog detected. In a real scenario, we would need to handle this.")
            
            # Find all article elements - looking for various possible selectors
            article_elements = []
            
            # Try different selectors that might contain articles
            for selector in [
                'article', 
                '.article', 
                '.article-teaser', 
                '.teaser', 
                '.news-item',
                'a[href^="/"]',  # Links that start with / (relative URLs)
                'a[href*="/naeringsliv/"]',  # Links containing /naeringsliv/
                'a[href*="/finans/"]',  # Links containing /finans/
                'a[href*="/boers/"]',  # Links containing /boers/
                '.frontpage-teaser',
                '[class*="article"]',  # Any element with "article" in its class
                '[class*="teaser"]',   # Any element with "teaser" in its class
            ]:
                elements = soup.select(selector)
                if elements:
                    article_elements.extend(elements)
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
            
            # Remove duplicates (in case the same element was selected multiple times)
            article_elements = list(set(article_elements))
            logger.info(f"Found {len(article_elements)} potential article elements")
            
            # Process each article element
            articles = []
            for article_elem in article_elements:
                try:
                    # If the element is a link itself
                    if article_elem.name == 'a':
                        link_elem = article_elem
                    else:
                        # Look for links in the element
                        link_elem = article_elem.select_one('a')
                    
                    if not link_elem:
                        continue
                    
                    # Get the URL
                    article_url = link_elem.get('href')
                    if not article_url:
                        continue
                    
                    # Make sure it's an absolute URL
                    if not article_url.startswith('http'):
                        article_url = f"{self.BASE_URL}{article_url}"
                    
                    # Skip non-article URLs
                    if '/tag/' in article_url or '/topic/' in article_url or '/author/' in article_url:
                        continue
                    
                    # Extract title
                    # First try to find a heading element
                    title_elem = article_elem.select_one('h1, h2, h3, h4')
                    
                    # If no heading, try to use the link text
                    if not title_elem:
                        title = link_elem.text.strip()
                    else:
                        title = title_elem.text.strip()
                    
                    # Skip if no title
                    if not title:
                        continue
                    
                    # Create Article object with basic information
                    article = Article(
                        url=article_url,
                        title=title
                    )
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error extracting article data: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} articles on page {page}")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Error fetching article list: {e}")
            return []
    
    def get_article_details(self, article_url: str) -> Article:
        """
        Fetch the full details of an article including checking for comments.
        
        Args:
            article_url: URL of the article to fetch
            
        Returns:
            Article object with full details
        """
        logger.info(f"Fetching article details from {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one('h1, .article-title')
            title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Extract author
            author_elem = soup.select_one('.author-name, .byline, .article-author')
            author = None
            if author_elem:
                author_text = author_elem.text.strip()
                # Often author text includes "Av " or similar prefix
                author_match = re.search(r'(?:Av|By)\s+(.+?)(?:\s*\||\s*$)', author_text, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                else:
                    author = author_text
            
            # Extract published date
            date_elem = soup.select_one('.published-date, time, .article-date, .article-timestamp')
            published_date = None
            if date_elem:
                # Try to get datetime from time element's datetime attribute
                datetime_attr = date_elem.get('datetime')
                if datetime_attr:
                    try:
                        published_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except ValueError:
                        logger.warning(f"Could not parse datetime attribute: {datetime_attr}")
                
                # If that fails, try to parse the text content
                if not published_date:
                    date_text = date_elem.text.strip()
                    # Try common Norwegian date formats
                    date_formats = [
                        '%d.%m.%Y %H:%M',  # 25.02.2025 22:15
                        '%d.%m.%Y',        # 25.02.2025
                        '%H:%M %d.%m.%Y',  # 22:15 25.02.2025
                        '%d. %B %Y',       # 25. februar 2025
                        '%d. %b %Y'        # 25. feb 2025
                    ]
                    
                    for date_format in date_formats:
                        try:
                            published_date = datetime.strptime(date_text, date_format)
                            break
                        except ValueError:
                            continue
                    
                    if not published_date:
                        logger.warning(f"Could not parse date: {date_text}")
            
            # Extract content - try multiple selectors to find the article content
            content = None
            content_selectors = [
                'article .content', 
                '.article-body', 
                '.article-text', 
                '.article-content',
                'article p',  # Paragraphs within article
                '.article p',  # Paragraphs within article class
                'main p',      # Paragraphs within main
                '.main-content p',  # Paragraphs within main content
                '.article-container p',  # Paragraphs within article container
                '[class*="article"] p',  # Paragraphs within any element with "article" in class
                '[class*="content"] p',  # Paragraphs within any element with "content" in class
            ]
            
            # Try each selector until we find content
            for selector in content_selectors:
                content_elems = soup.select(selector)
                if content_elems:
                    # Remove unwanted elements like ads, related articles, etc.
                    for content_elem in content_elems:
                        for unwanted in content_elem.select('.ad, .advertisement, .related-articles, .article-recommendations'):
                            unwanted.decompose()
                    
                    # Combine text from all matching elements
                    content = ' '.join([elem.text.strip() for elem in content_elems if elem.text.strip()])
                    if content:
                        break
            
            # If still no content, try to get all text from the main content area
            if not content:
                main_content = soup.select_one('main, article, .article, .content, [role="main"]')
                if main_content:
                    # Remove unwanted elements
                    for unwanted in main_content.select('header, footer, nav, aside, .ad, .advertisement, .related-articles, script, style'):
                        unwanted.decompose()
                    
                    content = main_content.text.strip()
            
            # Check for comments
            has_comments, comment_count = self.check_for_comments(soup)
            
            # Create and return Article object
            article = Article(
                url=article_url,
                title=title,
                published_date=published_date,
                author=author,
                content=content,
                has_comments=has_comments,
                comment_count=comment_count
            )
            
            return article
            
        except requests.RequestException as e:
            logger.error(f"Error fetching article details: {e}")
            return Article(url=article_url, title="Error fetching article")
    
    def check_for_comments(self, soup: BeautifulSoup) -> Tuple[bool, Optional[int]]:
        """
        This method is deprecated and will always return (False, None).
        The comment checking is now done in the gather step using the API.
        
        Args:
            soup: BeautifulSoup object of the article page
            
        Returns:
            Tuple of (has_comments, comment_count)
        """
        # In the new approach, we don't check for comments in the crawler
        # This is now done in the gather step using the API
        return False, None
    
    def get_related_articles(self, article_url: str, max_related: int = 3) -> List[Article]:
        """
        Find related articles from an article page.
        
        Args:
            article_url: URL of the article to find related articles from
            max_related: Maximum number of related articles to return
            
        Returns:
            List of Article objects for related articles
        """
        logger.info(f"Finding related articles from {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            related_articles = []
            
            # Look for related articles sections
            related_selectors = [
                '.related-articles', 
                '.article-recommendations', 
                '.recommended-articles',
                '.more-articles',
                '.read-more',
                '.similar-articles',
                '[class*="related"]',
                '[class*="recommendation"]',
                'aside',
                '.sidebar'
            ]
            
            related_sections = []
            for selector in related_selectors:
                sections = soup.select(selector)
                if sections:
                    related_sections.extend(sections)
            
            # If no specific related sections found, look for links in the article
            if not related_sections:
                article_content = soup.select_one('article, .article, .article-content, main')
                if article_content:
                    related_sections = [article_content]
            
            # Extract links from related sections
            for section in related_sections:
                links = section.select('a[href]')
                for link in links:
                    try:
                        # Get the URL
                        related_url = link.get('href')
                        if not related_url:
                            continue
                        
                        # Make sure it's an absolute URL
                        if not related_url.startswith('http'):
                            related_url = f"{self.BASE_URL}{related_url}"
                        
                        # Skip non-article URLs
                        if '/tag/' in related_url or '/topic/' in related_url or '/author/' in related_url:
                            continue
                        
                        # Skip if already in the list
                        if any(article.url == related_url for article in related_articles):
                            continue
                        
                        # Extract title
                        title_elem = link.select_one('h1, h2, h3, h4')
                        if title_elem:
                            title = title_elem.text.strip()
                        else:
                            title = link.text.strip()
                        
                        # Skip if no title
                        if not title:
                            continue
                        
                        # Create Article object with basic information
                        article = Article(
                            url=related_url,
                            title=title
                        )
                        related_articles.append(article)
                        
                        # Stop if we have enough related articles
                        if len(related_articles) >= max_related:
                            break
                    
                    except Exception as e:
                        logger.error(f"Error extracting related article data: {e}")
                        continue
                
                # Stop if we have enough related articles
                if len(related_articles) >= max_related:
                    break
            
            logger.info(f"Found {len(related_articles)} related articles from {article_url}")
            return related_articles
            
        except requests.RequestException as e:
            logger.error(f"Error fetching related articles: {e}")
            return []
    
    def crawl_with_depth(self, start_urls: List[str], max_related: int = 3, depth: int = 2) -> List[Article]:
        """
        Crawl articles starting from a list of URLs, following related articles up to a certain depth.
        
        Args:
            start_urls: List of URLs to start crawling from
            max_related: Maximum number of related articles to follow from each article
            depth: Maximum depth to crawl (1 = only start_urls, 2 = start_urls + related, etc.)
            
        Returns:
            List of Article objects
        """
        logger.info(f"Starting depth crawl with {len(start_urls)} start URLs, max_related={max_related}, depth={depth}")
        
        all_articles = []
        to_visit = [(url, 1) for url in start_urls]  # (url, current_depth)
        
        while to_visit:
            url, current_depth = to_visit.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Get article details
            article = self.get_article_details(url)
            all_articles.append(article)
            
            # If we haven't reached max depth, get related articles
            if current_depth < depth:
                related_articles = self.get_related_articles(url, max_related)
                
                # Add related articles to visit queue
                for related in related_articles:
                    if related.url not in self.visited_urls:
                        to_visit.append((related.url, current_depth + 1))
            
            # Avoid overloading the server
            import time
            time.sleep(1)  # 1-second delay between requests
        
        logger.info(f"Depth crawl complete, found {len(all_articles)} articles")
        return all_articles
