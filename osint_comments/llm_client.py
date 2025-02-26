# llm_client.py
import json
import logging
from typing import Dict, Any, Optional
import openai

from .config import OPENAI_API_KEY, OPENAI_MODEL, ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Client for interacting with the OpenAI API.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (optional, defaults to config value)
            model: OpenAI model to use (optional, defaults to config value)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in config.py or pass it to the constructor.")
        
        self.model = model or OPENAI_MODEL
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI client initialized with model: {self.model}")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text using the OpenAI API.
        
        Args:
            text: The text to analyze
            
        Returns:
            A dictionary containing the analysis results
        """
        try:
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(comment_text=text)
            
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
                logger.debug(f"Successfully analyzed text: {analysis}")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Raw response: {content}")
                # Return a default analysis with error information
                return {
                    "sentiment": "neutral",
                    "toxicity": 0.0,
                    "is_flagged": False,
                    "explanation": f"Error parsing response: {e}",
                    "error": True
                }
                
        except Exception as e:
            logger.error(f"Error analyzing text with OpenAI: {e}")
            # Return a default analysis with error information
            return {
                "sentiment": "neutral",
                "toxicity": 0.0,
                "is_flagged": False,
                "explanation": f"Error analyzing text: {e}",
                "error": True
            }
