# OSINT Comments

A Python application for collecting, storing, and processing comments from online articles for Open Source Intelligence (OSINT) purposes. This tool fetches comments from the E24 publication API, stores them in a local database, and publishes them to Kafka for further processing. It also includes an LLM-based analysis component that evaluates comments for harmful content and publishes the results to a separate Kafka topic.

## Features

- Fetch comments from E24 publication API
- Store comments, users, and article data in a SQLite database
- Publish raw comments to Kafka for downstream processing
- Analyze comments for aggressive, hateful, and racist content using OpenAI's GPT-4o-mini
- Publish analysis results to a separate Kafka topic
- Configurable request parameters (limit, offset, ordering)
- Proxy and User-Agent rotation to avoid rate limiting
- Clean architecture with separation of concerns

## Project Structure

```
osint_comments/
├── docker-compose.yml      # Docker setup for Kafka and Zookeeper
├── Dockerfile.analyzer     # Dockerfile for the analyzer service
├── poetry.lock             # Poetry lock file
├── pyproject.toml          # Poetry project configuration
├── README.md               # This file
└── osint_comments/         # Main package
    ├── analysis_models.py  # Pydantic models for analysis results
    ├── analyzer_service.py # Main service for analyzing comments
    ├── api_client.py       # API client for fetching comments
    ├── comment_analyzer.py # Core logic for analyzing comments
    ├── config.py           # Configuration settings
    ├── kafka_consumer.py   # Kafka consumer for reading comments
    ├── kafka_producer.py   # Kafka producer for publishing comments
    ├── llm_client.py       # OpenAI client for analyzing comments
    ├── main.py             # Main entry point for fetching comments
    ├── models.py           # SQLAlchemy models
    ├── repository.py       # Data access layer
    └── tests/              # Test directory
        ├── conftest.py     # Pytest configuration
        ├── test_api_client.py    # API client tests
        ├── test_comment_analyzer.py  # Comment analyzer tests
        └── test_repository.py    # Repository tests
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (dependency management)
- Docker and Docker Compose (for Kafka)
- OpenAI API key (for the comment analyzer)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd osint-comments
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

4. Start Kafka, Zookeeper, and the analyzer service using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Usage

### Fetching Comments

Run the application with an article identifier to fetch comments:

```bash
poetry run python osint_comments/main.py <article_identifier>
```

Where `<article_identifier>` is in the format `article:e24:Jbwa97`.

Example:

```bash
poetry run python osint_comments/main.py article:e24:Jbwa97
```

This will:
1. Fetch comments for the specified article from the E24 API
2. Store the article, users, and comments in the SQLite database
3. Publish the raw comments to the Kafka topic "raw-comments"

### Analyzing Comments

The comment analyzer service consumes messages from the "raw-comments" Kafka topic, analyzes them using OpenAI's GPT-4o-mini, and publishes the results to the "flagged-comments" Kafka topic.

To run the analyzer service manually:

```bash
export OPENAI_API_KEY=your_api_key_here
poetry run python -m osint_comments.analyzer_service
```

Alternatively, you can specify a maximum number of messages to process:

```bash
poetry run python -m osint_comments.analyzer_service 10  # Process up to 10 messages
```

## Configuration

### API Configuration

Configuration settings for the API client are stored in `config.py`:

- `API_BASE_URL`: Base URL for the comments API
- `COMMENTS_ENDPOINT_TEMPLATE`: Endpoint template for fetching comments
- `DEFAULT_LIMIT`: Default number of comments to fetch (default: 100)
- `DEFAULT_OFFSET`: Default offset for pagination (default: 0)
- `DEFAULT_ORDER`: Default ordering of comments (default: "score DESC")
- `DEFAULT_REPLIES`: Default ordering of replies (default: "ASC")

In `api_client.py`, you can configure:

- `USER_AGENTS`: List of User-Agent strings to rotate through
- `PROXIES`: List of proxy servers to use (if needed)

### Analyzer Configuration

Configuration settings for the comment analyzer are also stored in `config.py`:

- `OPENAI_API_KEY`: Your OpenAI API key (set as an environment variable)
- `OPENAI_MODEL`: The OpenAI model to use (default: "gpt-4o-mini")
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers (default: ["localhost:9092"])
- `RAW_COMMENTS_TOPIC`: Kafka topic for raw comments (default: "raw-comments")
- `FLAGGED_COMMENTS_TOPIC`: Kafka topic for flagged comments (default: "flagged-comments")
- `ANALYSIS_THRESHOLD`: Threshold for flagging comments (default: 0.7)
- `ANALYSIS_PROMPT_TEMPLATE`: Prompt template for analyzing comments

## Database

The application uses SQLite with SQLAlchemy ORM. The database file is created at `osint_comments/osint_comments.db`.

### Models

- **Article**: Represents an article with an identifier
- **User**: Represents a comment author with external_id, name, and display_name
- **Comment**: Represents a comment with message, timestamps, score, and relationships to Article and User

## Kafka Integration

### Topics

- **raw-comments**: Raw comments fetched from the API
- **flagged-comments**: Analysis results from the comment analyzer

### Message Format

#### Raw Comments

Raw comments are published to the "raw-comments" topic in the format returned by the API.

#### Flagged Comments

Analysis results are published to the "flagged-comments" topic in the following format:

```json
{
  "comment_id": 12345,
  "comment_text": "The comment text",
  "article_identifier": "article:e24:Jbwa97",
  "analysis": {
    "aggressive_score": 0.8,
    "hateful_score": 0.3,
    "racist_score": 0.1,
    "is_flagged": true,
    "explanation": "This comment contains aggressive language.",
    "max_category": "aggressive",
    "max_score": 0.8
  },
  "metadata": {
    "analyzed_at": "2025-02-25T19:45:00.123456",
    "error": false
  }
}
```

## Testing

Run tests using pytest:

```bash
poetry run pytest
```

### Testing the Comment Analyzer

To test the comment analyzer specifically:

```bash
poetry run pytest osint_comments/tests/test_comment_analyzer.py
```

## Development

### Adding Proxies

To use proxies for API requests, add them to the `PROXIES` list in `api_client.py`:

```python
PROXIES = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    # Add more proxies as needed
]
```

### Adding User Agents

To add more User-Agent strings for rotation, add them to the `USER_AGENTS` list in `api_client.py`.

## License

[Specify your license here]

## Contributing

[Add contributing guidelines if applicable]
