# test_llm_client.py
import pytest
import json
from unittest.mock import MagicMock, patch, ANY

from llm_client import OpenAIClient
from config import ANALYSIS_PROMPT_TEMPLATE

# Mock response for OpenAI API
class MockResponse:
    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completions create method
        mock_chat = MagicMock()
        mock_client.chat.completions.create = mock_chat
        
        # Set up a default response
        mock_response = MockResponse(json.dumps({
            "aggressive": 0.8,
            "hateful": 0.3,
            "racist": 0.1,
            "explanation": "This comment contains aggressive language."
        }))
        mock_chat.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def openai_client():
    """Create an OpenAIClient with mocked dependencies."""
    with patch('openai.api_key', 'test_api_key'), \
         patch('openai.OpenAI') as mock_openai:
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create the OpenAIClient
        client = OpenAIClient(api_key="test_api_key")
        
        # Replace the OpenAI client with our mock
        client.client = mock_client
        
        yield client

def test_openai_client_initialization():
    """Test initializing the OpenAIClient."""
    with patch('openai.api_key', None), \
         patch('openai.OpenAI') as mock_openai:
        
        # Test with API key provided
        client = OpenAIClient(api_key="test_api_key")
        assert client.api_key == "test_api_key"
        
        # Test with missing API key
        with pytest.raises(ValueError):
            OpenAIClient(api_key="")

def test_analyze_comment_success(openai_client, mock_openai):
    """Test analyzing a comment successfully."""
    # Set up the mock response
    mock_response = MockResponse(json.dumps({
        "aggressive": 0.8,
        "hateful": 0.3,
        "racist": 0.1,
        "explanation": "This comment contains aggressive language."
    }))
    openai_client.client.chat.completions.create.return_value = mock_response
    
    # Analyze a comment
    comment_text = "This is a test comment"
    result = openai_client.analyze_comment(comment_text)
    
    # Check that the OpenAI API was called correctly
    openai_client.client.chat.completions.create.assert_called_once_with(
        model=ANY,
        messages=[
            {"role": "system", "content": "You are a content moderation assistant that analyzes comments for harmful content."},
            {"role": "user", "content": ANALYSIS_PROMPT_TEMPLATE.format(comment_text=comment_text)}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    # Check the result
    assert result["aggressive"] == 0.8
    assert result["hateful"] == 0.3
    assert result["racist"] == 0.1
    assert result["explanation"] == "This comment contains aggressive language."

def test_analyze_comment_json_error(openai_client):
    """Test handling a JSON parsing error."""
    # Set up the mock response with invalid JSON
    mock_response = MockResponse("This is not valid JSON")
    openai_client.client.chat.completions.create.return_value = mock_response
    
    # Analyze a comment
    result = openai_client.analyze_comment("This is a test comment")
    
    # Check the result
    assert result["aggressive"] == 0.0
    assert result["hateful"] == 0.0
    assert result["racist"] == 0.0
    assert "Error parsing response" in result["explanation"]
    assert result["error"] == True

def test_analyze_comment_api_error(openai_client):
    """Test handling an API error."""
    # Set up the mock to raise an exception
    openai_client.client.chat.completions.create.side_effect = Exception("API error")
    
    # Analyze a comment
    result = openai_client.analyze_comment("This is a test comment")
    
    # Check the result
    assert result["aggressive"] == 0.0
    assert result["hateful"] == 0.0
    assert result["racist"] == 0.0
    assert "Error analyzing comment" in result["explanation"]
    assert result["error"] == True
