# api/app/routers/analysis.py
"""
Router for analysis-related endpoints.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from ..adapters.e24_integration_adapter import E24IntegrationAdapter
from ..services.websocket_service import websocket_manager

router = APIRouter()

def get_integration():
    """Dependency to get E24IntegrationAdapter instance"""
    return E24IntegrationAdapter()

async def analyze_with_logging(
    article_id: Optional[str] = None,
    limit: Optional[int] = None,
    integration: Optional[E24IntegrationAdapter] = None
):
    """
    Analyze comments with real-time logging via WebSocket
    """
    if integration is None:
        integration = E24IntegrationAdapter()
    
    # Log start
    await websocket_manager.log(
        f"Starting comment analysis: article_id={article_id}, limit={limit}",
        level="info",
        operation="analyze",
        entity_id=article_id
    )
    
    try:
        # Create a custom E24Integration instance with logging
        from osint_comments.e24_integration import E24Integration
        from osint_comments.models import Article, Comment
        
        # Create a custom E24Integration with the same db_path
        e24_integration = E24Integration(db_path=integration.integration.db_path)
        
        # Patch the repository to log each comment analysis
        original_update_comment_analysis = e24_integration.repository.update_comment_analysis
        
        async def update_comment_analysis_with_logging(comment, analysis_result):
            # Store original values to check if flagged status changes
            was_flagged = comment.is_flagged if hasattr(comment, 'is_flagged') else False
            
            # Call the original method
            original_update_comment_analysis(comment, analysis_result)
            
            # Get the article for this comment
            article = e24_integration.session.query(Article).filter(Article.id == comment.article_id).first()
            article_identifier = article.identifier if article else None
            
            # Log the analysis result
            if comment.is_flagged:
                flag_status = "newly flagged" if not was_flagged else "already flagged"
                await websocket_manager.log(
                    f"Comment {flag_status}: {comment.message[:50]}{'...' if len(comment.message) > 50 else ''} " +
                    f"(Aggressive: {comment.aggressive_score:.2f}, Hateful: {comment.hateful_score:.2f}, Racist: {comment.racist_score:.2f})",
                    level="warning",
                    operation="analyze",
                    entity_id=article_identifier
                )
            else:
                await websocket_manager.log(
                    f"Comment analyzed (not flagged): {comment.message[:50]}{'...' if len(comment.message) > 50 else ''} " +
                    f"(Aggressive: {comment.aggressive_score:.2f}, Hateful: {comment.hateful_score:.2f}, Racist: {comment.racist_score:.2f})",
                    level="info",
                    operation="analyze",
                    entity_id=article_identifier
                )
            
            return comment
        
        # Replace the method with our logging version
        e24_integration.repository.update_comment_analysis = update_comment_analysis_with_logging
        
        # Get comments to analyze
        if article_id:
            # Get a specific article
            article = e24_integration.repository.get_article_by_identifier(article_id)
            if not article:
                await websocket_manager.log(
                    f"Article not found: {article_id}",
                    level="error",
                    operation="analyze",
                    entity_id=article_id
                )
                return {
                    "status": "error",
                    "message": f"Article not found: {article_id}"
                }
            
            # Get comments for this article that haven't been analyzed
            comments = e24_integration.session.query(Comment).filter(
                Comment.article_id == article.id,
                Comment.is_analyzed == False
            ).all()
            
            await websocket_manager.log(
                f"Found {len(comments)} unanalyzed comments for article: {article.title}",
                level="info",
                operation="analyze",
                entity_id=article.identifier
            )
        else:
            # Get comments that haven't been analyzed yet
            comments = e24_integration.repository.get_comments_not_analyzed(limit=limit)
            
            await websocket_manager.log(
                f"Found {len(comments)} unanalyzed comments across all articles",
                level="info",
                operation="analyze"
            )
        
        # Process each comment
        analyzed_count = 0
        flagged_count = 0
        error_count = 0
        
        for i, comment in enumerate(comments):
            try:
                # Log progress periodically
                if i % 5 == 0 or i == len(comments) - 1:
                    await websocket_manager.log(
                        f"Analyzing comment {i+1}/{len(comments)}",
                        level="info",
                        operation="analyze"
                    )
                
                # Get the article for this comment
                article = e24_integration.session.query(Article).filter(Article.id == comment.article_id).first()
                
                await websocket_manager.log(
                    f"Analyzing comment ID {comment.id} from article: {article.title if article else 'Unknown'}",
                    level="info",
                    operation="analyze",
                    entity_id=article.identifier if article else None
                )
                
                # Analyze the comment
                analysis_result = e24_integration.llm_client.analyze_text(comment.message)
                
                # Update the comment with the analysis results (with logging)
                await update_comment_analysis_with_logging(comment, analysis_result)
                
                analyzed_count += 1
                if comment.is_flagged:
                    flagged_count += 1
            
            except Exception as e:
                await websocket_manager.log(
                    f"Error analyzing comment {comment.id}: {e}",
                    level="error",
                    operation="analyze",
                    entity_id=article.identifier if article else None
                )
                error_count += 1
        
        # Mark articles as analyzed
        if article_id:
            # Mark the specific article
            article = e24_integration.repository.get_article_by_identifier(article_id)
            if article:
                e24_integration.repository.mark_article_comments_analyzed(article)
                
                await websocket_manager.log(
                    f"Marked article as analyzed: {article.title}",
                    level="info",
                    operation="analyze",
                    entity_id=article.identifier
                )
        else:
            # Get all articles with comments gathered but not analyzed
            articles = e24_integration.repository.get_articles_with_comments_not_analyzed()
            
            # Check if all comments for each article have been analyzed
            for article in articles:
                unanalyzed_count = e24_integration.session.query(Comment).filter(
                    Comment.article_id == article.id,
                    Comment.is_analyzed == False
                ).count()
                
                if unanalyzed_count == 0:
                    e24_integration.repository.mark_article_comments_analyzed(article)
                    
                    await websocket_manager.log(
                        f"Marked article as analyzed: {article.title}",
                        level="info",
                        operation="analyze",
                        entity_id=article.identifier
                    )
        
        # Restore the original method
        e24_integration.repository.update_comment_analysis = original_update_comment_analysis
        
        # Log summary
        await websocket_manager.log(
            f"Analysis completed: {analyzed_count} comments analyzed, {flagged_count} flagged, {error_count} errors",
            level="info",
            operation="analyze",
            entity_id=article_id
        )
        
        # Create a result similar to what integration.analyze_comments would return
        result = {
            "status": "success",
            "stats": {
                "analyzed": analyzed_count,
                "flagged": flagged_count,
                "errors": error_count
            },
            "message": f"Successfully analyzed {analyzed_count} comments ({flagged_count} flagged)"
        }
        
        return result
    except Exception as e:
        # Log error
        await websocket_manager.log(
            f"Error during analysis: {str(e)}",
            level="error",
            operation="analyze",
            entity_id=article_id
        )
        raise

@router.post("/analyze")
async def analyze_comments(
    background_tasks: BackgroundTasks,
    article_id: Optional[str] = None,
    limit: Optional[int] = None,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Analyze comments for harmful content
    """
    # Log the request
    await websocket_manager.log(
        f"Received analyze comments request: article_id={article_id}, limit={limit}",
        level="info",
        operation="analyze",
        entity_id=article_id
    )
    
    # Run in background to avoid timeout
    background_tasks.add_task(
        analyze_with_logging,
        article_id=article_id,
        limit=limit,
        integration=integration
    )
    
    return {
        "status": "started",
        "message": "Analyzing comments in the background",
        "params": {
            "article_id": article_id,
            "limit": limit
        }
    }

@router.get("/flagged")
async def get_flagged_comments(
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get flagged comments
    """
    # This is a placeholder for now - we'll implement this later
    # when we add database access to get flagged comments
    return {
        "status": "success",
        "message": "This endpoint will return flagged comments"
    }
