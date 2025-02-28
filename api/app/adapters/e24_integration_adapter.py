# api/app/adapters/e24_integration_adapter.py
"""
Adapter for the E24Integration class to make it easier to use with FastAPI.
"""
from osint_comments.e24_integration import E24Integration
from typing import Dict, Any, List, Optional

class E24IntegrationAdapter:
    """
    Adapter for the E24Integration class to make it easier to use with FastAPI.
    """
    
    def __init__(self, db_path: str = "osint_comments.db"):
        self.integration = E24Integration(db_path=db_path)
    
    async def crawl_articles(self, 
                            process_content: bool = False,
                            months_back: int = 1, 
                            max_articles: Optional[int] = None) -> Dict[str, Any]:
        """
        Crawl articles from e24.no
        """
        try:
            articles = self.integration.crawl_articles(
                process_content=process_content,
                months_back=months_back,
                max_articles=max_articles
            )
            
            return {
                "status": "success",
                "articles_count": len(articles),
                "message": f"Successfully crawled {len(articles)} articles"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error crawling articles: {str(e)}"
            }
    
    async def gather_comments(self,
                             article_id: Optional[str] = None,
                             limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Gather comments for articles
        """
        try:
            new_comments = self.integration.gather_comments(
                article_id=article_id,
                limit=limit
            )
            
            return {
                "status": "success",
                "new_comments": new_comments,
                "message": f"Successfully gathered {new_comments} new comments"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error gathering comments: {str(e)}"
            }
    
    async def analyze_comments(self,
                              article_id: Optional[str] = None,
                              limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze comments for harmful content
        """
        try:
            analysis_stats = self.integration.analyze_comments(
                article_id=article_id,
                limit=limit
            )
            
            return {
                "status": "success",
                "stats": analysis_stats,
                "message": f"Successfully analyzed {analysis_stats['analyzed']} comments ({analysis_stats['flagged']} flagged)"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing comments: {str(e)}"
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about articles and comments
        """
        try:
            article_stats = self.integration.repository.get_article_stats()
            comment_stats = self.integration.repository.get_comment_stats()
            
            return {
                "status": "success",
                "article_stats": article_stats,
                "comment_stats": comment_stats
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting stats: {str(e)}"
            }
    
    async def get_articles(self, limit: Optional[int] = 10, offset: Optional[int] = 0) -> Dict[str, Any]:
        """
        Get articles from the database
        """
        try:
            # Import the Article model directly
            from osint_comments.models import Article
            
            # Query articles from the database
            articles = self.integration.session.query(Article).order_by(
                Article.published_date.desc()
            ).offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "identifier": article.identifier,
                    "title": article.title,
                    "url": article.url,
                    "published_date": article.published_date.isoformat() if article.published_date else None,
                    "author": article.author,
                    "has_comments": article.has_comments,
                    "comment_count": article.comment_count,
                    "comments_gathered": article.comments_gathered,
                    "comments_analyzed": article.comments_analyzed
                })
            
            return {
                "status": "success",
                "articles": articles_data,
                "total": self.integration.repository.get_article_stats()["total_articles"]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting articles: {str(e)}"
            }
    
    async def get_article_by_id(self, article_id: str) -> Dict[str, Any]:
        """
        Get an article by its identifier
        """
        try:
            article = self.integration.repository.get_article_by_identifier(article_id)
            
            if not article:
                return {
                    "status": "error",
                    "message": f"Article not found: {article_id}"
                }
            
            article_data = {
                "id": article.id,
                "identifier": article.identifier,
                "title": article.title,
                "url": article.url,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "author": article.author,
                "content": article.content,
                "has_comments": article.has_comments,
                "comment_count": article.comment_count,
                "comments_gathered": article.comments_gathered,
                "comments_analyzed": article.comments_analyzed
            }
            
            return {
                "status": "success",
                "article": article_data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting article: {str(e)}"
            }
    
    async def get_comments(self, 
                          article_id: Optional[str] = None, 
                          flagged_only: bool = False,
                          min_aggressive: Optional[float] = None,
                          min_hateful: Optional[float] = None,
                          min_racist: Optional[float] = None,
                          limit: Optional[int] = 10, 
                          offset: Optional[int] = 0) -> Dict[str, Any]:
        """
        Get comments from the database
        
        Parameters:
        - article_id: Filter by article identifier
        - flagged_only: Only return flagged comments
        - min_aggressive: Minimum aggressive score (0.0 to 1.0)
        - min_hateful: Minimum hateful score (0.0 to 1.0)
        - min_racist: Minimum racist score (0.0 to 1.0)
        - limit: Maximum number of comments to return
        - offset: Offset for pagination
        """
        try:
            # Start with a base query
            from sqlalchemy import desc
            from osint_comments.models import Comment, Article
            
            query = self.integration.session.query(Comment)
            
            # Apply filters
            if article_id:
                article = self.integration.repository.get_article_by_identifier(article_id)
                if not article:
                    return {
                        "status": "error",
                        "message": f"Article not found: {article_id}"
                    }
                query = query.filter(Comment.article_id == article.id)
            
            if flagged_only:
                query = query.filter(Comment.is_flagged == True)
            
            # Apply score filters
            if min_aggressive is not None:
                query = query.filter(Comment.aggressive_score >= min_aggressive)
                
            if min_hateful is not None:
                query = query.filter(Comment.hateful_score >= min_hateful)
                
            if min_racist is not None:
                query = query.filter(Comment.racist_score >= min_racist)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            query = query.order_by(desc(Comment.created_at)).offset(offset).limit(limit)
            
            # Execute query
            comments = query.all()
            
            # Convert to dictionaries
            comments_data = []
            for comment in comments:
                # Get the article for this comment
                article = self.integration.session.query(Article).filter(Article.id == comment.article_id).first()
                
                comments_data.append({
                    "id": comment.id,
                    "message": comment.message,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
                    "score": comment.score,
                    "article_id": comment.article_id,
                    "article_title": article.title if article else None,
                    "article_identifier": article.identifier if article else None,
                    "user_id": comment.user_id,
                    "is_analyzed": comment.is_analyzed,
                    "is_flagged": comment.is_flagged,
                    "aggressive_score": comment.aggressive_score,
                    "hateful_score": comment.hateful_score,
                    "racist_score": comment.racist_score,
                    "analysis_explanation": comment.analysis_explanation
                })
            
            return {
                "status": "success",
                "comments": comments_data,
                "total": total_count
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting comments: {str(e)}"
            }
