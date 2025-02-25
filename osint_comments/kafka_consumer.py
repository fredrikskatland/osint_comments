# kafka_consumer.py
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from kafka import KafkaConsumer

from config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC

logger = logging.getLogger(__name__)

class KafkaConsumerClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KafkaConsumerClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, bootstrap_servers: List[str] = None, topics: List[str] = None):
        if not hasattr(self, "consumer"):
            if bootstrap_servers is None:
                bootstrap_servers = KAFKA_BOOTSTRAP_SERVERS
            
            if topics is None:
                topics = [RAW_COMMENTS_TOPIC]
                
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="comment-analyzer-group"
            )
            logger.info(f"Kafka consumer initialized for topics: {topics}")

    def consume_messages(self, process_message: Callable[[Dict[str, Any]], None], 
                        max_messages: Optional[int] = None) -> None:
        """
        Consume messages from Kafka topics and process them using the provided callback.
        
        Args:
            process_message: A callback function that processes each message
            max_messages: Maximum number of messages to consume (None for infinite)
        """
        try:
            message_count = 0
            logger.info("Starting to consume messages...")
            
            for message in self.consumer:
                try:
                    logger.debug(f"Received message from topic {message.topic}, partition {message.partition}, offset {message.offset}")
                    process_message(message.value)
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
            self.close()
            
    def close(self) -> None:
        """Close the Kafka consumer."""
        if hasattr(self, "consumer"):
            self.consumer.close()
            logger.info("Kafka consumer closed")
