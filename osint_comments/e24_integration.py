"""
Integration module for the e24.no crawler with the osint_comments project.

This module provides functionality to fetch articles with comments from e24.no
and process them using the osint_comments analysis pipeline.
"""
import logging
import sys
import os
import argparse
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import from crawler package
import crawler.web_scraper
import crawler.crawler_service
import crawler.article_repository
import crawler.models

# Import from osint_comments package
from .models import Base, Article, Comment, User
from .repository import Repository
from .api_client import APIClient
from .llm_client import OpenAIClient
from . import config

# Configure logging
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


class E24Integration:
    """
    Integration class for the e24.no crawler with the osint_comments project.
    
    This class provides a unified workflow for:
    1. Crawling articles from e24.no
    2. Gathering comments for articles with comments
    3. Analyzing comments for harmful content
    """
    
    def __init__(self, db_path: str = "osint_comments.db", kafka_bootstrap_servers: Optional[str] = None):
        """
        Initialize the integration.
        
        Args:
            db_path: Path to the SQLite database file
            kafka_bootstrap_servers: Kafka bootstrap servers (optional)
        """
        # Set up database
        self.db_path = db_path
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        
        # Set up SQLAlchemy engine and session
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create repository
        self.repository = Repository(self.session)
        
        # Set up API client
        self.api_client = APIClient()
        
        # Set up LLM client
        self.llm_client = OpenAIClient()
        
        # Set up Kafka producers if Kafka is enabled
        self.raw_comments_producer = None
        self.flagged_comments_producer = None
        
        if kafka_bootstrap_servers:
            try:
                from .kafka_producer import KafkaProducer
                
                self.raw_comments_producer = KafkaProducer(
                    bootstrap_servers=kafka_bootstrap_servers,
                    topic=config.RAW_COMMENTS_TOPIC
                )
                
                self.flagged_comments_producer = KafkaProducer(
                    bootstrap_servers=kafka_bootstrap_servers,
                    topic=config.FLAGGED_COMMENTS_TOPIC
                )
                
                console.print("[bold green]Kafka producers initialized[/bold green]")
            except Exception as e:
                console.print(f"[bold yellow]Warning: Failed to initialize Kafka producers: {e}[/bold yellow]")
                console.print("[bold yellow]Continuing without Kafka support[/bold yellow]")
        
        # Set up crawler components
        self.scraper = crawler.web_scraper.E24Scraper()
        self.crawler_service = crawler.crawler_service.CrawlerService(
            scraper=self.scraper,
            repository=None,  # We'll handle saving articles ourselves
            kafka_producer=None,  # We'll handle Kafka publishing ourselves
            cache_dir="./e24_cache"
        )
    
    def crawl_articles(self, pages: int = 3, process_content: bool = False, 
                       crawl_method: str = "standard", related_articles: int = 3, 
                       depth: int = 2) -> List[Article]:
        """
        Crawl articles from e24.no and save them to the database.
        
        Args:
            pages: Number of pages to crawl
            process_content: Whether to process article content
            crawl_method: Crawling method to use ("standard" or "depth")
            related_articles: Number of related articles to follow from each article (for depth crawling)
            depth: Maximum depth to crawl (for depth crawling)
            
        Returns:
            List of articles with comments
        """
        # Determine crawl method
        if crawl_method == "depth":
            console.print(f"[bold green]Crawling articles from e24.no with depth crawling[/bold green]")
            console.print(f"[bold]Front pages: {pages}, Related articles: {related_articles}, Depth: {depth}[/bold]")
            
            # Use depth crawling
            crawler_articles = self.crawler_service.crawl_with_depth(
                pages=pages,
                max_related=related_articles,
                depth=depth
            )
        else:
            # Use regular crawling
            console.print(f"[bold green]Crawling articles from e24.no (pages: {pages})[/bold green]")
            crawler_articles = self.crawler_service.crawl_recent_articles(pages=pages)
        
        console.print(f"[bold]Found {len(crawler_articles)} articles[/bold]")
        
        # Process articles
        articles_with_comments = []
        for crawler_article in crawler_articles:
            # Process the article content if needed
            if process_content and not crawler_article.content:
                self.crawler_service.process_article_content(crawler_article)
            
            # Save to our database
            article = self.repository.save_article_from_crawler(crawler_article)
            
            # Track articles with comments
            if article.has_comments:
                articles_with_comments.append(article)
        
        # Print summary
        console.print(f"[bold green]Saved {len(crawler_articles)} articles to database[/bold green]")
        console.print(f"[bold]Found {len(articles_with_comments)} articles with comments[/bold]")
        
        # Print statistics
        self.print_stats()
        
        return articles_with_comments
    
    def gather_comments(self, article_id: Optional[str] = None, limit: Optional[int] = None, 
                        publish_to_kafka: bool = False) -> int:
        """
        Gather comments for articles that have comments but haven't had their comments gathered yet.
        
        Args:
            article_id: Identifier for a specific article (optional)
            limit: Maximum number of articles to process (optional)
            publish_to_kafka: Whether to publish comments to Kafka
            
        Returns:
            Number of new comments gathered
        """
        # Get articles that need comments gathered
        if article_id:
            # Process a specific article
            article = self.repository.get_article_by_identifier(article_id)
            if not article:
                console.print(f"[bold red]Article not found: {article_id}[/bold red]")
                return 0
            
            articles = [article]
        else:
            # Get articles with comments not gathered yet
            articles = self.repository.get_articles_with_comments_not_gathered(limit=limit)
        
        console.print(f"[bold green]Gathering comments for {len(articles)} articles[/bold green]")
        
        # Process each article
        total_comments = 0
        new_comments = 0
        
        for article in articles:
            console.print(f"Processing article: {article.title}")
            
            # Fetch comments from the API
            try:
                data = self.api_client.fetch_comments(article.identifier)
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
                    user = self.repository.get_or_create_user(external_id, name, display_name)
                    
                    # Add comment
                    comment, created = self.repository.add_comment(item, article, user)
                    
                    article_comments += 1
                    if created:
                        article_new_comments += 1
                        
                        # Publish to Kafka if enabled
                        if publish_to_kafka and self.raw_comments_producer:
                            self.raw_comments_producer.send_message(comment.to_dict())
                
                # Update article status
                self.repository.mark_article_comments_gathered(article)
                
                console.print(f"  Processed {article_comments} comments ({article_new_comments} new)")
                total_comments += article_comments
                new_comments += article_new_comments
                
            except Exception as e:
                console.print(f"[bold red]Error processing article {article.identifier}: {e}[/bold red]")
        
        # Print summary
        console.print(f"[bold green]Processed {total_comments} comments ({new_comments} new) for {len(articles)} articles[/bold green]")
        
        # Print statistics
        self.print_stats()
        
        return new_comments
    
    def analyze_comments(self, article_id: Optional[str] = None, limit: Optional[int] = None, 
                         publish_to_kafka: bool = False) -> Dict[str, int]:
        """
        Analyze comments that haven't been analyzed yet.
        
        Args:
            article_id: Identifier for a specific article (optional)
            limit: Maximum number of comments to analyze (optional)
            publish_to_kafka: Whether to publish flagged comments to Kafka
            
        Returns:
            Dictionary with analysis statistics
        """
        # Get comments to analyze
        if article_id:
            # Get a specific article
            article = self.repository.get_article_by_identifier(article_id)
            if not article:
                console.print(f"[bold red]Article not found: {article_id}[/bold red]")
                return {"analyzed": 0, "flagged": 0, "errors": 0}
            
            # Get comments for this article that haven't been analyzed
            comments = self.session.query(Comment).filter(
                Comment.article_id == article.id,
                Comment.is_analyzed == False
            ).all()
        else:
            # Get comments that haven't been analyzed yet
            comments = self.repository.get_comments_not_analyzed(limit=limit)
        
        console.print(f"[bold green]Analyzing {len(comments)} comments[/bold green]")
        
        # Process each comment
        analyzed_count = 0
        flagged_count = 0
        error_count = 0
        
        for comment in comments:
            try:
                console.print(f"Analyzing comment ID {comment.id}")
                
                # Analyze the comment
                analysis_result = self.llm_client.analyze_text(comment.message)
                
                # Update the comment with the analysis results
                self.repository.update_comment_analysis(comment, analysis_result)
                
                analyzed_count += 1
                if comment.is_flagged:
                    flagged_count += 1
                    console.print(f"  [bold yellow]Flagged comment: {comment.message[:50]}...[/bold yellow]")
                    
                    # Publish to Kafka if enabled
                    if publish_to_kafka and self.flagged_comments_producer:
                        self.flagged_comments_producer.send_message({
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
        if article_id:
            # Mark the specific article
            article = self.repository.get_article_by_identifier(article_id)
            if article:
                self.repository.mark_article_comments_analyzed(article)
        else:
            # Get all articles with comments gathered but not analyzed
            articles = self.repository.get_articles_with_comments_not_analyzed()
            
            # Check if all comments for each article have been analyzed
            for article in articles:
                unanalyzed_count = self.session.query(Comment).filter(
                    Comment.article_id == article.id,
                    Comment.is_analyzed == False
                ).count()
                
                if unanalyzed_count == 0:
                    self.repository.mark_article_comments_analyzed(article)
        
        # Print summary
        console.print(f"[bold green]Analyzed {analyzed_count} comments ({flagged_count} flagged, {error_count} errors)[/bold green]")
        
        # Print statistics
        self.print_stats()
        
        return {
            "analyzed": analyzed_count,
            "flagged": flagged_count,
            "errors": error_count
        }
    
    def print_stats(self):
        """Print statistics about the database."""
        # Get statistics
        article_stats = self.repository.get_article_stats()
        comment_stats = self.repository.get_comment_stats()
        
        # Print statistics
        table = Table(title="Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        for key, value in article_stats.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        for key, value in comment_stats.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(table)
    
    def run_full_pipeline(self, pages: int = 3, crawl_method: str = "standard", 
                          related_articles: int = 3, depth: int = 2, 
                          limit: Optional[int] = None, publish_to_kafka: bool = False) -> None:
        """
        Run the full pipeline: crawl, gather comments, and analyze.
        
        Args:
            pages: Number of pages to crawl
            crawl_method: Crawling method to use ("standard" or "depth")
            related_articles: Number of related articles to follow from each article (for depth crawling)
            depth: Maximum depth to crawl (for depth crawling)
            limit: Maximum number of articles/comments to process
            publish_to_kafka: Whether to publish to Kafka
        """
        console.print("[bold green]Running full pipeline[/bold green]")
        
        # Step 1: Crawl articles
        console.print("\n[bold]Step 1: Crawling articles[/bold]")
        articles_with_comments = self.crawl_articles(
            pages=pages, 
            process_content=True,
            crawl_method=crawl_method,
            related_articles=related_articles,
            depth=depth
        )
        
        # Step 2: Gather comments
        console.print("\n[bold]Step 2: Gathering comments[/bold]")
        new_comments = self.gather_comments(limit=limit, publish_to_kafka=publish_to_kafka)
        
        # Step 3: Analyze comments
        console.print("\n[bold]Step 3: Analyzing comments[/bold]")
        analysis_stats = self.analyze_comments(limit=limit, publish_to_kafka=publish_to_kafka)
        
        # Print final summary
        console.print("\n[bold green]Pipeline complete![/bold green]")
        console.print(f"Found {len(articles_with_comments)} articles with comments")
        console.print(f"Gathered {new_comments} new comments")
        console.print(f"Analyzed {analysis_stats['analyzed']} comments ({analysis_stats['flagged']} flagged, {analysis_stats['errors']} errors)")
        
        # Print final statistics
        self.print_stats()


def main():
    """Main entry point for the integration."""
    parser = argparse.ArgumentParser(
        description="Integrate e24.no crawler with osint_comments"
    )
    
    # Add common arguments
    parser.add_argument(
        "--db-path", 
        type=str, 
        default="osint_comments.db", 
        help="Path to SQLite database file (default: osint_comments.db)"
    )
    
    parser.add_argument(
        "--kafka-servers", 
        type=str, 
        default=None, 
        help="Kafka bootstrap servers (default: None, disables Kafka)"
    )
    
    parser.add_argument(
        "--publish-to-kafka", 
        action="store_true", 
        help="Publish to Kafka (requires --kafka-servers)"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl articles from e24.no")
    crawl_parser.add_argument(
        "--pages", 
        type=int, 
        default=3, 
        help="Number of pages to crawl (default: 3)"
    )
    crawl_parser.add_argument(
        "--process-content", 
        action="store_true", 
        help="Process article content"
    )
    
    # Add crawl method options
    crawl_parser.add_argument(
        "--crawl-method", 
        choices=["standard", "depth"], 
        default="standard",
        help="Crawling method to use (standard or depth)"
    )
    crawl_parser.add_argument(
        "--related-articles", 
        type=int, 
        default=3,
        help="Number of related articles to follow from each article (for depth crawling)"
    )
    crawl_parser.add_argument(
        "--depth", 
        type=int, 
        default=2,
        help="Maximum depth to crawl (for depth crawling)"
    )
    
    # Gather command
    gather_parser = subparsers.add_parser("gather", help="Gather comments for articles")
    gather_parser.add_argument(
        "--article-id", 
        type=str, 
        help="Identifier for a specific article"
    )
    gather_parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Maximum number of articles to process"
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze comments for harmful content")
    analyze_parser.add_argument(
        "--article-id", 
        type=str, 
        help="Identifier for a specific article"
    )
    analyze_parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Maximum number of comments to analyze"
    )
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run the full pipeline")
    pipeline_parser.add_argument(
        "--pages", 
        type=int, 
        default=3, 
        help="Number of pages to crawl (default: 3)"
    )
    pipeline_parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Maximum number of articles/comments to process"
    )
    
    # Add crawl method options to pipeline command
    pipeline_parser.add_argument(
        "--crawl-method", 
        choices=["standard", "depth"], 
        default="standard",
        help="Crawling method to use (standard or depth)"
    )
    pipeline_parser.add_argument(
        "--related-articles", 
        type=int, 
        default=3,
        help="Number of related articles to follow from each article (for depth crawling)"
    )
    pipeline_parser.add_argument(
        "--depth", 
        type=int, 
        default=2,
        help="Maximum depth to crawl (for depth crawling)"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    # Check if publish_to_kafka is set but kafka_servers is not
    if args.publish_to_kafka and not args.kafka_servers:
        console.print("[bold red]Error: --publish-to-kafka requires --kafka-servers[/bold red]")
        return
    
    # Create integration
    integration = E24Integration(
        db_path=args.db_path,
        kafka_bootstrap_servers=args.kafka_servers
    )
    
    # Run the appropriate command
    if args.command == "crawl":
        integration.crawl_articles(
            pages=args.pages, 
            process_content=args.process_content,
            crawl_method=args.crawl_method,
            related_articles=args.related_articles,
            depth=args.depth
        )
    elif args.command == "gather":
        integration.gather_comments(
            article_id=args.article_id,
            limit=args.limit,
            publish_to_kafka=args.publish_to_kafka
        )
    elif args.command == "analyze":
        integration.analyze_comments(
            article_id=args.article_id,
            limit=args.limit,
            publish_to_kafka=args.publish_to_kafka
        )
    elif args.command == "pipeline":
        integration.run_full_pipeline(
            pages=args.pages,
            crawl_method=args.crawl_method,
            related_articles=args.related_articles,
            depth=args.depth,
            limit=args.limit,
            publish_to_kafka=args.publish_to_kafka
        )
    elif args.command == "stats":
        integration.print_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
