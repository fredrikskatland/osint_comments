# E24 Crawler

A web crawler for e24.no that identifies articles with comments, following clean architecture principles with separation of concerns.

## Features

- Crawls e24.no to find articles
- Identifies articles with comments
- Stores article data in a SQLite database
- Caches crawled URLs to avoid redundant processing
- Command-line interface for easy usage
- Integration with Kafka for publishing articles with comments

## Architecture

The crawler follows clean architecture principles with separation of concerns:

1. **Domain Layer**
   - `models.py`: Defines domain entities like `Article`

2. **Application Layer**
   - `crawler_service.py`: Orchestrates the crawling process

3. **Infrastructure Layer**
   - `web_scraper.py`: Handles HTTP requests and HTML parsing
   - `article_repository.py`: Stores article data in a SQLite database

4. **Interface Layer**
   - `cli.py`: Command-line interface for running the crawler
   - `__main__.py`: Entry point for running as a module
   - `integration.py`: Integration with the osint_comments project

## Installation

The E24 Crawler is part of the OSINT Comments project and uses Poetry for dependency management. To install:

1. Make sure you have Poetry installed
2. Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/osint_comments.git
cd osint_comments
poetry install
```

## Usage

### Command-line Interface

Run the crawler from the command line:

```bash
# Activate the Poetry environment
poetry shell

# Run with default settings (crawl 3 pages)
python -m crawler

# Crawl more pages
python -m crawler --pages 5

# Limit the number of articles to process
python -m crawler --max-articles 10

# Force recrawling of articles that have been crawled before
python -m crawler --force-recrawl

# List articles with comments from the database
python -m crawler --list-comments

# List recent articles from the database
python -m crawler --list-recent

# Enable verbose logging
python -m crawler --verbose
```

### API Usage

You can also use the crawler programmatically:

```python
from crawler.web_scraper import E24Scraper
from crawler.crawler_service import CrawlerService
from crawler.article_repository import ArticleRepository

# Create components
repository = ArticleRepository(db_path="articles.db")
scraper = E24Scraper()
crawler_service = CrawlerService(
    scraper=scraper,
    repository=repository,
    cache_dir="./cache"
)

# Run crawler
articles = crawler_service.crawl_recent_articles(pages=3)
articles_with_comments = crawler_service.process_articles(articles)

# Print results
for article in articles_with_comments:
    print(f"{article.title} - {article.url}")
    print(f"Comments: {article.comment_count}")
    print("-" * 50)
```

## Integration with OSINT Comments

The crawler can be integrated with the OSINT Comments project to analyze comments from e24.no:

```python
from crawler.crawler_service import CrawlerService
from osint_comments.kafka_producer import KafkaProducer

# Create Kafka producer
kafka_producer = KafkaProducer(bootstrap_servers="localhost:9092")

# Create crawler service with Kafka producer
crawler_service = CrawlerService(
    repository=repository,
    kafka_producer=kafka_producer
)

# Run crawler (articles with comments will be published to Kafka)
crawler_service.run_crawler(pages=3)
```

For a complete integration example, see the `osint_comments.e24_integration` module.

## Testing

Run the tests with pytest:

```bash
# Run all crawler tests
poetry run pytest crawler/

# Run a specific test file
poetry run pytest crawler/test_crawler.py
```

## Customization

You can customize the crawler by modifying the following:

- HTML selectors in `web_scraper.py` to match e24.no's structure
- Database schema in `article_repository.py`
- Crawling parameters in `crawler_service.py`

## Notes

- The crawler includes rate limiting to avoid overloading e24.no's servers
- The HTML selectors in `web_scraper.py` may need to be updated if e24.no changes its structure
