# OSINT Comments

A Python application for collecting, storing, and processing comments from online articles for Open Source Intelligence (OSINT) purposes. This tool fetches comments from the E24 publication API, stores them in a local database, and publishes them to Kafka for further processing.

## Features

- Fetch comments from E24 publication API
- Store comments, users, and article data in a SQLite database
- Publish raw comments to Kafka for downstream processing
- Configurable request parameters (limit, offset, ordering)
- Proxy and User-Agent rotation to avoid rate limiting
- Clean architecture with separation of concerns

## Project Structure

```
osint_comments/
├── docker-compose.yml      # Docker setup for Kafka and Zookeeper
├── poetry.lock             # Poetry lock file
├── pyproject.toml          # Poetry project configuration
├── README.md               # This file
└── osint_comments/         # Main package
    ├── api_client.py       # API client for fetching comments
    ├── config.py           # Configuration settings
    ├── kafka_producer.py   # Kafka producer for publishing comments
    ├── main.py             # Main entry point
    ├── models.py           # SQLAlchemy models
    ├── repository.py       # Data access layer
    └── tests/              # Test directory
        ├── conftest.py     # Pytest configuration
        ├── test_api_client.py  # API client tests
        └── test_repository.py  # Repository tests
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (dependency management)
- Docker and Docker Compose (for Kafka)

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

3. Start Kafka and Zookeeper using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Usage

### Basic Usage

Run the application with an article identifier:

```bash
poetry run python osint_comments/main.py <article_identifier>
```

Where `<article_identifier>` is in the format `article:e24:Jbwa97`.

### Example

```bash
poetry run python osint_comments/main.py article:e24:Jbwa97
```

This will:
1. Fetch comments for the specified article from the E24 API
2. Store the article, users, and comments in the SQLite database
3. Publish the raw comments to the Kafka topic "raw-comments"

## Configuration

Configuration settings are stored in `config.py`:

- `API_BASE_URL`: Base URL for the comments API
- `COMMENTS_ENDPOINT_TEMPLATE`: Endpoint template for fetching comments
- `DEFAULT_LIMIT`: Default number of comments to fetch (default: 100)
- `DEFAULT_OFFSET`: Default offset for pagination (default: 0)
- `DEFAULT_ORDER`: Default ordering of comments (default: "score DESC")
- `DEFAULT_REPLIES`: Default ordering of replies (default: "ASC")

In `api_client.py`, you can configure:

- `USER_AGENTS`: List of User-Agent strings to rotate through
- `PROXIES`: List of proxy servers to use (if needed)

## Database

The application uses SQLite with SQLAlchemy ORM. The database file is created at `osint_comments/osint_comments.db`.

### Models

- **Article**: Represents an article with an identifier
- **User**: Represents a comment author with external_id, name, and display_name
- **Comment**: Represents a comment with message, timestamps, score, and relationships to Article and User

## Kafka Integration

Raw comments are published to the Kafka topic "raw-comments" for further processing. The Kafka producer is configured to connect to `localhost:9092` by default.

## Testing

Run tests using pytest:

```bash
poetry run pytest
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
