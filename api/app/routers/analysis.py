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
        # Log analysis process
        await websocket_manager.log(
            f"Analyzing comments for {'all articles' if article_id is None else f'article {article_id}'}",
            level="info",
            operation="analyze",
            entity_id=article_id
        )
        
        # Call the method and await it
        result = await integration.analyze_comments(
            article_id=article_id,
            limit=limit
        )
        
        if result["status"] == "success":
            stats = result["stats"]
            
            # Log completion
            await websocket_manager.log(
                f"Analysis completed: {stats['analyzed']} comments analyzed, {stats['flagged']} flagged",
                level="info",
                operation="analyze",
                entity_id=article_id
            )
            
            # Log final completion
            await websocket_manager.log(
                f"Analysis task completed successfully: {stats['analyzed']} comments analyzed, {stats['flagged']} flagged",
                level="info",
                operation="analyze",
                entity_id=article_id
            )
            
            return result
        else:
            # Log error from the result
            await websocket_manager.log(
                f"Error during analysis: {result['message']}",
                level="error",
                operation="analyze",
                entity_id=article_id
            )
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
