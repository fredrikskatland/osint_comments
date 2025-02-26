# tests/test_repository.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Base, Article, User, Comment
from ..repository import Repository
from datetime import datetime

@pytest.fixture
def session():
    # Create an in-memory SQLite database for testing.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_or_create_article(session):
    repo = Repository(session)
    identifier = "article:e24:TestArticle"
    article1 = repo.get_or_create_article(identifier)
    article2 = repo.get_or_create_article(identifier)
    # They should be the same record.
    assert article1.id == article2.id
    assert article1.identifier == identifier

def test_get_or_create_user(session):
    repo = Repository(session)
    external_id = 123
    name = "Test User"
    display_name = "Tester"
    user1 = repo.get_or_create_user(external_id, name, display_name)
    user2 = repo.get_or_create_user(external_id, name, display_name)
    # They should be the same record.
    assert user1.id == user2.id
    assert user1.name == name
    assert user1.display_name == display_name

def test_add_comment(session):
    repo = Repository(session)
    article = repo.get_or_create_article("article:e24:TestArticle")
    user = repo.get_or_create_user(123, "Test User", "Tester")
    comment_data = {
        "id": 1,
        "message": "Test comment",
        "createdAt": "2025-02-23T08:56:30.547Z",
        "updatedAt": "2025-02-23T08:56:30.547Z",
        "score": 10,
    }
    comment1, created1 = repo.add_comment(comment_data, article, user)
    comment2, created2 = repo.add_comment(comment_data, article, user)
    # The same comment should not be added twice.
    assert comment1.id == comment2.id
    assert comment1.message == "Test comment"
    # Check that timestamps are correctly converted.
    assert isinstance(comment1.created_at, datetime)
    # First comment should be created, second should not
    assert created1 == True
    assert created2 == False
