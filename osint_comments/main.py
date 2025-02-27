"""
Main entry point for the OSINT Comments Core.

This module allows the OSINT Comments Core to be run directly with:
python -m osint_comments.main
"""
import sys
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from .models import Base, Article, Comment
from .repository import Repository
from .api_client import APIClient
from .kafka_producer import KafkaProducer
from .llm_client import OpenAIClient
from . import config

# Set up logging
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)
console = Console()


def setup_database(db_path: str):
    """
    Set up the database connection.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        Tuple of (engine, session, repository)
    """
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repository = Repository(session)
    return engine, session, repository


def crawl_articles(args):
    """
    Crawl articles from e24.no and save them to the database.
    
    Args:
        args: Command-line arguments
    """
    from crawler.web_scraper import E24Scraper
    from crawler.crawler_service import CrawlerService
    
    # Set up database
    _, session, repository = setup_database(args.db_path)
    
    # Set up crawler
    scraper = E24Scraper()
    crawler_service = CrawlerService(
        scraper=scraper,
        repository=None,  # We'll handle saving articles ourselves
        kafka_producer=None,
        cache_dir=args.cache_dir
    )
    
    # Crawl articles
    console.print(f"[bold green]Crawling articles from e24.no (pages: {args.pages})[/bold green]")
    articles = crawler_service.crawl_recent_articles(pages=args.pages)
    console.print(f"[bold]Found {len(articles)} articles[/bold]")
    
    # Process articles
    articles_with_comments = []
    for article in articles:
        # Process the article content if needed
        if args.process_content and not article.content:
            crawler_service.process_article_content(article)
        
        # Save to our database
        db_article = repository.save_article_from_crawler(article)
        
        # Track articles with comments
        if article.has_comments:
            articles_with_comments.append(article)
    
    # Print summary
    console.print(f"[bold green]Saved {len(articles)} articles to database[/bold green]")
    console.print(f"[bold]Found {len(articles_with_comments)} articles with comments[/bold]")
    
    # Print statistics
    stats = repository.get_article_stats()
    table = Table(title="Article Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    for key, value in stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)


def gather_comments(args):
    """
    Gather comments for articles that have comments but haven't had their comments gathered yet.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    _, session, repository = setup_database(args.db_path)
    
    # Set up API client
    api_client = APIClient()
    
    # Set up Kafka producer if needed
    kafka_producer = None
    if args.publish_to_kafka:
        kafka_producer = KafkaProducer(
            bootstrap_servers=args.kafka_servers,
            topic=config.RAW_COMMENTS_TOPIC
        )
    
    # Get articles that need comments gathered
    if args.article_id:
        # Process a specific article
        article = repository.get_article_by_identifier(args.article_id)
        if not article:
            console.print(f"[bold red]Article not found: {args.article_id}[/bold red]")
            return
        
        articles = [article]
    else:
        # Get articles with comments not gathered yet
        articles = repository.get_articles_with_comments_not_gathered(limit=args.limit)
    
    console.print(f"[bold green]Gathering comments for {len(articles)} articles[/bold green]")
    
    # Process each article
    total_comments = 0
    new_comments = 0
    
    for article in articles:
        console.print(f"Processing article: {article.title}")
        
        # Fetch comments from the API
        try:
            data = api_client.fetch_comments(article.identifier)
            items = data.get("items", [])
            console.print(f"  Fetched {len(items)} comments")
            
            # Process each comment
            article_comments = 0
            article_new_comments = 0
            
            for item in items:
                user_data = item.get("user", {})
                external_id = user_data.get("id")
                name = user_data.get("name")
                display_name = user_data.get("displayName")
                
                # Get or create user
                user = repository.get_or_create_user(external_id, name, display_name)
                
                # Add comment
                comment, created = repository.add_comment(item, article, user)
                
                article_comments += 1
                if created:
                    article_new_comments += 1
                    
                    # Publish to Kafka if enabled
                    if kafka_producer:
                        kafka_producer.send_message(comment.to_dict())
            
            # Update article status
            repository.mark_article_comments_gathered(article)
            
            console.print(f"  Processed {article_comments} comments ({article_new_comments} new)")
            total_comments += article_comments
            new_comments += article_new_comments
            
        except Exception as e:
            console.print(f"[bold red]Error processing article {article.identifier}: {e}[/bold red]")
    
    # Print summary
    console.print(f"[bold green]Processed {total_comments} comments ({new_comments} new) for {len(articles)} articles[/bold green]")
    
    # Print statistics
    comment_stats = repository.get_comment_stats()
    article_stats = repository.get_article_stats()
    
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    for key, value in article_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    for key, value in comment_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)


def analyze_comments(args):
    """
    Analyze comments that haven't been analyzed yet.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    _, session, repository = setup_database(args.db_path)
    
    # Set up LLM client
    llm_client = OpenAIClient()
    
    # Set up Kafka producer if needed
    kafka_producer = None
    if args.publish_to_kafka:
        kafka_producer = KafkaProducer(
            bootstrap_servers=args.kafka_servers,
            topic=config.FLAGGED_COMMENTS_TOPIC
        )
    
    # Get comments to analyze
    if args.article_id:
        # Get a specific article
        article = repository.get_article_by_identifier(args.article_id)
        if not article:
            console.print(f"[bold red]Article not found: {args.article_id}[/bold red]")
            return
        
        # Get comments for this article that haven't been analyzed
        comments = session.query(Comment).filter(
            Comment.article_id == article.id,
            Comment.is_analyzed == False
        ).all()
    else:
        # Get comments that haven't been analyzed yet
        comments = repository.get_comments_not_analyzed(limit=args.limit)
    
    console.print(f"[bold green]Analyzing {len(comments)} comments[/bold green]")
    
    # Process each comment
    analyzed_count = 0
    flagged_count = 0
    error_count = 0
    
    for comment in comments:
        try:
            console.print(f"Analyzing comment ID {comment.id}")
            
            # Analyze the comment
            analysis_result = llm_client.analyze_text(comment.message)
            
            # Update the comment with the analysis results
            repository.update_comment_analysis(comment, analysis_result)
            
            analyzed_count += 1
            if comment.is_flagged:
                flagged_count += 1
                console.print(f"  [bold yellow]Flagged comment: {comment.message[:50]}...[/bold yellow]")
                
                # Publish to Kafka if enabled
                if kafka_producer:
                    kafka_producer.send_message({
                        "comment_id": comment.id,
                        "message": comment.message,
                        "article_id": comment.article_id,
                        "analysis": {
                            "aggressive_score": comment.aggressive_score,
                            "hateful_score": comment.hateful_score,
                            "racist_score": comment.racist_score,
                            "is_flagged": comment.is_flagged,
                            "explanation": comment.analysis_explanation
                        }
                    })
        
        except Exception as e:
            console.print(f"[bold red]Error analyzing comment {comment.id}: {e}[/bold red]")
            error_count += 1
    
    # Mark articles as analyzed
    if args.article_id:
        # Mark the specific article
        article = repository.get_article_by_identifier(args.article_id)
        if article:
            repository.mark_article_comments_analyzed(article)
    else:
        # Get all articles with comments gathered but not analyzed
        articles = repository.get_articles_with_comments_not_analyzed()
        
        # Check if all comments for each article have been analyzed
        for article in articles:
            unanalyzed_count = session.query(Comment).filter(
                Comment.article_id == article.id,
                Comment.is_analyzed == False
            ).count()
            
            if unanalyzed_count == 0:
                repository.mark_article_comments_analyzed(article)
    
    # Print summary
    console.print(f"[bold green]Analyzed {analyzed_count} comments ({flagged_count} flagged, {error_count} errors)[/bold green]")
    
    # Print statistics
    comment_stats = repository.get_comment_stats()
    article_stats = repository.get_article_stats()
    
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    for key, value in article_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    for key, value in comment_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)


def show_stats(args):
    """
    Show statistics about the database.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    _, session, repository = setup_database(args.db_path)
    
    # Get statistics
    article_stats = repository.get_article_stats()
    comment_stats = repository.get_comment_stats()
    
    # Print statistics
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    for key, value in article_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    for key, value in comment_stats.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)


def main():
    """
    Main entry point for the OSINT Comments Core.
    """
    parser = argparse.ArgumentParser(description="OSINT Comments Core")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl articles from e24.no")
    crawl_parser.add_argument("--pages", type=int, default=3, help="Number of pages to crawl (default: 3)")
    crawl_parser.add_argument("--db-path", default="osint_comments.db", help="Path to the SQLite database")
    crawl_parser.add_argument("--cache-dir", default="./cache", help="Directory for caching crawled articles")
    crawl_parser.add_argument("--process-content", action="store_true", help="Process article content")
    crawl_parser.set_defaults(func=crawl_articles)
    
    # Gather comments command
    gather_parser = subparsers.add_parser("gather", help="Gather comments for articles")
    gather_parser.add_argument("--article-id", help="Identifier for a specific article")
    gather_parser.add_argument("--limit", type=int, default=None, help="Maximum number of articles to process")
    gather_parser.add_argument("--db-path", default="osint_comments.db", help="Path to the SQLite database")
    gather_parser.add_argument("--kafka-servers", default="localhost:9092", help="Kafka bootstrap servers")
    gather_parser.add_argument("--publish-to-kafka", action="store_true", help="Publish comments to Kafka")
    gather_parser.set_defaults(func=gather_comments)
    
    # Analyze comments command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze comments for harmful content")
    analyze_parser.add_argument("--article-id", help="Identifier for a specific article")
    analyze_parser.add_argument("--limit", type=int, default=None, help="Maximum number of comments to analyze")
    analyze_parser.add_argument("--db-path", default="osint_comments.db", help="Path to the SQLite database")
    analyze_parser.add_argument("--kafka-servers", default="localhost:9092", help="Kafka bootstrap servers")
    analyze_parser.add_argument("--publish-to-kafka", action="store_true", help="Publish flagged comments to Kafka")
    analyze_parser.set_defaults(func=analyze_comments)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics about the database")
    stats_parser.add_argument("--db-path", default="osint_comments.db", help="Path to the SQLite database")
    stats_parser.set_defaults(func=show_stats)
    
    args = parser.parse_args()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
