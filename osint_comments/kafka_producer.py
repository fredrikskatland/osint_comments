# kafka_producer.py
import json
import logging
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KafkaProducerClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, bootstrap_servers=["localhost:9092"]):
        if not hasattr(self, "producer"):
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
            )


    def send_message(self, topic: str, message: dict):
        future = self.producer.send(topic, message)
        try:
            record_metadata = future.get(timeout=10)
            logger.info("Message sent to topic '%s' partition %s offset %s", 
                        record_metadata.topic, record_metadata.partition, record_metadata.offset)
        except Exception as e:
            logger.error("Failed to send message to Kafka: %s", e)
