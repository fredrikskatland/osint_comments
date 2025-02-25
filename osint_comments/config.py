# config.py
import os

# Base URL for the comments API (for publication "e24")
API_BASE_URL = "https://cmmnts-api.i.bt.no/v1/publications/e24/"

# Endpoint template – the article_identifier should be something like "article:e24:Jbwa97"
COMMENTS_ENDPOINT_TEMPLATE = "{article_identifier}/comments"

# Default query parameters (you can adjust these later)
DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0
DEFAULT_ORDER = "score DESC"
DEFAULT_REPLIES = "ASC"

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
RAW_COMMENTS_TOPIC = "raw-comments"
FLAGGED_COMMENTS_TOPIC = "flagged-comments"

# Analysis configuration
ANALYSIS_THRESHOLD = 0.7  # Threshold for flagging comments

# Prompt template for comment analysis
ANALYSIS_PROMPT_TEMPLATE = """
Analyze the following comment for harmful content. Evaluate it for:
1. Aggressive language (hostility, threats, excessive anger)
2. Hateful content (bigotry, discrimination)
3. Racist content (racial slurs, stereotypes, prejudice)

Provide a confidence score from 0.0 to 1.0 for each category, where:
- 0.0 means definitely not present
- 1.0 means definitely present

Comment: "{comment_text}"

Respond with a JSON object in the following format:
{{
  "aggressive": {{score}},
  "hateful": {{score}},
  "racist": {{score}},
  "explanation": "brief explanation of your analysis"
}}
"""
