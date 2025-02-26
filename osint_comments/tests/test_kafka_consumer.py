import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from ..kafka_consumer import KafkaConsumer
from ..config import RAW_COMMENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS

@pytest.fixture
def mock_kafka_consumer():
    with patch('kafka.KafkaConsumer') as mock:
        yield mock

@pytest.fixture
def consumer(mock_kafka_consumer):
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=RAW_COMMENTS_TOPIC,
        group_id="test-group"
    )
    return consumer

def test_kafka_consumer_init(consumer, mock_kafka_consumer):
    # Check that the Kafka consumer was initialized with the correct parameters
    mock_kafka_consumer.assert_called_once_with(
        RAW_COMMENTS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="test-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=consumer._deserialize
    )

def test_deserialize(consumer):
    # Create a sample message
    message = {
        "id": "123",
        "content": "This is a test comment",
        "author": "Test User",
        "timestamp": datetime.now().isoformat(),
        "article_id": "456"
    }
    
    # Serialize the message
    serialized = json.dumps(message).encode('utf-8')
    
    # Deserialize the message
    deserialized = consumer._deserialize(serialized)
    
    # Check that the deserialized message is correct
    assert deserialized["id"] == message["id"]
    assert deserialized["content"] == message["content"]
    assert deserialized["author"] == message["author"]
    assert deserialized["article_id"] == message["article_id"]

def test_process_message(consumer):
    # Create a sample message
    message = {
        "id": "123",
        "content": "This is a test comment",
        "author": "Test User",
        "timestamp": datetime.now().isoformat(),
        "article_id": "456"
    }
    
    # Set up a mock message processor
    mock_processor = MagicMock()
    consumer.message_processor = mock_processor
    
    # Process the message
    consumer._process_message(message)
    
    # Check that the message processor was called with the correct arguments
    mock_processor.assert_called_once_with(message)
