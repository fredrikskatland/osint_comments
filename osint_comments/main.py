# main.py
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from repository import Repository
from api_client import APIClient
from kafka_producer import KafkaProducerClient

# Set up logging (using Rich for nicer output, as previously discussed)
import logging
from rich.logging import RichHandler
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

def main(article_identifier: str):
    # Set up the database connection (using SQLite for this example)
    engine = create_engine("sqlite:///osint_comments.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = Repository(session)
    api_client = APIClient()
    kafka_producer = KafkaProducerClient(bootstrap_servers=["localhost:9092"])

    # Fetch comments from the API.
    data = api_client.fetch_comments(article_identifier)
    items = data.get("items", [])
    logger.info("Fetched %d comments", len(items))

    # Create or retrieve the article record.
    article = repo.get_or_create_article(article_identifier)

    # Process each comment.
    for item in items:
        user_data = item.get("user", {})
        external_id = user_data.get("id")
        name = user_data.get("name")
        display_name = user_data.get("displayName")
        user = repo.get_or_create_user(external_id, name, display_name)
        
        comment, created = repo.add_comment(item, article, user)
        if created:
            logger.info("Stored new comment id %s", comment.id)
            # Publish the raw comment to Kafka.
            kafka_producer.send_message("raw-comments", item)
        else:
            logger.info("Comment id %s already exists; skipping Kafka publish", comment.id)

    logger.info("Comments stored and published successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <article_identifier>")
        sys.exit(1)
    article_identifier = sys.argv[1]
    main(article_identifier)
