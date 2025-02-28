# api/app/routers/crawler.py
"""
Router for crawler-related endpoints.
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

async def crawl_with_logging(
    process_content: bool = False,
    months_back: int = 1,
    max_articles: Optional[int] = None,
    integration: Optional[E24IntegrationAdapter] = None
):
    """
    Crawl articles with real-time logging via WebSocket
    """
    if integration is None:
        integration = E24IntegrationAdapter()
    
    # Log start
    await websocket_manager.log(
        f"Starting crawl: months_back={months_back}, max_articles={max_articles}, process_content={process_content}",
        level="info",
        operation="crawl"
    )
    
    try:
        # Start crawling
        # We need to directly call the integration's method and await it
        result = await integration.crawl_articles(
            process_content=process_content,
            months_back=months_back,
            max_articles=max_articles
        )
        
        # Check if the result is successful
        if result["status"] == "success":
            articles_count = result["articles_count"]
            
            # Log completion
            await websocket_manager.log(
                f"Crawl completed: {articles_count} articles found",
                level="info",
                operation="crawl"
            )
            
            # We don't have access to the actual article objects here,
            # just the count, so we can't log individual articles
            
            # Log completion
            await websocket_manager.log(
                f"Crawl task completed successfully: {articles_count} articles processed",
                level="info",
                operation="crawl"
            )
            
            return result
        else:
            # Log error from the result
            await websocket_manager.log(
                f"Error during crawl: {result['message']}",
                level="error",
                operation="crawl"
            )
            return result
        
        # No need to restore anything since we're not patching methods anymore
    except Exception as e:
        # Log error
        await websocket_manager.log(
            f"Error during crawl: {str(e)}",
            level="error",
            operation="crawl"
        )
        raise

@router.post("/crawl")
async def crawl_articles(
    background_tasks: BackgroundTasks,
    process_content: bool = False,
    months_back: int = 1,
    max_articles: Optional[int] = None,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Crawl articles from e24.no
    """
    # Log the request
    await websocket_manager.log(
        f"Received crawl request: months_back={months_back}, max_articles={max_articles}, process_content={process_content}",
        level="info",
        operation="crawl"
    )
    
    # Run in background to avoid timeout
    background_tasks.add_task(
        crawl_with_logging,
        process_content=process_content,
        months_back=months_back,
        max_articles=max_articles,
        integration=integration
    )
    
    return {
        "status": "started",
        "message": "Crawling articles in the background",
        "params": {
            "process_content": process_content,
            "months_back": months_back,
            "max_articles": max_articles
        }
    }

@router.get("/stats")
async def get_stats(integration: E24IntegrationAdapter = Depends(get_integration)):
    """
    Get statistics about articles and comments
    """
    return await integration.get_stats()

@router.get("/articles")
async def get_articles(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get articles from the database
    """
    return await integration.get_articles(limit=limit, offset=offset)

@router.get("/articles/{article_id}")
async def get_article_by_id(
    article_id: str,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get an article by its identifier
    """
    return await integration.get_article_by_id(article_id)
