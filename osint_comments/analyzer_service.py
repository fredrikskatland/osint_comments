# analyzer_service.py
import sys
import logging
import time
import signal
from typing import Optional

from rich.logging import RichHandler

from config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC, ANALYSIS_THRESHOLD
from kafka_consumer import KafkaConsumerClient
from kafka_producer import KafkaProducerClient
from llm_client import OpenAIClient
from comment_analyzer import CommentAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

class AnalyzerService:
    """
    Service for analyzing comments from Kafka and publishing the results.
    """
    
    def __init__(self, max_messages: Optional[int] = None):
        """
        Initialize the AnalyzerService.
        
        Args:
            max_messages: Maximum number of messages to process (None for infinite)
        """
        self.running = False
        self.max_messages = max_messages
        
        # Initialize components
        self.kafka_consumer = KafkaConsumerClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            topics=[RAW_COMMENTS_TOPIC]
        )
        self.kafka_producer = KafkaProducerClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
        )
        self.openai_client = OpenAIClient()
        self.comment_analyzer = CommentAnalyzer(
            openai_client=self.openai_client,
            kafka_producer=self.kafka_producer,
            threshold=ANALYSIS_THRESHOLD
        )
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        logger.info("AnalyzerService initialized")
        
    def start(self) -> None:
        """Start the analyzer service."""
        self.running = True
        logger.info("Starting AnalyzerService")
        
        try:
            # Start consuming messages
            self.kafka_consumer.consume_messages(
                process_message=self._process_message,
                max_messages=self.max_messages
            )
        except KeyboardInterrupt:
            logger.info("Service interrupted by user")
        except Exception as e:
            logger.error(f"Error in AnalyzerService: {e}")
        finally:
            self.stop()
            
    def stop(self) -> None:
        """Stop the analyzer service."""
        if self.running:
            logger.info("Stopping AnalyzerService")
            self.running = False
            
    def _process_message(self, message: dict) -> None:
        """
        Process a message from Kafka.
        
        Args:
            message: The message to process
        """
        try:
            # Process the comment
            self.comment_analyzer.process_comment(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _handle_signal(self, signum, frame) -> None:
        """
        Handle signals (SIGINT, SIGTERM).
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down")
        self.stop()
        
def main() -> None:
    """Main entry point for the analyzer service."""
    # Parse command line arguments
    max_messages = None
    if len(sys.argv) > 1:
        try:
            max_messages = int(sys.argv[1])
            logger.info(f"Will process up to {max_messages} messages")
        except ValueError:
            logger.warning(f"Invalid max_messages value: {sys.argv[1]}, using unlimited")
    
    # Create and start the service
    service = AnalyzerService(max_messages=max_messages)
    service.start()
    
if __name__ == "__main__":
    main()
