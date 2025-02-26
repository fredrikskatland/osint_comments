"""
Main entry point for the e24.no crawler.

This module allows the crawler to be run directly with:
python -m crawler
"""
from .cli import main

if __name__ == "__main__":
    main()
