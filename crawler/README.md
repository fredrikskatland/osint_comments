# E24 Crawler

A web crawler for e24.no that identifies articles using the sitemap structure, following clean architecture principles with separation of concerns.

## Features

- Crawls e24.no sitemaps to find articles
- Supports crawling articles from multiple months
- Stores article data in a SQLite database
- Caches crawled URLs to avoid redundant processing
- Command-line interface for easy usage
- Integration with Kafka for publishing articles

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

# Run with default settings (crawl current month)
python -m crawler

# Crawl articles from the last 3 months
python -m crawler --months-back 3

# Limit the number of articles to process
python -m crawler --max-articles 50

# Force recrawling of articles that have been crawled before
python -m crawler --force-recrawl

# List recent articles from the database
python -m crawler --list-recent

# Enable verbose logging
python -m crawler --verbose
```

### Sitemap-based Crawling

The crawler uses the sitemap structure of e24.no to find articles:

```bash
# Crawl articles from the last 3 months
python -m crawler --months-back 3
```

This will:
1. Find the sitemaps for the current month and the previous 2 months
2. Extract article URLs from each sitemap
3. Process each article to get its details

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

# Crawl articles from the current month
articles = crawler_service.crawl_articles(months_back=1)
processed_articles = crawler_service.process_articles(articles)

# Crawl articles from the last 3 months with a limit
articles = crawler_service.crawl_articles(months_back=3, max_articles=50)
processed_articles = crawler_service.process_articles(articles)

# Print results
for article in processed_articles:
    print(f"{article.title} - {article.url}")
    print("-" * 50)
```

## Integration with OSINT Comments

The crawler is designed to work with the OSINT Comments project as part of a three-step pipeline:

1. **Crawl** (E24 Crawler): Collect articles from e24.no
2. **Gather** (OSINT Comments): Fetch comments for articles using the API
3. **Analyze** (OSINT Comments): Analyze comments for harmful content

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
