import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

# Use relative imports
from ..analyzer_service import AnalyzerService
from ..kafka_consumer import KafkaConsumer
from ..kafka_producer import KafkaProducer
from ..llm_client import OpenAIClient
from ..comment_analyzer import CommentAnalyzer

@pytest.fixture
def mock_kafka_consumer():
    consumer = MagicMock(spec=KafkaConsumer)
    return consumer

@pytest.fixture
def mock_kafka_producer():
    producer = MagicMock(spec=KafkaProducer)
    return producer

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=OpenAIClient)
    return client

@pytest.fixture
def mock_comment_analyzer():
    analyzer = MagicMock(spec=CommentAnalyzer)
    return analyzer

@pytest.fixture
def analyzer_service(mock_kafka_consumer, mock_kafka_producer, mock_llm_client, mock_comment_analyzer):
    service = AnalyzerService(
        kafka_consumer=mock_kafka_consumer,
        kafka_producer=mock_kafka_producer,
        llm_client=mock_llm_client,
        comment_analyzer=mock_comment_analyzer
    )
    return service

def test_analyzer_service_init(analyzer_service, mock_kafka_consumer, mock_kafka_producer, mock_llm_client, mock_comment_analyzer):
    assert analyzer_service.kafka_consumer == mock_kafka_consumer
    assert analyzer_service.kafka_producer == mock_kafka_producer
    assert analyzer_service.llm_client == mock_llm_client
    assert analyzer_service.comment_analyzer == mock_comment_analyzer

def test_analyzer_service_process_message(analyzer_service, mock_comment_analyzer):
    # Create a sample message
    message = {
        "id": "123",
        "content": "This is a test comment",
        "author": "Test User",
        "timestamp": datetime.now().isoformat(),
        "article_id": "456"
    }
    
    # Set up the mock comment analyzer to return a result
    analysis_result = {
        "sentiment": "positive",
        "toxicity": 0.1,
        "is_flagged": False
    }
    mock_comment_analyzer.analyze_comment.return_value = analysis_result
    
    # Process the message
    result = analyzer_service.process_message(json.dumps(message))
    
    # Check that the comment analyzer was called with the correct arguments
    mock_comment_analyzer.analyze_comment.assert_called_once_with(message)
    
    # Check that the result is correct
    assert result == analysis_result
