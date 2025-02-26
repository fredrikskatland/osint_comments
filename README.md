# OSINT Comments Project

This project provides tools for collecting, analyzing, and processing comments from various online sources.

## Project Overview

The OSINT Comments project consists of two main components:

1. **OSINT Comments Core** - A framework for analyzing and processing comments
2. **E24 Crawler** - A web crawler for collecting articles and comments from e24.no

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

4. **Interface Layer**
   - CLI tools for running components
   - API endpoints for integration

## Components

### 1. OSINT Comments Core (osint_comments/)

The core package provides functionality for:
- Analyzing comments using NLP techniques
- Storing comments and articles in a database
- Processing comments through a Kafka-based pipeline
- API client for interacting with external services

For more details, see the [OSINT Comments documentation](osint_comments/README.md).

### 2. E24 Crawler (crawler/)

A web crawler for e24.no that identifies articles with comments, following clean architecture principles with separation of concerns.

For more details, see the [E24 Crawler documentation](crawler/README.md).

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- Kafka (for the full pipeline)
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

### Running the Components

#### Running the E24 Crawler

```bash
# Run with default settings (crawl 3 pages)
python -m crawler

# Crawl more pages
python -m crawler --pages 5

# List articles with comments from the database
python -m crawler --list-comments
```

#### Running the Integration

To use the crawler with the OSINT Comments pipeline:

```bash
# Run the integration script
python -m osint_comments.e24_integration

# Specify number of pages to crawl
python -m osint_comments.e24_integration --pages 5
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
