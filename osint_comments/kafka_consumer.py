# kafka_consumer.py
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from kafka import KafkaConsumer as KafkaConsumerLib

from .config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC

logger = logging.getLogger(__name__)

class KafkaConsumer:
    """
    Kafka consumer for consuming messages from Kafka topics.
    """
    
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS, 
                 topic: str = RAW_COMMENTS_TOPIC, 
                 group_id: str = "osint-comments-consumer"):
        """
        Initialize the Kafka consumer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic to consume from
            group_id: Consumer group ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer = None
        self.message_processor = None
        self.running = False
        
        logger.info(f"Kafka consumer initialized for topic: {topic}")
        
    def _create_consumer(self):
        """Create the Kafka consumer."""
        return KafkaConsumerLib(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=self._deserialize
        )
        
    def _deserialize(self, value):
        """Deserialize a message from Kafka."""
        try:
            return json.loads(value.decode("utf-8"))
        except Exception as e:
            logger.error(f"Error deserializing message: {e}")
            return {}
            
    def _process_message(self, message):
        """
        Process a message from Kafka.
        
        Args:
            message: The message to process
        """
        if self.message_processor:
            return self.message_processor(message)
        else:
            logger.warning("No message processor set")
            return None
            
    def run(self, max_messages: Optional[int] = None):
        """
        Run the Kafka consumer.
        
        Args:
            max_messages: Maximum number of messages to consume (None for infinite)
        """
        if not self.message_processor:
            raise ValueError("No message processor set")
            
        self.running = True
        self.consumer = self._create_consumer()
        
        try:
            message_count = 0
            logger.info(f"Starting to consume messages from topic: {self.topic}")
            
            for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    logger.debug(f"Received message from partition {message.partition}, offset {message.offset}")
                    self._process_message(message.value)
                    message_count += 1
                    
                    if max_messages is not None and message_count >= max_messages:
                        logger.info(f"Reached maximum message count ({max_messages}), stopping consumption")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Consumption interrupted by user")
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            self.consumer = None
            logger.info("Kafka consumer closed")
