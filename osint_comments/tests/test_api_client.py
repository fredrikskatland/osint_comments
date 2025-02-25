# tests/test_api_client.py
import pytest
from api_client import APIClient

def fake_requests_get(url, *args, **kwargs):
    class FakeResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception("Bad status code")

        def json(self):
            return self._json_data

    # If the URL contains our test article identifier, return a fake JSON response.
    if "article:e24:TestArticle" in url:
        return FakeResponse({
            "count": 1,
            "items": [
                {
                    "id": 1,
                    "message": "Fake comment",
                    "createdAt": "2025-02-23T08:56:30.547Z",
                    "updatedAt": "2025-02-23T08:56:30.547Z",
                    "score": 10,
                    "user": {
                        "id": 123,
                        "name": "Fake User",
                        "displayName": "Fake Display"
                    }
                }
            ],
            "commentsClosed": False,
            "moderationStatus": "STANDARD"
        })
    return FakeResponse({}, 404)

def test_fetch_comments(monkeypatch):
    # Replace requests.get with our fake_requests_get.
    monkeypatch.setattr("api_client.requests.get", fake_requests_get)
    client = APIClient()
    data = client.fetch_comments("article:e24:TestArticle")
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["message"] == "Fake comment"
