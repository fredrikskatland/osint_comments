"""
Main entry point for the OSINT Comments Core.

This module allows the OSINT Comments Core to be run directly with:
python -m osint_comments.main
"""
import sys
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from .repository import Repository
from .api_client import APIClient
from .kafka_consumer import KafkaConsumer
from .kafka_producer import KafkaProducer
from .config import Config

# Set up logging
import logging
from rich.logging import RichHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


def process_article(article_identifier: str, config: Config):
    """
    Process comments for a specific article.
    
    Args:
        article_identifier: Identifier for the article
        config: Configuration object
    """
    # Set up the database connection
    engine = create_engine(f"sqlite:///{config.db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = Repository(session)
    api_client = APIClient()
    kafka_producer = KafkaProducer(
        bootstrap_servers=config.kafka_bootstrap_servers,
        topic="raw-comments"
    )

    # Fetch comments from the API
    data = api_client.fetch_comments(article_identifier)
    items = data.get("items", [])
    logger.info(f"Fetched {len(items)} comments for article {article_identifier}")

    # Create or retrieve the article record
    article = repo.get_or_create_article(article_identifier)

    # Process each comment
    for item in items:
        user_data = item.get("user", {})
        external_id = user_data.get("id")
        name = user_data.get("name")
        display_name = user_data.get("displayName")
        user = repo.get_or_create_user(external_id, name, display_name)
        
        comment, created = repo.add_comment(item, article, user)
        if created:
            logger.info(f"Stored new comment id {comment.id}")
            # Publish the raw comment to Kafka
            kafka_producer.send_message(comment.to_dict())
        else:
            logger.info(f"Comment id {comment.id} already exists; skipping Kafka publish")

    logger.info("Comments stored and published successfully")


def run_consumer(config: Config):
    """
    Run the Kafka consumer to process incoming comments.
    
    Args:
        config: Configuration object
    """
    logger.info("Starting Kafka consumer")
    
    # Set up the database connection
    engine = create_engine(f"sqlite:///{config.db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = Repository(session)
    
    # Create and run the consumer
    consumer = KafkaConsumer(
        bootstrap_servers=config.kafka_bootstrap_servers,
        topic="raw-comments",
        group_id="osint-comments-consumer",
        repository=repo
    )
    
    try:
        consumer.run()
    except KeyboardInterrupt:
        logger.info("Stopping Kafka consumer")
        consumer.stop()


def main():
    """
    Main entry point for the OSINT Comments Core.
    """
    parser = argparse.ArgumentParser(description="OSINT Comments Core")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process article command
    process_parser = subparsers.add_parser("process", help="Process comments for a specific article")
    process_parser.add_argument("article_id", help="Identifier for the article")
    process_parser.add_argument("--config", help="Path to configuration file")
    
    # Run consumer command
    consumer_parser = subparsers.add_parser("consumer", help="Run the Kafka consumer")
    consumer_parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config if hasattr(args, "config") else None)
    
    if args.command == "process":
        process_article(args.article_id, config)
    elif args.command == "consumer":
        run_consumer(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
