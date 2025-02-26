# OSINT Comments Project

This project provides tools for collecting, analyzing, and processing comments from various online sources.

## Components

### 1. OSINT Comments Core (osint_comments/)

The core package provides functionality for:
- Analyzing comments using NLP techniques
- Storing comments and articles in a database
- Processing comments through a Kafka-based pipeline
- API client for interacting with external services

### 2. E24 Crawler (crawler/)

A web crawler for e24.no that identifies articles with comments, following clean architecture principles with separation of concerns.

#### Features

- Crawls e24.no to find articles
- Identifies articles with comments
- Stores article data in a SQLite database
- Caches crawled URLs to avoid redundant processing
- Command-line interface for easy usage

## Getting Started

### Prerequisites

- Python 3.7+
- Kafka (for the full pipeline)
- SQLite (for local storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/osint_comments.git
cd osint_comments
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Install the crawler package:
```bash
cd crawler
pip install -e .
cd ..
```

### Running the E24 Crawler

You can run the crawler directly:

```bash
# Run with default settings (crawl 3 pages)
python -m crawler

# Crawl more pages
python -m crawler --pages 5

# List articles with comments from the database
python -m crawler --list-comments
```

### Integrating with OSINT Comments

To use the crawler with the OSINT Comments pipeline:

```bash
# Run the integration script
python -m osint_comments.e24_integration

# Specify number of pages to crawl
python -m osint_comments.e24_integration --pages 5
```

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

## Testing

Run the tests with pytest:

```bash
pytest osint_comments/tests/
pytest crawler/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
