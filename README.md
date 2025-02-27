# OSINT Comments Project

This project provides tools for collecting, analyzing, and processing comments from various online sources.

## Project Overview

The OSINT Comments project consists of two main components:

1. **OSINT Comments Core** - A framework for analyzing and processing comments
2. **E24 Crawler** - A web crawler for collecting articles from e24.no

These components work together to create a pipeline for collecting, analyzing, and storing comments from online sources.

## Architecture

The project follows clean architecture principles with separation of concerns:

1. **Domain Layer**
   - Models for articles, comments, and analysis results

2. **Application Layer**
   - Services for orchestrating the processing pipeline

3. **Infrastructure Layer**
   - Repositories for data storage
   - Kafka producers/consumers for messaging
   - Web scrapers for data collection
   - API clients for fetching comments

4. **Interface Layer**
   - CLI tools for running components
   - API endpoints for integration

## Components

### 1. OSINT Comments Core (osint_comments/)

The core package provides functionality for:
- Gathering comments using API clients
- Analyzing comments using NLP techniques
- Storing comments and articles in a database
- Processing comments through a Kafka-based pipeline

For more details, see the [OSINT Comments documentation](osint_comments/README.md).

### 2. E24 Crawler (crawler/)

A web crawler for e24.no that identifies articles, following clean architecture principles with separation of concerns.

For more details, see the [E24 Crawler documentation](crawler/README.md).

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- Kafka (optional, for the full pipeline)
- SQLite (for local storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/osint_comments.git
cd osint_comments
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Activate the Poetry environment:
```bash
poetry shell
```

### Running the Pipeline

The project follows a three-step pipeline:

1. **Crawl**: Collect articles from e24.no
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
# Crawl articles from the last 3 months
poetry run python -m osint_comments.e24_integration crawl --months-back 3

# Crawl with a limit on the number of articles
poetry run python -m osint_comments.e24_integration crawl --max-articles 50

# Gather comments for a specific article
poetry run python -m osint_comments.e24_integration gather --article-id article:e24:example-article

# Analyze comments with Kafka integration
poetry run python -m osint_comments.e24_integration analyze --publish-to-kafka --kafka-servers localhost:9092

# Run the full pipeline with all options
poetry run python -m osint_comments.e24_integration pipeline --months-back 3 --max-articles 100 --publish-to-kafka --kafka-servers localhost:9092
```

## Testing

Run the tests with pytest:

```bash
# Run all tests
poetry run pytest

# Run specific test modules
poetry run pytest osint_comments/tests/
poetry run pytest crawler/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
