# test_kafka_consumer.py
import pytest
from unittest.mock import MagicMock, patch, call

from kafka_consumer import KafkaConsumerClient
from config import RAW_COMMENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS

@pytest.fixture
def mock_kafka_consumer():
    """Create a mock Kafka consumer."""
    with patch('kafka_consumer.KafkaConsumer') as mock_consumer_class:
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        
        # Set up mock messages
        message1 = MagicMock()
        message1.value = {"id": 1, "message": "Test message 1"}
        message1.topic = RAW_COMMENTS_TOPIC
        message1.partition = 0
        message1.offset = 0
        
        message2 = MagicMock()
        message2.value = {"id": 2, "message": "Test message 2"}
        message2.topic = RAW_COMMENTS_TOPIC
        message2.partition = 0
        message2.offset = 1
        
        # Set up the mock consumer to return the messages
        mock_consumer.__iter__.return_value = iter([message1, message2])
        
        yield mock_consumer

def test_kafka_consumer_initialization():
    """Test initializing the KafkaConsumerClient."""
    with patch('kafka_consumer.KafkaConsumer') as mock_consumer_class:
        # Test with default parameters
        client = KafkaConsumerClient()
        mock_consumer_class.assert_called_once_with(
            RAW_COMMENTS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=ANY,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="comment-analyzer-group"
        )
        
        # Reset the mock
        mock_consumer_class.reset_mock()
        
        # Test with custom parameters
        custom_servers = ["custom-server:9092"]
        custom_topics = ["custom-topic"]
        client = KafkaConsumerClient(
            bootstrap_servers=custom_servers,
            topics=custom_topics
        )
        mock_consumer_class.assert_called_once_with(
            "custom-topic",
            bootstrap_servers=custom_servers,
            value_deserializer=ANY,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="comment-analyzer-group"
        )

def test_consume_messages(mock_kafka_consumer):
    """Test consuming messages from Kafka."""
    # Create a mock process_message function
    process_message = MagicMock()
    
    # Create the client
    client = KafkaConsumerClient()
    
    # Replace the consumer with our mock
    client.consumer = mock_kafka_consumer
    
    # Consume messages
    client.consume_messages(process_message)
    
    # Check that process_message was called for each message
    assert process_message.call_count == 2
    process_message.assert_has_calls([
        call({"id": 1, "message": "Test message 1"}),
        call({"id": 2, "message": "Test message 2"})
    ])

def test_consume_messages_with_max(mock_kafka_consumer):
    """Test consuming a limited number of messages."""
    # Create a mock process_message function
    process_message = MagicMock()
    
    # Create the client
    client = KafkaConsumerClient()
    
    # Replace the consumer with our mock
    client.consumer = mock_kafka_consumer
    
    # Consume messages with a limit
    client.consume_messages(process_message, max_messages=1)
    
    # Check that process_message was called only once
    process_message.assert_called_once_with({"id": 1, "message": "Test message 1"})

def test_consume_messages_error_handling(mock_kafka_consumer):
    """Test error handling during message consumption."""
    # Create a process_message function that raises an exception
    def process_message(message):
        if message["id"] == 1:
            raise Exception("Test error")
    
    # Create a mock process_message function
    mock_process = MagicMock(side_effect=process_message)
    
    # Create the client
    client = KafkaConsumerClient()
    
    # Replace the consumer with our mock
    client.consumer = mock_kafka_consumer
    
    # Consume messages
    client.consume_messages(mock_process)
    
    # Check that process_message was called for each message
    assert mock_process.call_count == 2
    
    # The second message should still be processed despite the error in the first
    mock_process.assert_has_calls([
        call({"id": 1, "message": "Test message 1"}),
        call({"id": 2, "message": "Test message 2"})
    ])

def test_close():
    """Test closing the Kafka consumer."""
    with patch('kafka_consumer.KafkaConsumer') as mock_consumer_class:
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        
        # Create the client
        client = KafkaConsumerClient()
        
        # Close the consumer
        client.close()
        
        # Check that the consumer was closed
        mock_consumer.close.assert_called_once()
