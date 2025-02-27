# models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    
    # Core article data
    identifier = Column(String, unique=True, nullable=False)  # Format: article:e24:ArticleID
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    published_date = Column(DateTime, nullable=True)
    author = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    
    # Comment-related data
    has_comments = Column(Boolean, default=False)
    comment_count = Column(Integer, default=0)
    
    # Status tracking
    comments_gathered = Column(Boolean, default=False)
    comments_analyzed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = relationship("Comment", back_populates="article")
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "identifier": self.identifier,
            "url": self.url,
            "title": self.title,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "author": self.author,
            "content": self.content,
            "has_comments": self.has_comments,
            "comment_count": self.comment_count,
            "comments_gathered": self.comments_gathered,
            "comments_analyzed": self.comments_analyzed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, unique=True, nullable=True)
    name = Column(String)
    display_name = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = relationship("Comment", back_populates="user")
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "name": self.name,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)  # using the API's comment id
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    
    # Foreign keys
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Status tracking
    is_analyzed = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    
    # Analysis results
    aggressive_score = Column(Float, nullable=True)
    hateful_score = Column(Float, nullable=True)
    racist_score = Column(Float, nullable=True)
    analysis_explanation = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    
    # Timestamps for the record
    record_created_at = Column(DateTime, default=datetime.utcnow)
    record_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="comments")
    user = relationship("User", back_populates="comments")
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "score": self.score,
            "article_id": self.article_id,
            "user_id": self.user_id,
            "is_analyzed": self.is_analyzed,
            "is_flagged": self.is_flagged,
            "aggressive_score": self.aggressive_score,
            "hateful_score": self.hateful_score,
            "racist_score": self.racist_score,
            "analysis_explanation": self.analysis_explanation,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "record_created_at": self.record_created_at.isoformat() if self.record_created_at else None,
            "record_updated_at": self.record_updated_at.isoformat() if self.record_updated_at else None
        }
