# test_comment_analyzer.py
import pytest
from unittest.mock import MagicMock, patch

from comment_analyzer import CommentAnalyzer
from llm_client import OpenAIClient
from kafka_producer import KafkaProducerClient
from analysis_models import CommentAnalysis

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock(spec=OpenAIClient)
    client.analyze_comment.return_value = {
        "aggressive": 0.8,
        "hateful": 0.3,
        "racist": 0.1,
        "explanation": "This comment contains aggressive language."
    }
    return client

@pytest.fixture
def mock_kafka_producer():
    """Create a mock Kafka producer."""
    producer = MagicMock(spec=KafkaProducerClient)
    return producer

@pytest.fixture
def comment_analyzer(mock_openai_client, mock_kafka_producer):
    """Create a CommentAnalyzer with mock dependencies."""
    return CommentAnalyzer(
        openai_client=mock_openai_client,
        kafka_producer=mock_kafka_producer,
        threshold=0.7
    )

def test_process_comment(comment_analyzer, mock_openai_client, mock_kafka_producer):
    """Test processing a comment."""
    # Sample comment data
    comment_data = {
        "id": 12345,
        "message": "This is a test comment that might be aggressive.",
        "articleId": "article:e24:test123"
    }
    
    # Process the comment
    result = comment_analyzer.process_comment(comment_data)
    
    # Check that the OpenAI client was called
    mock_openai_client.analyze_comment.assert_called_once_with(comment_data["message"])
    
    # Check that the Kafka producer was called
    mock_kafka_producer.send_message.assert_called_once()
    
    # Check the result
    assert isinstance(result, CommentAnalysis)
    assert result.comment_id == comment_data["id"]
    assert result.comment_text == comment_data["message"]
    assert result.article_identifier == comment_data["articleId"]
    assert result.aggressive_score == 0.8
    assert result.hateful_score == 0.3
    assert result.racist_score == 0.1
    assert result.is_flagged == True  # Aggressive score is above threshold
    assert result.max_category == "aggressive"
    assert result.max_score == 0.8

def test_process_comment_empty_text(comment_analyzer, mock_openai_client, mock_kafka_producer):
    """Test processing a comment with empty text."""
    # Sample comment data with empty message
    comment_data = {
        "id": 12345,
        "message": "",
        "articleId": "article:e24:test123"
    }
    
    # Process the comment
    result = comment_analyzer.process_comment(comment_data)
    
    # Check that the OpenAI client was not called
    mock_openai_client.analyze_comment.assert_not_called()
    
    # Check that the Kafka producer was not called
    mock_kafka_producer.send_message.assert_not_called()
    
    # Check the result
    assert result is None

def test_process_comment_not_flagged(comment_analyzer, mock_openai_client, mock_kafka_producer):
    """Test processing a comment that is not flagged."""
    # Override the mock response
    mock_openai_client.analyze_comment.return_value = {
        "aggressive": 0.2,
        "hateful": 0.1,
        "racist": 0.0,
        "explanation": "This comment is not problematic."
    }
    
    # Sample comment data
    comment_data = {
        "id": 12345,
        "message": "This is a friendly comment.",
        "articleId": "article:e24:test123"
    }
    
    # Process the comment
    result = comment_analyzer.process_comment(comment_data)
    
    # Check the result
    assert isinstance(result, CommentAnalysis)
    assert result.is_flagged == False  # All scores are below threshold
    assert result.max_category == "aggressive"
    assert result.max_score == 0.2
