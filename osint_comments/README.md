# OSINT Comments Core

The core component of the OSINT Comments project, providing functionality for gathering, analyzing, and processing comments from various online sources.

## Features

- Gathering comments using API clients
- Comment analysis using NLP techniques
- Storage of comments and articles in a database
- Processing pipeline using Kafka
- Integration with the E24 Crawler

## Architecture

The OSINT Comments Core follows clean architecture principles:

1. **Domain Layer**
   - `models.py`: Defines domain entities like `Article` and `Comment`
   - `analysis_models.py`: Defines models for analysis results

2. **Application Layer**
   - `analyzer_service.py`: Orchestrates the analysis process
   - `comment_analyzer.py`: Analyzes comments using NLP techniques

3. **Infrastructure Layer**
   - `repository.py`: Stores articles and comments in a database
   - `kafka_consumer.py`: Consumes messages from Kafka
   - `kafka_producer.py`: Produces messages to Kafka
   - `llm_client.py`: Client for interacting with language models
   - `api_client.py`: Client for interacting with external APIs

4. **Interface Layer**
   - `main.py`: Entry point for running the application
   - `e24_integration.py`: Integration with the E24 Crawler

## Usage

### Running the Pipeline

The OSINT Comments Core implements a three-step pipeline:

1. **Crawl**: Collect articles from e24.no using the sitemap structure
2. **Gather**: Fetch comments for articles using the API
3. **Analyze**: Analyze comments for harmful content

You can run each step individually or the full pipeline:

```bash
# Run the full pipeline with default settings
poetry run python -m osint_comments.e24_integration pipeline

# Run individual steps
poetry run python -m osint_comments.e24_integration crawl
poetry run python -m osint_comments.e24_integration gather
poetry run python -m osint_comments.e24_integration analyze

# Show statistics about articles and comments
poetry run python -m osint_comments.e24_integration stats
```

### Step 1: Crawling Articles

The crawler uses the sitemap structure of e24.no to find articles. By default, it crawls the current month's articles.

```bash
# Crawl articles from the current month
poetry run python -m osint_comments.e24_integration crawl

# Crawl articles from the last 3 months
poetry run python -m osint_comments.e24_integration crawl --months-back 3

# Limit to 50 articles
poetry run python -m osint_comments.e24_integration crawl --max-articles 50

# Process article content (extract full text)
poetry run python -m osint_comments.e24_integration crawl --process-content
```

### Step 2: Gathering Comments

After crawling articles, you can gather comments for them:

```bash
# Gather comments for all articles that haven't had comments gathered yet
poetry run python -m osint_comments.e24_integration gather

# Gather comments for a specific article by ID
poetry run python -m osint_comments.e24_integration gather --article-id QM2mxR

# Limit the number of articles to process
poetry run python -m osint_comments.e24_integration gather --limit 20

# Publish comments to Kafka as they're gathered
poetry run python -m osint_comments.e24_integration gather --publish-to-kafka --kafka-servers localhost:9092
```

### Step 3: Analyzing Comments

Finally, analyze the gathered comments:

```bash
# Analyze all comments that haven't been analyzed yet
poetry run python -m osint_comments.e24_integration analyze

# Analyze comments for a specific article
poetry run python -m osint_comments.e24_integration analyze --article-id QM2mxR

# Limit the number of comments to analyze
poetry run python -m osint_comments.e24_integration analyze --limit 100

# Publish flagged comments to Kafka
poetry run python -m osint_comments.e24_integration analyze --publish-to-kafka --kafka-servers localhost:9092
```

### Running the Full Pipeline

You can run the complete pipeline with a single command:

```bash
# Run the full pipeline with default settings
poetry run python -m osint_comments.e24_integration pipeline

# Run the pipeline with custom settings
poetry run python -m osint_comments.e24_integration pipeline --months-back 3 --max-articles 100 --limit 50 --publish-to-kafka --kafka-servers localhost:9092
```

This will:
1. Crawl articles from the specified months (default: current month)
2. Gather comments for those articles
3. Analyze the comments for harmful content

### Running the Analysis Pipeline Directly

You can also run the analysis pipeline directly:

```bash
# Run the main analysis pipeline
python -m osint_comments.main

# Run with custom configuration
python -m osint_comments.main --config config.json
```

## Configuration

The OSINT Comments Core can be configured using environment variables or a configuration file:

- `KAFKA_BOOTSTRAP_SERVERS`: Comma-separated list of Kafka bootstrap servers
- `KAFKA_TOPIC`: Kafka topic for consuming comments
- `DB_PATH`: Path to the SQLite database file
- `API_KEY`: API key for external services
- `LLM_MODEL`: Language model to use for analysis

## Testing

Run the tests with pytest:

```bash
# Run all tests
poetry run pytest osint_comments/tests/

# Run specific test modules
poetry run pytest osint_comments/tests/test_analyzer_service.py
```

## Extending

The OSINT Comments Core is designed to be extensible:

- Add new analysis techniques in `comment_analyzer.py`
- Add new data sources by creating new integration modules
- Add new storage backends by extending the repository

## Integration with E24 Crawler

The OSINT Comments Core is designed to work with the E24 Crawler as part of a three-step pipeline:

1. **Crawl** (E24 Crawler): Collect articles from e24.no
2. **Gather** (OSINT Comments): Fetch comments for articles using the API
3. **Analyze** (OSINT Comments): Analyze comments for harmful content

The `e24_integration.py` module provides a unified interface for running this pipeline.
