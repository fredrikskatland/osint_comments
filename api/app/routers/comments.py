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
        # Log gathering process
        await websocket_manager.log(
            f"Gathering comments for {'all articles' if article_id is None else f'article {article_id}'}",
            level="info",
            operation="gather",
            entity_id=article_id
        )
        
        # Call the method and await it
        result = await integration.gather_comments(
            article_id=article_id,
            limit=limit
        )
        
        if result["status"] == "success":
            new_comments = result["new_comments"]
            
            # Log completion
            await websocket_manager.log(
                f"Gathered {new_comments} new comments",
                level="info",
                operation="gather",
                entity_id=article_id
            )
            
            # Log final completion
            await websocket_manager.log(
                f"Comment gathering completed successfully: {new_comments} new comments",
                level="info",
                operation="gather",
                entity_id=article_id
            )
            
            return result
        else:
            # Log error from the result
            await websocket_manager.log(
                f"Error during comment gathering: {result['message']}",
                level="error",
                operation="gather",
                entity_id=article_id
            )
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
