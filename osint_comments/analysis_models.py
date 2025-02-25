# analysis_models.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class CommentAnalysis(BaseModel):
    """Model for comment analysis results."""
    
    # Original comment information
    comment_id: int = Field(..., description="ID of the original comment")
    comment_text: str = Field(..., description="Text of the original comment")
    article_identifier: str = Field(..., description="Identifier of the article the comment belongs to")
    
    # Analysis scores
    aggressive_score: float = Field(..., ge=0.0, le=1.0, description="Score for aggressive content (0.0-1.0)")
    hateful_score: float = Field(..., ge=0.0, le=1.0, description="Score for hateful content (0.0-1.0)")
    racist_score: float = Field(..., ge=0.0, le=1.0, description="Score for racist content (0.0-1.0)")
    
    # Overall flag status
    is_flagged: bool = Field(..., description="Whether the comment is flagged as problematic")
    
    # Additional information
    explanation: str = Field(..., description="Explanation of the analysis")
    max_category: str = Field(..., description="Category with the highest score")
    max_score: float = Field(..., ge=0.0, le=1.0, description="Highest score among all categories")
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the analysis")
    error: bool = Field(default=False, description="Whether an error occurred during analysis")
    
    @validator('max_category', 'max_score', pre=True, always=True)
    def set_max_category_and_score(cls, v, values):
        """Set the max_category and max_score based on the analysis scores."""
        if 'max_category' in values or 'max_score' in values:
            return v
            
        scores = {
            'aggressive': values.get('aggressive_score', 0.0),
            'hateful': values.get('hateful_score', 0.0),
            'racist': values.get('racist_score', 0.0)
        }
        
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        
        if v is None and 'max_category' not in values:
            return max_category
        elif v is None and 'max_score' not in values:
            return max_score
        return v
    
    @classmethod
    def from_raw_analysis(cls, comment_data: Dict[str, Any], analysis: Dict[str, Any], 
                          threshold: float = 0.7) -> 'CommentAnalysis':
        """
        Create a CommentAnalysis instance from raw comment data and analysis results.
        
        Args:
            comment_data: Raw comment data from Kafka
            analysis: Analysis results from the LLM
            threshold: Threshold for flagging comments (default: 0.7)
            
        Returns:
            A CommentAnalysis instance
        """
        # Extract scores from analysis
        aggressive_score = float(analysis.get('aggressive', 0.0))
        hateful_score = float(analysis.get('hateful', 0.0))
        racist_score = float(analysis.get('racist', 0.0))
        
        # Determine if the comment should be flagged
        is_flagged = (
            aggressive_score >= threshold or 
            hateful_score >= threshold or 
            racist_score >= threshold
        )
        
        # Create the CommentAnalysis instance
        return cls(
            comment_id=comment_data.get('id'),
            comment_text=comment_data.get('message', ''),
            article_identifier=comment_data.get('articleId', ''),
            aggressive_score=aggressive_score,
            hateful_score=hateful_score,
            racist_score=racist_score,
            is_flagged=is_flagged,
            explanation=analysis.get('explanation', ''),
            max_category='',  # Will be set by validator
            max_score=0.0,    # Will be set by validator
            error=analysis.get('error', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for Kafka publishing."""
        return {
            "comment_id": self.comment_id,
            "comment_text": self.comment_text,
            "article_identifier": self.article_identifier,
            "analysis": {
                "aggressive_score": self.aggressive_score,
                "hateful_score": self.hateful_score,
                "racist_score": self.racist_score,
                "is_flagged": self.is_flagged,
                "explanation": self.explanation,
                "max_category": self.max_category,
                "max_score": self.max_score
            },
            "metadata": {
                "analyzed_at": self.analyzed_at.isoformat(),
                "error": self.error
            }
        }
