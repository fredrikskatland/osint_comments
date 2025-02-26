import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from ..comment_analyzer import CommentAnalyzer
from ..llm_client import OpenAIClient
from ..kafka_producer import KafkaProducer

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=OpenAIClient)
    return client

@pytest.fixture
def mock_kafka_producer():
    producer = MagicMock(spec=KafkaProducer)
    return producer

@pytest.fixture
def comment_analyzer(mock_llm_client, mock_kafka_producer):
    analyzer = CommentAnalyzer(
        llm_client=mock_llm_client,
        kafka_producer=mock_kafka_producer
    )
    return analyzer

def test_comment_analyzer_init(comment_analyzer, mock_llm_client, mock_kafka_producer):
    assert comment_analyzer.llm_client == mock_llm_client
    assert comment_analyzer.kafka_producer == mock_kafka_producer

def test_analyze_comment_not_flagged(comment_analyzer, mock_llm_client, mock_kafka_producer):
    # Create a sample comment
    comment = {
        "id": "123",
        "content": "This is a positive comment",
        "author": "Test User",
        "timestamp": datetime.now().isoformat(),
        "article_id": "456"
    }
    
    # Set up the mock LLM client to return a result
    analysis_result = {
        "sentiment": "positive",
        "toxicity": 0.1,
        "is_flagged": False
    }
    mock_llm_client.analyze_text.return_value = analysis_result
    
    # Analyze the comment
    result = comment_analyzer.analyze_comment(comment)
    
    # Check that the LLM client was called with the correct arguments
    mock_llm_client.analyze_text.assert_called_once_with(comment["content"])
    
    # Check that the result is correct
    assert result == analysis_result
    
    # Check that the Kafka producer was not called (since the comment is not flagged)
    mock_kafka_producer.send_message.assert_not_called()

def test_analyze_comment_flagged(comment_analyzer, mock_llm_client, mock_kafka_producer):
    # Create a sample comment
    comment = {
        "id": "123",
        "content": "This is a toxic comment",
        "author": "Test User",
        "timestamp": datetime.now().isoformat(),
        "article_id": "456"
    }
    
    # Set up the mock LLM client to return a result
    analysis_result = {
        "sentiment": "negative",
        "toxicity": 0.8,
        "is_flagged": True
    }
    mock_llm_client.analyze_text.return_value = analysis_result
    
    # Analyze the comment
    result = comment_analyzer.analyze_comment(comment)
    
    # Check that the LLM client was called with the correct arguments
    mock_llm_client.analyze_text.assert_called_once_with(comment["content"])
    
    # Check that the result is correct
    assert result == analysis_result
    
    # Check that the Kafka producer was called with the correct arguments
    mock_kafka_producer.send_message.assert_called_once()
    args, kwargs = mock_kafka_producer.send_message.call_args
    message = args[0]
    assert message["id"] == comment["id"]
    assert message["content"] == comment["content"]
    assert message["analysis"] == analysis_result
