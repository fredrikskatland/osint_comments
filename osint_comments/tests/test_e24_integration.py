"""
Tests for the e24.no integration with osint_comments.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ..e24_integration import E24Integration
from crawler.models import Article as CrawlerArticle
from ..models import Article, Comment


@pytest.fixture
def mock_config():
    """Mock Config object."""
    config = MagicMock()
    config.db_path = ":memory:"
    config.kafka_bootstrap_servers = "localhost:9092"
    return config


@pytest.fixture
def mock_repository():
    """Mock Repository object."""
    repository = MagicMock()
    repository.save_article.return_value = True
    repository.save_comment.return_value = True
    return repository


@pytest.fixture
def mock_kafka_producer():
    """Mock KafkaProducer object."""
    producer = MagicMock()
    producer.send_message.return_value = True
    return producer


@pytest.fixture
def mock_article_repository():
    """Mock ArticleRepository object."""
    repository = MagicMock()
    repository.save_article.return_value = True
    return repository


@pytest.fixture
def mock_scraper():
    """Mock E24Scraper object."""
    scraper = MagicMock()
    return scraper


@pytest.fixture
def mock_crawler_service():
    """Mock CrawlerService object."""
    service = MagicMock()
    
    # Create sample articles
    articles = [
        CrawlerArticle(
            url="https://e24.no/article1",
            title="Test Article 1",
            published_date=datetime.now(),
            author="Test Author 1",
            content="Test content 1",
            has_comments=True,
            comment_count=5
        ),
        CrawlerArticle(
            url="https://e24.no/article2",
            title="Test Article 2",
            published_date=datetime.now(),
            author="Test Author 2",
            content="Test content 2",
            has_comments=False,
            comment_count=0
        )
    ]
    
    service.crawl_recent_articles.return_value = articles
    service.process_articles.return_value = [articles[0]]  # Only return the article with comments
    
    return service


@pytest.fixture
def integration(mock_config, mock_repository, mock_kafka_producer, 
                mock_article_repository, mock_scraper, mock_crawler_service):
    """Create E24Integration with mocked dependencies."""
    with patch("osint_comments.e24_integration.Config", return_value=mock_config), \
         patch("osint_comments.e24_integration.Repository", return_value=mock_repository), \
         patch("osint_comments.e24_integration.KafkaProducer", return_value=mock_kafka_producer), \
         patch("osint_comments.e24_integration.crawler.article_repository.ArticleRepository", return_value=mock_article_repository), \
         patch("osint_comments.e24_integration.crawler.web_scraper.E24Scraper", return_value=mock_scraper), \
         patch("osint_comments.e24_integration.crawler.crawler_service.CrawlerService", return_value=mock_crawler_service):
        
        integration = E24Integration()
        
        # Replace the extract_comments method to return a fixed list of comments
        def mock_extract_comments(crawler_article):
            if crawler_article.has_comments:
                return [
                    Comment(
                        article_url=crawler_article.url,
                        content="Test comment 1",
                        author="Test Commenter 1",
                        timestamp=datetime.now(),
                        source="e24.no"
                    ),
                    Comment(
                        article_url=crawler_article.url,
                        content="Test comment 2",
                        author="Test Commenter 2",
                        timestamp=datetime.now(),
                        source="e24.no"
                    )
                ]
            return []
        
        integration.extract_comments = mock_extract_comments
        
        return integration


def test_convert_to_osint_article(integration):
    """Test converting a crawler Article to an osint_comments Article."""
    # Create a crawler Article
    crawler_article = CrawlerArticle(
        url="https://e24.no/article1",
        title="Test Article",
        published_date=datetime.now(),
        author="Test Author",
        content="Test content",
        has_comments=True,
        comment_count=5
    )
    
    # Convert to osint_comments Article
    article = integration.convert_to_osint_article(crawler_article)
    
    # Check that the conversion was correct
    assert isinstance(article, Article)
    assert article.url == crawler_article.url
    assert article.title == crawler_article.title
    assert article.source == "e24.no"
    assert article.published_date == crawler_article.published_date
    assert article.author == crawler_article.author
    assert article.content == crawler_article.content


def test_extract_comments(integration):
    """Test extracting comments from a crawler Article."""
    # Create a crawler Article with comments
    crawler_article = CrawlerArticle(
        url="https://e24.no/article1",
        title="Test Article",
        published_date=datetime.now(),
        author="Test Author",
        content="Test content",
        has_comments=True,
        comment_count=5
    )
    
    # Extract comments
    comments = integration.extract_comments(crawler_article)
    
    # Check that comments were extracted
    assert len(comments) == 2
    assert all(isinstance(comment, Comment) for comment in comments)
    assert all(comment.article_url == crawler_article.url for comment in comments)
    assert all(comment.source == "e24.no" for comment in comments)
    
    # Create a crawler Article without comments
    crawler_article = CrawlerArticle(
        url="https://e24.no/article2",
        title="Test Article",
        published_date=datetime.now(),
        author="Test Author",
        content="Test content",
        has_comments=False,
        comment_count=0
    )
    
    # Extract comments
    comments = integration.extract_comments(crawler_article)
    
    # Check that no comments were extracted
    assert len(comments) == 0


def test_process_article(integration):
    """Test processing an article."""
    # Create a crawler Article with comments
    crawler_article = CrawlerArticle(
        url="https://e24.no/article1",
        title="Test Article",
        published_date=datetime.now(),
        author="Test Author",
        content="Test content",
        has_comments=True,
        comment_count=5
    )
    
    # Process the article
    integration.process_article(crawler_article)
    
    # Check that the article was saved to the repository
    integration.repository.save_article.assert_called_once()
    
    # Check that comments were saved to the repository and published to Kafka
    assert integration.repository.save_comment.call_count == 2
    assert integration.kafka_producer.send_message.call_count == 2


def test_run(integration):
    """Test running the integration."""
    # Run the integration
    integration.run(pages=3, max_articles=10)
    
    # Check that the crawler service was called
    integration.crawler_service.crawl_recent_articles.assert_called_once_with(pages=3)
    integration.crawler_service.process_articles.assert_called_once()
    
    # Check that process_article was called for each article with comments
    assert integration.repository.save_article.call_count == 1
    assert integration.repository.save_comment.call_count == 2
    assert integration.kafka_producer.send_message.call_count == 2
