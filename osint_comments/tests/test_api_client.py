import pytest
from unittest.mock import patch, MagicMock
from ..api_client import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@patch('requests.get')
def test_fetch_comments_success(mock_get, api_client):
    # Mock the response from the API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "123",
                "message": "This is a test comment",
                "user": {
                    "id": "456",
                    "name": "test_user",
                    "displayName": "Test User"
                },
                "createdAt": "2025-02-23T08:56:30.547Z",
                "updatedAt": "2025-02-23T08:56:30.547Z",
                "score": 10
            }
        ],
        "total": 1
    }
    mock_get.return_value = mock_response
    
    # Call the method
    result = api_client.fetch_comments("article:e24:123")
    
    # Check that the result is correct
    assert result["items"][0]["id"] == "123"
    assert result["items"][0]["message"] == "This is a test comment"
    assert result["total"] == 1
    
    # Check that the API was called with the correct parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "article:e24:123" in args[0]

@patch('requests.get')
def test_fetch_comments_error(mock_get, api_client):
    # Mock the response from the API
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    # Call the method and check that it raises an exception
    with pytest.raises(Exception):
        api_client.fetch_comments("article:e24:123")
