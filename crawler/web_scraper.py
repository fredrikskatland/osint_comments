"""
Web scraper for e24.no to extract articles using the sitemap structure.
"""
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import re
from .models import Article

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class E24Scraper:
    """
    Scraper for e24.no to extract articles using the sitemap structure.
    """
    BASE_URL = "https://e24.no"
    SITEMAP_URL_TEMPLATE = "https://e24.no/sitemaps/{year}-{month:02d}-articles.xml"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,nb;q=0.8",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_articles_from_sitemap(self, year: Optional[int] = None, month: Optional[int] = None) -> List[Article]:
        """
        Fetch articles from the sitemap for a specific year and month.
        If year and month are not provided, the current year and month are used.
        
        Args:
            year: Year to fetch articles for (default: current year)
            month: Month to fetch articles for (default: current month)
            
        Returns:
            List of Article objects with basic information
        """
        # Use current year and month if not provided
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        sitemap_url = self.SITEMAP_URL_TEMPLATE.format(year=year, month=month)
        logger.info(f"Fetching articles from sitemap: {sitemap_url}")
        
        try:
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            # Parse the XML sitemap
            root = ET.fromstring(response.content)
            
            # Extract namespace if present
            ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
            url_tag = 'ns:url' if ns else 'url'
            loc_tag = 'ns:loc' if ns else 'loc'
            
            articles = []
            
            # Extract article URLs from the sitemap
            for url_elem in root.findall(url_tag, ns):
                loc_elem = url_elem.find(loc_tag, ns)
                if loc_elem is not None:
                    article_url = loc_elem.text
                    
                    # Extract article identifier from URL
                    article_id_match = re.search(r'/i/([a-zA-Z0-9]+)/?', article_url)
                    if article_id_match:
                        article_id = article_id_match.group(1)
                        
                        # Create Article object with basic information
                        article = Article(
                            url=article_url,
                            title="",  # Title will be filled in when getting article details
                            identifier=article_id
                        )
                        articles.append(article)
            
            logger.info(f"Found {len(articles)} articles in sitemap for {year}-{month:02d}")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Error fetching sitemap: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap XML: {e}")
            return []
    
    def get_articles_from_recent_sitemaps(self, months_back: int = 1) -> List[Article]:
        """
        Fetch articles from the sitemaps for recent months.
        
        Args:
            months_back: Number of months to go back from the current month
            
        Returns:
            List of Article objects with basic information
        """
        now = datetime.now()
        all_articles = []
        
        # Get articles for the current month and previous months
        for i in range(months_back):
            date = now - timedelta(days=30 * i)
            year = date.year
            month = date.month
            
            articles = self.get_articles_from_sitemap(year, month)
            all_articles.extend(articles)
            
            # Avoid overloading the server
            if i < months_back - 1:
                import time
                time.sleep(1)  # 1-second delay between requests
        
        return all_articles
    
    def get_article_details(self, article_url: str) -> Article:
        """
        Fetch the full details of an article.
        
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
            
            # Extract article identifier from URL
            article_id = None
            article_id_match = re.search(r'/i/([a-zA-Z0-9]+)/?', article_url)
            if article_id_match:
                article_id = article_id_match.group(1)
            
            # Create and return Article object
            article = Article(
                url=article_url,
                title=title,
                published_date=published_date,
                author=author,
                content=content,
                has_comments=False,  # Comments are checked in the gather step using the API
                comment_count=0,     # Comments are checked in the gather step using the API
                identifier=article_id
            )
            
            return article
            
        except requests.RequestException as e:
            logger.error(f"Error fetching article details: {e}")
            return Article(url=article_url, title="Error fetching article")
    
    def process_articles(self, articles: List[Article], max_articles: Optional[int] = None) -> List[Article]:
        """
        Process a list of articles to get their full details.
        
        Args:
            articles: List of articles to process
            max_articles: Maximum number of articles to process (None for all)
            
        Returns:
            List of processed articles with full details
        """
        processed_articles = []
        
        # Limit the number of articles if specified
        if max_articles is not None:
            articles = articles[:max_articles]
        
        logger.info(f"Processing {len(articles)} articles")
        
        for i, article in enumerate(articles):
            logger.info(f"Processing article {i+1}/{len(articles)}: {article.url}")
            
            # Get full article details
            full_article = self.get_article_details(article.url)
            processed_articles.append(full_article)
            
            # Avoid overloading the server
            if i < len(articles) - 1:
                import time
                time.sleep(1)  # 1-second delay between requests
        
        logger.info(f"Processed {len(processed_articles)} articles")
        return processed_articles
    
    def crawl_articles(self, months_back: int = 1, max_articles: Optional[int] = None) -> List[Article]:
        """
        Crawl articles from recent sitemaps and process them.
        
        Args:
            months_back: Number of months to go back from the current month
            max_articles: Maximum number of articles to process (None for all)
            
        Returns:
            List of processed articles with full details
        """
        # Get articles from recent sitemaps
        articles = self.get_articles_from_recent_sitemaps(months_back)
        
        # Process articles to get full details
        return self.process_articles(articles, max_articles)
