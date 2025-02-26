# kafka_producer.py
import json
import logging
from kafka import KafkaProducer as KafkaProducerLib

from .config import KAFKA_BOOTSTRAP_SERVERS

logger = logging.getLogger(__name__)

class KafkaProducer:
    """
    Kafka producer for sending messages to Kafka topics.
    """
    
    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, topic=None):
        """
        Initialize the Kafka producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Default topic to send messages to
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = KafkaProducerLib(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
        )
        logger.info(f"Kafka producer initialized for bootstrap servers: {bootstrap_servers}")
        if topic:
            logger.info(f"Default topic: {topic}")

    def send_message(self, message, topic=None):
        """
        Send a message to a Kafka topic.
        
        Args:
            message: The message to send
            topic: The topic to send the message to (overrides default topic)
        """
        if topic is None:
            topic = self.topic
            
        if topic is None:
            raise ValueError("No topic specified")
            
        future = self.producer.send(topic, message)
        try:
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to topic '{record_metadata.topic}' partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            return False
            
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
