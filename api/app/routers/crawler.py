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
        # Create a custom E24Integration instance with logging
        from osint_comments.e24_integration import E24Integration
        from osint_comments.models import Article
        
        # Create a custom E24Integration with the same db_path
        e24_integration = E24Integration(db_path=integration.integration.db_path)
        
        # Patch the crawler_service to log each article
        original_save_article = e24_integration.repository.save_article_from_crawler
        
        async def save_article_with_logging(crawler_article):
            # Call the original method
            article = original_save_article(crawler_article)
            
            # Log the article
            await websocket_manager.log(
                f"Crawled article: {article.title}",
                level="info",
                operation="crawl",
                entity_id=article.identifier
            )
            
            return article
        
        # Replace the method with our logging version
        e24_integration.repository.save_article_from_crawler = save_article_with_logging
        
        # Start crawling
        await websocket_manager.log(
            f"Fetching articles from e24.no...",
            level="info",
            operation="crawl"
        )
        
        # Call the crawl_articles method directly on our custom integration
        articles = []
        
        # Use sitemap crawling
        await websocket_manager.log(
            f"Using sitemap crawling with months_back={months_back}",
            level="info",
            operation="crawl"
        )
        
        crawler_articles = e24_integration.crawler_service.crawl_articles(
            months_back=months_back,
            max_articles=max_articles
        )
        
        await websocket_manager.log(
            f"Found {len(crawler_articles)} articles in sitemap",
            level="info",
            operation="crawl"
        )
        
        # Process each article
        for i, crawler_article in enumerate(crawler_articles):
            try:
                # Log progress
                if i % 5 == 0 or i == len(crawler_articles) - 1:
                    await websocket_manager.log(
                        f"Processing article {i+1}/{len(crawler_articles)}",
                        level="info",
                        operation="crawl"
                    )
                
                # Process the article content if needed
                if process_content and not crawler_article.content:
                    await websocket_manager.log(
                        f"Processing content for article: {crawler_article.title}",
                        level="info",
                        operation="crawl",
                        entity_id=crawler_article.identifier
                    )
                    e24_integration.crawler_service.process_article_content(crawler_article)
                
                # Save to our database with logging
                article = await save_article_with_logging(crawler_article)
                articles.append(article)
                
            except Exception as article_error:
                await websocket_manager.log(
                    f"Error processing article {crawler_article.title}: {str(article_error)}",
                    level="error",
                    operation="crawl",
                    entity_id=crawler_article.identifier if hasattr(crawler_article, 'identifier') else None
                )
        
        # Restore the original method
        e24_integration.repository.save_article_from_crawler = original_save_article
        
        # Create a result similar to what integration.crawl_articles would return
        result = {
            "status": "success",
            "articles_count": len(articles),
            "message": f"Successfully crawled {len(articles)} articles"
        }
        
        # Log completion
        await websocket_manager.log(
            f"Crawl completed: {len(articles)} articles processed",
            level="info",
            operation="crawl"
        )
        
        # Log statistics
        article_stats = e24_integration.repository.get_article_stats()
        await websocket_manager.log(
            f"Article statistics: {article_stats['total_articles']} total, {article_stats['articles_with_comments']} with comments",
            level="info",
            operation="crawl"
        )
        
        return result
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
    search: Optional[str] = None,
    has_comments: Optional[bool] = None,
    comments_gathered: Optional[bool] = None,
    comments_analyzed: Optional[bool] = None,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get articles from the database with filtering options
    
    Parameters:
    - limit: Maximum number of articles to return
    - offset: Offset for pagination
    - search: Search query for article title
    - has_comments: Filter articles that have comments
    - comments_gathered: Filter articles that have had comments gathered
    - comments_analyzed: Filter articles that have had comments analyzed
    """
    return await integration.get_articles(
        limit=limit, 
        offset=offset,
        search=search,
        has_comments=has_comments,
        comments_gathered=comments_gathered,
        comments_analyzed=comments_analyzed
    )

@router.get("/articles/{article_id}")
async def get_article_by_id(
    article_id: str,
    integration: E24IntegrationAdapter = Depends(get_integration)
):
    """
    Get an article by its identifier
    """
    return await integration.get_article_by_id(article_id)
