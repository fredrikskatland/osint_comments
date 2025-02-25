# test_analysis_models.py
import pytest
from datetime import datetime
from pydantic import ValidationError

from analysis_models import CommentAnalysis

def test_comment_analysis_creation():
    """Test creating a CommentAnalysis instance directly."""
    analysis = CommentAnalysis(
        comment_id=12345,
        comment_text="This is a test comment",
        article_identifier="article:e24:test123",
        aggressive_score=0.8,
        hateful_score=0.3,
        racist_score=0.1,
        is_flagged=True,
        explanation="This comment contains aggressive language",
        max_category="aggressive",
        max_score=0.8
    )
    
    # Check that the fields are set correctly
    assert analysis.comment_id == 12345
    assert analysis.comment_text == "This is a test comment"
    assert analysis.article_identifier == "article:e24:test123"
    assert analysis.aggressive_score == 0.8
    assert analysis.hateful_score == 0.3
    assert analysis.racist_score == 0.1
    assert analysis.is_flagged == True
    assert analysis.explanation == "This comment contains aggressive language"
    assert analysis.max_category == "aggressive"
    assert analysis.max_score == 0.8
    assert isinstance(analysis.analyzed_at, datetime)
    assert analysis.error == False

def test_comment_analysis_from_raw_analysis():
    """Test creating a CommentAnalysis instance from raw analysis data."""
    # Sample comment data
    comment_data = {
        "id": 12345,
        "message": "This is a test comment",
        "articleId": "article:e24:test123"
    }
    
    # Sample analysis results
    analysis_results = {
        "aggressive": 0.8,
        "hateful": 0.3,
        "racist": 0.1,
        "explanation": "This comment contains aggressive language"
    }
    
    # Create a CommentAnalysis instance
    analysis = CommentAnalysis.from_raw_analysis(
        comment_data=comment_data,
        analysis=analysis_results,
        threshold=0.7
    )
    
    # Check that the fields are set correctly
    assert analysis.comment_id == 12345
    assert analysis.comment_text == "This is a test comment"
    assert analysis.article_identifier == "article:e24:test123"
    assert analysis.aggressive_score == 0.8
    assert analysis.hateful_score == 0.3
    assert analysis.racist_score == 0.1
    assert analysis.is_flagged == True
    assert analysis.explanation == "This comment contains aggressive language"
    assert analysis.max_category == "aggressive"
    assert analysis.max_score == 0.8
    assert isinstance(analysis.analyzed_at, datetime)
    assert analysis.error == False

def test_comment_analysis_not_flagged():
    """Test creating a CommentAnalysis instance that is not flagged."""
    # Sample comment data
    comment_data = {
        "id": 12345,
        "message": "This is a friendly comment",
        "articleId": "article:e24:test123"
    }
    
    # Sample analysis results
    analysis_results = {
        "aggressive": 0.2,
        "hateful": 0.1,
        "racist": 0.0,
        "explanation": "This comment is not problematic"
    }
    
    # Create a CommentAnalysis instance
    analysis = CommentAnalysis.from_raw_analysis(
        comment_data=comment_data,
        analysis=analysis_results,
        threshold=0.7
    )
    
    # Check that the fields are set correctly
    assert analysis.is_flagged == False
    assert analysis.max_category == "aggressive"
    assert analysis.max_score == 0.2

def test_comment_analysis_to_dict():
    """Test converting a CommentAnalysis instance to a dictionary."""
    # Create a CommentAnalysis instance
    analysis = CommentAnalysis(
        comment_id=12345,
        comment_text="This is a test comment",
        article_identifier="article:e24:test123",
        aggressive_score=0.8,
        hateful_score=0.3,
        racist_score=0.1,
        is_flagged=True,
        explanation="This comment contains aggressive language",
        max_category="aggressive",
        max_score=0.8
    )
    
    # Convert to dictionary
    analysis_dict = analysis.to_dict()
    
    # Check the dictionary structure
    assert analysis_dict["comment_id"] == 12345
    assert analysis_dict["comment_text"] == "This is a test comment"
    assert analysis_dict["article_identifier"] == "article:e24:test123"
    assert analysis_dict["analysis"]["aggressive_score"] == 0.8
    assert analysis_dict["analysis"]["hateful_score"] == 0.3
    assert analysis_dict["analysis"]["racist_score"] == 0.1
    assert analysis_dict["analysis"]["is_flagged"] == True
    assert analysis_dict["analysis"]["explanation"] == "This comment contains aggressive language"
    assert analysis_dict["analysis"]["max_category"] == "aggressive"
    assert analysis_dict["analysis"]["max_score"] == 0.8
    assert "analyzed_at" in analysis_dict["metadata"]
    assert analysis_dict["metadata"]["error"] == False

def test_comment_analysis_validation():
    """Test validation of CommentAnalysis fields."""
    # Test with invalid aggressive_score
    with pytest.raises(ValidationError):
        CommentAnalysis(
            comment_id=12345,
            comment_text="This is a test comment",
            article_identifier="article:e24:test123",
            aggressive_score=1.5,  # Invalid: should be between 0.0 and 1.0
            hateful_score=0.3,
            racist_score=0.1,
            is_flagged=True,
            explanation="This comment contains aggressive language",
            max_category="aggressive",
            max_score=0.8
        )
    
    # Test with missing required field
    with pytest.raises(ValidationError):
        CommentAnalysis(
            comment_id=12345,
            # comment_text is missing
            article_identifier="article:e24:test123",
            aggressive_score=0.8,
            hateful_score=0.3,
            racist_score=0.1,
            is_flagged=True,
            explanation="This comment contains aggressive language",
            max_category="aggressive",
            max_score=0.8
        )
