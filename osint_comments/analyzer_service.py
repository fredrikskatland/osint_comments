# analyzer_service.py
import sys
import logging
import time
import signal
from typing import Optional

from rich.logging import RichHandler

from .config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC, ANALYSIS_THRESHOLD
from .kafka_consumer import KafkaConsumer
from .kafka_producer import KafkaProducer
from .llm_client import OpenAIClient
from .comment_analyzer import CommentAnalyzer

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
    
    def __init__(self, kafka_consumer=None, kafka_producer=None, llm_client=None, comment_analyzer=None, max_messages: Optional[int] = None):
        """
        Initialize the AnalyzerService.
        
        Args:
            kafka_consumer: Kafka consumer instance (optional)
            kafka_producer: Kafka producer instance (optional)
            llm_client: LLM client instance (optional)
            comment_analyzer: Comment analyzer instance (optional)
            max_messages: Maximum number of messages to process (None for infinite)
        """
        self.running = False
        self.max_messages = max_messages
        
        # Initialize components
        self.kafka_consumer = kafka_consumer or KafkaConsumer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            topic=RAW_COMMENTS_TOPIC,
            group_id="osint-comments-analyzer"
        )
        self.kafka_producer = kafka_producer or KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            topic="analyzed-comments"
        )
        self.llm_client = llm_client or OpenAIClient()
        self.comment_analyzer = comment_analyzer or CommentAnalyzer(
            llm_client=self.llm_client,
            kafka_producer=self.kafka_producer
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
            # Set the message processor for the Kafka consumer
            self.kafka_consumer.message_processor = self.process_message
            
            # Start consuming messages
            self.kafka_consumer.run(max_messages=self.max_messages)
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
            self.kafka_consumer.stop()
            
    def process_message(self, message: dict) -> dict:
        """
        Process a message from Kafka.
        
        Args:
            message: The message to process
            
        Returns:
            The analysis result
        """
        try:
            # Analyze the comment
            result = self.comment_analyzer.analyze_comment(message)
            return result
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e)}
            
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
