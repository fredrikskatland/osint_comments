# llm_client.py
import json
import logging
from typing import Dict, Any, Optional
import openai

from config import OPENAI_API_KEY, OPENAI_MODEL, ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class OpenAIClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OpenAIClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not hasattr(self, "client"):
            self.api_key = api_key or OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OpenAI API key is required. Set it in config.py or pass it to the constructor.")
            
            self.model = model or OPENAI_MODEL
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI client initialized with model: {self.model}")

    def analyze_comment(self, comment_text: str) -> Dict[str, Any]:
        """
        Analyze a comment using the OpenAI API.
        
        Args:
            comment_text: The text of the comment to analyze
            
        Returns:
            A dictionary containing the analysis results
        """
        try:
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(comment_text=comment_text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a content moderation assistant that analyzes comments for harmful content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Use deterministic output for consistent analysis
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Extract the content from the response
            content = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                analysis = json.loads(content)
                logger.debug(f"Successfully analyzed comment: {analysis}")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Raw response: {content}")
                # Return a default analysis with error information
                return {
                    "aggressive": 0.0,
                    "hateful": 0.0,
                    "racist": 0.0,
                    "explanation": f"Error parsing response: {e}",
                    "error": True
                }
                
        except Exception as e:
            logger.error(f"Error analyzing comment with OpenAI: {e}")
            # Return a default analysis with error information
            return {
                "aggressive": 0.0,
                "hateful": 0.0,
                "racist": 0.0,
                "explanation": f"Error analyzing comment: {e}",
                "error": True
            }
