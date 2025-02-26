"""
Repository for storing and retrieving articles.
"""
import logging
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from .models import Article

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ArticleRepository:
    """
    Repository for storing and retrieving articles from a SQLite database.
    """
    
    def __init__(self, db_path: str = "articles.db"):
        """
        Initialize the repository with a database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create articles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                published_date TEXT,
                author TEXT,
                content TEXT,
                has_comments BOOLEAN NOT NULL,
                comment_count INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            logger.debug("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
        finally:
            conn.close()
    
    def save_article(self, article: Article) -> bool:
        """
        Save an article to the database.
        
        Args:
            article: The article to save
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check if article already exists
            cursor.execute("SELECT url FROM articles WHERE url = ?", (article.url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing article
                cursor.execute('''
                UPDATE articles SET
                    title = ?,
                    published_date = ?,
                    author = ?,
                    content = ?,
                    has_comments = ?,
                    comment_count = ?,
                    updated_at = ?
                WHERE url = ?
                ''', (
                    article.title,
                    article.published_date.isoformat() if article.published_date else None,
                    article.author,
                    article.content,
                    article.has_comments,
                    article.comment_count,
                    now,
                    article.url
                ))
                logger.debug(f"Updated article in database: {article.title}")
            else:
                # Insert new article
                cursor.execute('''
                INSERT INTO articles (
                    url, title, published_date, author, content,
                    has_comments, comment_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.url,
                    article.title,
                    article.published_date.isoformat() if article.published_date else None,
                    article.author,
                    article.content,
                    article.has_comments,
                    article.comment_count,
                    now,
                    now
                ))
                logger.debug(f"Inserted new article in database: {article.title}")
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving article to database: {e}")
            return False
        finally:
            conn.close()
    
    def get_article_by_url(self, url: str) -> Optional[Article]:
        """
        Get an article by its URL.
        
        Args:
            url: The URL of the article
            
        Returns:
            The article if found, None otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE url = ?", (url,))
            row = cursor.fetchone()
            
            if row:
                # Convert row to dictionary
                article_dict = dict(row)
                
                # Create Article object
                return Article(
                    url=article_dict["url"],
                    title=article_dict["title"],
                    published_date=datetime.fromisoformat(article_dict["published_date"]) if article_dict["published_date"] else None,
                    author=article_dict["author"],
                    content=article_dict["content"],
                    has_comments=bool(article_dict["has_comments"]),
                    comment_count=article_dict["comment_count"]
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting article from database: {e}")
            return None
        finally:
            conn.close()
    
    def get_articles_with_comments(self, limit: Optional[int] = None) -> List[Article]:
        """
        Get all articles that have comments.
        
        Args:
            limit: Maximum number of articles to return (None for all)
            
        Returns:
            List of articles with comments
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE has_comments = 1 ORDER BY published_date DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                # Convert row to dictionary
                article_dict = dict(row)
                
                # Create Article object
                article = Article(
                    url=article_dict["url"],
                    title=article_dict["title"],
                    published_date=datetime.fromisoformat(article_dict["published_date"]) if article_dict["published_date"] else None,
                    author=article_dict["author"],
                    content=article_dict["content"],
                    has_comments=bool(article_dict["has_comments"]),
                    comment_count=article_dict["comment_count"]
                )
                articles.append(article)
            
            return articles
        except Exception as e:
            logger.error(f"Error getting articles with comments from database: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_articles(self, limit: int = 10) -> List[Article]:
        """
        Get the most recent articles.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of recent articles
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM articles ORDER BY published_date DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                # Convert row to dictionary
                article_dict = dict(row)
                
                # Create Article object
                article = Article(
                    url=article_dict["url"],
                    title=article_dict["title"],
                    published_date=datetime.fromisoformat(article_dict["published_date"]) if article_dict["published_date"] else None,
                    author=article_dict["author"],
                    content=article_dict["content"],
                    has_comments=bool(article_dict["has_comments"]),
                    comment_count=article_dict["comment_count"]
                )
                articles.append(article)
            
            return articles
        except Exception as e:
            logger.error(f"Error getting recent articles from database: {e}")
            return []
        finally:
            conn.close()
