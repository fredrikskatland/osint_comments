# repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from .models import Article, User, Comment
from crawler.models import Article as CrawlerArticle

class Repository:
    """
    Unified repository for managing articles, users, and comments.
    Provides methods for each step of the workflow: crawling, gathering comments, and analyzing.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    #
    # Article methods
    #
    
    def save_article_from_crawler(self, crawler_article: CrawlerArticle) -> Article:
        """
        Save an article from the crawler to the database.
        
        Args:
            crawler_article: Article from the crawler
            
        Returns:
            The saved Article
        """
        # Use the identifier already set by the crawler
        identifier = f"article:e24:{crawler_article.identifier}"
        
        # Check if the article already exists
        article = self.session.query(Article).filter_by(identifier=identifier).first()
        
        if article:
            # Update existing article
            article.url = crawler_article.url
            article.title = crawler_article.title
            article.published_date = crawler_article.published_date
            article.author = crawler_article.author
            article.content = crawler_article.content
            article.has_comments = crawler_article.has_comments
            article.comment_count = crawler_article.comment_count
            article.updated_at = datetime.utcnow()
        else:
            # Create new article
            article = Article(
                identifier=identifier,
                url=crawler_article.url,
                title=crawler_article.title,
                published_date=crawler_article.published_date,
                author=crawler_article.author,
                content=crawler_article.content,
                has_comments=crawler_article.has_comments,
                comment_count=crawler_article.comment_count,
                comments_gathered=False,
                comments_analyzed=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(article)
        
        self.session.commit()
        return article
    
    def get_article_by_identifier(self, identifier: str) -> Optional[Article]:
        """
        Get an article by its identifier.
        
        Args:
            identifier: Article identifier
            
        Returns:
            The article if found, None otherwise
        """
        return self.session.query(Article).filter_by(identifier=identifier).first()
    
    def get_article_by_url(self, url: str) -> Optional[Article]:
        """
        Get an article by its URL.
        
        Args:
            url: Article URL
            
        Returns:
            The article if found, None otherwise
        """
        return self.session.query(Article).filter_by(url=url).first()
    
    def get_articles_with_comments_not_gathered(self, limit: Optional[int] = None) -> List[Article]:
        """
        Get articles that haven't had their comments gathered yet.
        In the new approach, we check all articles for comments using the API.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of articles
        """
        query = self.session.query(Article).filter(
            Article.comments_gathered == False
        ).order_by(Article.published_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_articles_with_comments_not_analyzed(self, limit: Optional[int] = None) -> List[Article]:
        """
        Get articles that have comments gathered but not analyzed.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of articles
        """
        query = self.session.query(Article).filter(
            Article.has_comments == True,
            Article.comments_gathered == True,
            Article.comments_analyzed == False
        ).order_by(Article.published_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def mark_article_comments_gathered(self, article: Article) -> None:
        """
        Mark an article as having had its comments gathered.
        
        Args:
            article: The article to update
        """
        article.comments_gathered = True
        article.updated_at = datetime.utcnow()
        self.session.commit()
    
    def mark_article_comments_analyzed(self, article: Article) -> None:
        """
        Mark an article as having had its comments analyzed.
        
        Args:
            article: The article to update
        """
        article.comments_analyzed = True
        article.updated_at = datetime.utcnow()
        self.session.commit()
    
    def get_article_stats(self) -> Dict[str, int]:
        """
        Get statistics about articles in the database.
        
        Returns:
            Dictionary with statistics
        """
        total_articles = self.session.query(func.count(Article.id)).scalar()
        articles_with_comments = self.session.query(func.count(Article.id)).filter(Article.has_comments == True).scalar()
        comments_gathered = self.session.query(func.count(Article.id)).filter(Article.comments_gathered == True).scalar()
        comments_analyzed = self.session.query(func.count(Article.id)).filter(Article.comments_analyzed == True).scalar()
        
        return {
            "total_articles": total_articles,
            "articles_with_comments": articles_with_comments,
            "comments_gathered": comments_gathered,
            "comments_analyzed": comments_analyzed
        }
    
    #
    # User methods
    #
    
    def get_or_create_user(self, external_id: int, name: str, display_name: str) -> User:
        """
        Get or create a user.
        
        Args:
            external_id: External ID of the user
            name: User name
            display_name: User display name
            
        Returns:
            The user
        """
        user = self.session.query(User).filter_by(external_id=external_id).first()
        if not user:
            user = User(
                external_id=external_id,
                name=name,
                display_name=display_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(user)
            self.session.commit()
        return user
    
    #
    # Comment methods
    #
    
    def add_comment(self, comment_data: dict, article: Article, user: User) -> Tuple[Comment, bool]:
        """
        Add a comment to the database.
        
        Args:
            comment_data: Comment data from the API
            article: The article the comment belongs to
            user: The user who wrote the comment
            
        Returns:
            Tuple of (comment, created) where created is True if the comment was newly created
        """
        # Check if the comment already exists
        existing = self.session.query(Comment).filter_by(id=comment_data['id']).first()
        if existing:
            return existing, False

        # Convert ISO timestamps to Python datetime objects
        created_at = datetime.fromisoformat(comment_data['createdAt'].replace("Z", "+00:00"))
        updated_at = None
        if comment_data.get('updatedAt'):
            updated_at = datetime.fromisoformat(comment_data['updatedAt'].replace("Z", "+00:00"))

        # Create the comment
        comment = Comment(
            id=comment_data['id'],
            message=comment_data['message'],
            created_at=created_at,
            updated_at=updated_at,
            score=comment_data.get('score'),
            article_id=article.id,
            user_id=user.id,
            is_analyzed=False,
            is_flagged=False,
            record_created_at=datetime.utcnow(),
            record_updated_at=datetime.utcnow()
        )
        self.session.add(comment)
        self.session.commit()
        return comment, True
    
    def get_comments_not_analyzed(self, limit: Optional[int] = None) -> List[Comment]:
        """
        Get comments that haven't been analyzed yet.
        
        Args:
            limit: Maximum number of comments to return
            
        Returns:
            List of comments
        """
        query = self.session.query(Comment).filter(Comment.is_analyzed == False)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def update_comment_analysis(self, comment: Comment, analysis_data: Dict[str, Any]) -> None:
        """
        Update a comment with analysis data.
        
        Args:
            comment: The comment to update
            analysis_data: Analysis data
        """
        comment.is_analyzed = True
        comment.is_flagged = analysis_data.get('is_flagged', False)
        comment.aggressive_score = analysis_data.get('aggressive', 0.0)
        comment.hateful_score = analysis_data.get('hateful', 0.0)
        comment.racist_score = analysis_data.get('racist', 0.0)
        comment.analysis_explanation = analysis_data.get('explanation', '')
        comment.analyzed_at = datetime.utcnow()
        comment.record_updated_at = datetime.utcnow()
        self.session.commit()
    
    def get_comment_stats(self) -> Dict[str, int]:
        """
        Get statistics about comments in the database.
        
        Returns:
            Dictionary with statistics
        """
        total_comments = self.session.query(func.count(Comment.id)).scalar()
        analyzed_comments = self.session.query(func.count(Comment.id)).filter(Comment.is_analyzed == True).scalar()
        flagged_comments = self.session.query(func.count(Comment.id)).filter(Comment.is_flagged == True).scalar()
        
        return {
            "total_comments": total_comments,
            "analyzed_comments": analyzed_comments,
            "flagged_comments": flagged_comments
        }
