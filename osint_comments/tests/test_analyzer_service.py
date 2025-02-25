# test_analyzer_service.py
import pytest
import signal
from unittest.mock import MagicMock, patch, call, ANY

from analyzer_service import AnalyzerService
from kafka_consumer import KafkaConsumerClient
from kafka_producer import KafkaProducerClient
from llm_client import OpenAIClient
from comment_analyzer import CommentAnalyzer

@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for the AnalyzerService."""
    with patch('analyzer_service.KafkaConsumerClient') as mock_consumer_class, \
         patch('analyzer_service.KafkaProducerClient') as mock_producer_class, \
         patch('analyzer_service.OpenAIClient') as mock_openai_class, \
         patch('analyzer_service.CommentAnalyzer') as mock_analyzer_class:
        
        # Create mock instances
        mock_consumer = MagicMock(spec=KafkaConsumerClient)
        mock_producer = MagicMock(spec=KafkaProducerClient)
        mock_openai = MagicMock(spec=OpenAIClient)
        mock_analyzer = MagicMock(spec=CommentAnalyzer)
        
        # Set up the mock classes to return the mock instances
        mock_consumer_class.return_value = mock_consumer
        mock_producer_class.return_value = mock_producer
        mock_openai_class.return_value = mock_openai
        mock_analyzer_class.return_value = mock_analyzer
        
        yield {
            'consumer_class': mock_consumer_class,
            'producer_class': mock_producer_class,
            'openai_class': mock_openai_class,
            'analyzer_class': mock_analyzer_class,
            'consumer': mock_consumer,
            'producer': mock_producer,
            'openai': mock_openai,
            'analyzer': mock_analyzer
        }

def test_analyzer_service_initialization(mock_dependencies):
    """Test initializing the AnalyzerService."""
    # Create the service
    service = AnalyzerService()
    
    # Check that the dependencies were initialized correctly
    mock_dependencies['consumer_class'].assert_called_once()
    mock_dependencies['producer_class'].assert_called_once()
    mock_dependencies['openai_class'].assert_called_once()
    mock_dependencies['analyzer_class'].assert_called_once_with(
        openai_client=mock_dependencies['openai'],
        kafka_producer=mock_dependencies['producer'],
        threshold=ANY
    )

def test_analyzer_service_start(mock_dependencies):
    """Test starting the AnalyzerService."""
    # Create the service
    service = AnalyzerService()
    
    # Start the service
    service.start()
    
    # Check that the consumer was started
    mock_dependencies['consumer'].consume_messages.assert_called_once_with(
        process_message=service._process_message,
        max_messages=None
    )

def test_analyzer_service_start_with_max_messages(mock_dependencies):
    """Test starting the AnalyzerService with a maximum number of messages."""
    # Create the service with a maximum number of messages
    service = AnalyzerService(max_messages=10)
    
    # Start the service
    service.start()
    
    # Check that the consumer was started with the correct parameters
    mock_dependencies['consumer'].consume_messages.assert_called_once_with(
        process_message=service._process_message,
        max_messages=10
    )

def test_analyzer_service_stop(mock_dependencies):
    """Test stopping the AnalyzerService."""
    # Create the service
    service = AnalyzerService()
    
    # Set the running flag
    service.running = True
    
    # Stop the service
    service.stop()
    
    # Check that the running flag was set to False
    assert service.running == False

def test_analyzer_service_process_message(mock_dependencies):
    """Test processing a message."""
    # Create the service
    service = AnalyzerService()
    
    # Create a test message
    message = {"id": 1, "message": "Test message"}
    
    # Process the message
    service._process_message(message)
    
    # Check that the analyzer was called
    mock_dependencies['analyzer'].process_comment.assert_called_once_with(message)

def test_analyzer_service_process_message_error(mock_dependencies):
    """Test error handling during message processing."""
    # Set up the analyzer to raise an exception
    mock_dependencies['analyzer'].process_comment.side_effect = Exception("Test error")
    
    # Create the service
    service = AnalyzerService()
    
    # Create a test message
    message = {"id": 1, "message": "Test message"}
    
    # Process the message (should not raise an exception)
    service._process_message(message)
    
    # Check that the analyzer was called
    mock_dependencies['analyzer'].process_comment.assert_called_once_with(message)

def test_analyzer_service_signal_handling(mock_dependencies):
    """Test signal handling."""
    # Create the service
    service = AnalyzerService()
    
    # Set the running flag
    service.running = True
    
    # Simulate a SIGINT signal
    service._handle_signal(signal.SIGINT, None)
    
    # Check that the running flag was set to False
    assert service.running == False
