# models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    # Relationship: an article can have many comments.
    comments = relationship("Comment", back_populates="article")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, unique=True, nullable=True)
    name = Column(String)
    display_name = Column(String)
    # Relationship: a user can have many comments.
    comments = relationship("Comment", back_populates="user")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)  # using the API's comment id
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    article = relationship("Article", back_populates="comments")
    user = relationship("User", back_populates="comments")
