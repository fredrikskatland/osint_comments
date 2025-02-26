import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from ..llm_client import OpenAIClient
from ..config import ANALYSIS_PROMPT_TEMPLATE

@pytest.fixture
def mock_openai():
    with patch('openai.OpenAI') as mock:
        yield mock

@pytest.fixture
def llm_client(mock_openai):
    client = OpenAIClient()
    return client

def test_llm_client_init(llm_client, mock_openai):
    # Check that the OpenAI client was initialized
    mock_openai.assert_called_once()

def test_analyze_text(llm_client):
    # Create a sample comment
    comment = "This is a test comment"
    
    # Set up the mock OpenAI client to return a result
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = json.dumps({
        "sentiment": "positive",
        "toxicity": 0.1,
        "is_flagged": False
    })
    llm_client.client.chat.completions.create.return_value = mock_completion
    
    # Analyze the comment
    result = llm_client.analyze_text(comment)
    
    # Check that the OpenAI client was called with the correct arguments
    llm_client.client.chat.completions.create.assert_called_once()
    args, kwargs = llm_client.client.chat.completions.create.call_args
    
    # Check that the prompt includes the comment
    assert any(comment in message["content"] for message in kwargs["messages"])
    
    # Check that the result is correct
    assert result["sentiment"] == "positive"
    assert result["toxicity"] == 0.1
    assert result["is_flagged"] == False

def test_analyze_text_error(llm_client):
    # Create a sample comment
    comment = "This is a test comment"
    
    # Set up the mock OpenAI client to return an invalid result
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Invalid JSON"
    llm_client.client.chat.completions.create.return_value = mock_completion
    
    # Analyze the comment and check that it returns a default result
    result = llm_client.analyze_text(comment)
    
    # Check that the result is the default
    assert "sentiment" in result
    assert "toxicity" in result
    assert "is_flagged" in result
