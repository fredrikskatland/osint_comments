# config.py

# Base URL for the comments API (for publication "e24")
API_BASE_URL = "https://cmmnts-api.i.bt.no/v1/publications/e24/"

# Endpoint template – the article_identifier should be something like "article:e24:Jbwa97"
COMMENTS_ENDPOINT_TEMPLATE = "{article_identifier}/comments"

# Default query parameters (you can adjust these later)
DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0
DEFAULT_ORDER = "score DESC"
DEFAULT_REPLIES = "ASC"
