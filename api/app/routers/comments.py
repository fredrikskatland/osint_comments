# api/app/routers/comments.py
"""
Router for comments-related endpoints.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional, Dict, Any, List
from ..adapters.e24_integration_adapter import E24IntegrationAdapter
from ..services.websocket_service import websocket_manager

router = APIRouter()

def get_integration():
    """Dependency to get E24IntegrationAdapter instance"""
    return E24IntegrationAdapter()

async def gather_with_logging(
    article_id: Optional[str] = None,
    limit: Optional[int] = None,
    integration: Optional[E24IntegrationAdapter] = None
):
    """
    Gather comments with real-time logging via WebSocket
    """
    if integration is None:
        integration = E24IntegrationAdapter()
    
    # Log start
    await websocket_manager.log(
        f"Starting comment gathering: article_id={article_id}, limit={limit}",
        level="info",
        operation="gather",
        entity_id=article_id
    )
    
    try:
        # Create a custom E24Integration instance with logging
        from osint_comments.e24_integration import E24Integration
        from osint_comments.models import Article, Comment
        
        # Create a custom E24Integration with the same db_path
        e24_integration = E24Integration(db_path=integration.integration.db_path)
        
        # Patch the repository to log each comment
        original_add_comment = e24_integration.repository.add_comment
        
        async def add_comment_with_logging(item, article, user):
            # Call the original method
            comment, created = original_add_comment(item, article, user)
            
            # Log the comment
            status = "New" if created else "Existing"
            await websocket_manager.log(
                f"{status} comment: {comment.message[:50]}{'...' if len(comment.message) > 50 else ''}",
                level="info",
                operation="gather",
                entity_id=article.identifier
            )
            
            return comment, created
        
        # Replace the method with our logging version
        e24_integration.repository.add_comment = add_comment_with_logging
        
        # Get articles that need comments gathered
        if article_id:
            # Process a specific article
            article = e24_integration.repository.get_article_by_identifier(article_id)
            if not article:
                await websocket_manager.log(
                    f"Article not found: {article_id}",
                    level="error",
                    operation="gather",
                    entity_id=article_id
                )
                return {
                    "status": "error",
                    "message": f"Article not found: {article_id}"
                }
            
            articles = [article]
        else:
            # Get articles with comments not gathered yet
            articles = e24_integration.repository.get_articles_with_comments_not_gathered(limit=limit)
        
        await websocket_manager.log(
            f"Gathering comments for {len(articles)} articles",
            level="info",
            operation="gather"
        )
        
        # Process each article
        total_comments = 0
        new_comments = 0
        articles_with_comments = 0
        
        for article in articles:
            await websocket_manager.log(
                f"Processing article: {article.title}",
                level="info",
                operation="gather",
                entity_id=article.identifier
            )
            
            # Fetch comments from the API
            try:
                data = e24_integration.api_client.fetch_comments(article.identifier)
                items = data.get("items", [])
                
                await websocket_manager.log(
                    f"Fetched {len(items)} comments for article: {article.title}",
                    level="info",
                    operation="gather",
                    entity_id=article.identifier
                )
                
                # Update article has_comments and comment_count based on API response
                has_comments = len(items) > 0
                article.has_comments = has_comments
                article.comment_count = len(items)
                
                if has_comments:
                    articles_with_comments += 1
                
                # Process each comment
                article_comments = 0
                article_new_comments = 0
                
                for item in items:
                    user_data = item.get("user", {})
                    external_id = user_data.get("id")
                    name = user_data.get("name")
                    display_name = user_data.get("displayName")
                    
                    # Get or create user
                    user = e24_integration.repository.get_or_create_user(external_id, name, display_name)
                    
                    # Add comment with logging
                    comment, created = await add_comment_with_logging(item, article, user)
                    
                    article_comments += 1
                    if created:
                        article_new_comments += 1
                
                # Update article status
                e24_integration.repository.mark_article_comments_gathered(article)
                
                await websocket_manager.log(
                    f"Processed {article_comments} comments ({article_new_comments} new) for article: {article.title}",
                    level="info",
                    operation="gather",
                    entity_id=article.identifier
                )
                
                total_comments += article_comments
                new_comments += article_new_comments
                
            except Exception as e:
                await websocket_manager.log(
                    f"Error processing article {article.identifier}: {e}",
                    level="error",
                    operation="gather",
                    entity_id=article.identifier
                )
                # Still mark as gathered to avoid retrying failed articles
                e24_integration.repository.mark_article_comments_gathered(article)
        
        # Restore the original method
        e24_integration.repository.add_comment = original_add_comment
        
        # Log summary
        await websocket_manager.log(
            f"Processed {total_comments} comments ({new_comments} new) for {len(articles)} articles",
            level="info",
            operation="gather"
        )
        
        await websocket_manager.log(
            f"Found {articles_with_comments} articles with comments",
            level="info",
            operation="gather"
        )
        
        # Create a result similar to what integration.gather_comments would return
        result = {
            "status": "success",
            "new_comments": new_comments,
            "message": f"Successfully gathered {new_comments} new comments"
        }
        
        return result
    except Exception as e:
        # Log error
        await websocket_manager.log(
            f"Error during comment gathering: {str(e)}",
            level="error",
            operation="gather",
            entity_id=article_id
        )
        raise

@router.post("/gather")
async def gather_comments(
    background_tasks: BackgroundTasks,
    article_id: Optional[str] = None,
    limit: Optional[int] = None,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Gather comments for articles
    """
    # Log the request
    await websocket_manager.log(
        f"Received gather comments request: article_id={article_id}, limit={limit}",
        level="info",
        operation="gather",
        entity_id=article_id
    )
    
    # Run in background to avoid timeout
    background_tasks.add_task(
        gather_with_logging,
        article_id=article_id,
        limit=limit,
        integration=integration
    )
    
    return {
        "status": "started",
        "message": "Gathering comments in the background",
        "params": {
            "article_id": article_id,
            "limit": limit
        }
    }

@router.get("/list")
async def get_comments(
    article_id: Optional[str] = None,
    flagged_only: bool = False,
    min_aggressive: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_hateful: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_racist: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get comments from the database
    
    - **article_id**: Filter by article identifier
    - **flagged_only**: Only return flagged comments
    - **min_aggressive**: Minimum aggressive score (0.0 to 1.0)
    - **min_hateful**: Minimum hateful score (0.0 to 1.0)
    - **min_racist**: Minimum racist score (0.0 to 1.0)
    - **limit**: Maximum number of comments to return
    - **offset**: Offset for pagination
    """
    return await integration.get_comments(
        article_id=article_id,
        flagged_only=flagged_only,
        min_aggressive=min_aggressive,
        min_hateful=min_hateful,
        min_racist=min_racist,
        limit=limit,
        offset=offset
    )

@router.get("/articles/{article_id}")
async def get_article_comments(
    article_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get comments for a specific article
    """
    return await integration.get_comments(
        article_id=article_id,
        limit=limit,
        offset=offset
    )

@router.get("/flagged")
async def get_flagged_comments(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get flagged comments
    """
    return await integration.get_comments(
        flagged_only=True,
        limit=limit,
        offset=offset
    )
