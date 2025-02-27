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

1. **Crawl**: Collect articles from e24.no (using the E24 Crawler)
2. **Gather**: Fetch comments for articles using the API
3. **Analyze**: Analyze comments for harmful content

You can run each step individually or the full pipeline:

```bash
# Run the full pipeline
poetry run python -m osint_comments.e24_integration pipeline

# Run individual steps
poetry run python -m osint_comments.e24_integration crawl
poetry run python -m osint_comments.e24_integration gather
poetry run python -m osint_comments.e24_integration analyze

# Show statistics
poetry run python -m osint_comments.e24_integration stats
```

### Advanced Options

```bash
# Crawl with depth (follow related articles)
poetry run python -m osint_comments.e24_integration crawl --crawl-method depth --related-articles 3 --depth 2

# Gather comments for a specific article
poetry run python -m osint_comments.e24_integration gather --article-id article:e24:example-article

# Analyze comments with Kafka integration
poetry run python -m osint_comments.e24_integration analyze --publish-to-kafka --kafka-servers localhost:9092

# Run the full pipeline with all options
poetry run python -m osint_comments.e24_integration pipeline --pages 5 --crawl-method depth --related-articles 3 --depth 2 --publish-to-kafka --kafka-servers localhost:9092
```

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
