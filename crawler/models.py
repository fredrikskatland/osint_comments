"""
Domain models for the E24 crawler module.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Article:
    """
    Represents an article from e24.no
    """
    url: str
    title: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    content: Optional[str] = None
    has_comments: bool = False
    comment_count: Optional[int] = None
    identifier: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the article"""
        return f"{self.title} ({self.url})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "url": self.url,
            "title": self.title,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "author": self.author,
            "content": self.content,
            "has_comments": self.has_comments,
            "comment_count": self.comment_count,
            "identifier": self.identifier
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Article':
        """Create an Article instance from a dictionary"""
        if "published_date" in data and data["published_date"]:
            data["published_date"] = datetime.fromisoformat(data["published_date"])
        return cls(**data)
