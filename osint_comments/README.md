# OSINT Comments Core

The core component of the OSINT Comments project, providing functionality for analyzing and processing comments from various online sources.

## Features

- Comment analysis using NLP techniques
- Storage of comments and articles in a database
- Processing pipeline using Kafka
- API client for interacting with external services

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

## Usage

### Running the Analysis Pipeline

```bash
# Run the main analysis pipeline
python -m osint_comments.main

# Run with custom configuration
python -m osint_comments.main --config config.json
```

### Integrating with E24 Crawler

The OSINT Comments Core can be integrated with the E24 Crawler to analyze comments from e24.no:

```bash
# Run the integration script
python -m osint_comments.e24_integration

# Specify number of pages to crawl
python -m osint_comments.e24_integration --pages 5
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
