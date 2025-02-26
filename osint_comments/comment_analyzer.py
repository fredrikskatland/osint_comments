# comment_analyzer.py
import logging
import time
from typing import Dict, Any, Optional

from .config import ANALYSIS_THRESHOLD, FLAGGED_COMMENTS_TOPIC
from .llm_client import OpenAIClient
from .kafka_producer import KafkaProducer
from .analysis_models import CommentAnalysis

logger = logging.getLogger(__name__)

class CommentAnalyzer:
    """
    Analyzes comments for harmful content and publishes the results to Kafka.
    """
    
    def __init__(self, llm_client: Optional[OpenAIClient] = None, 
                 kafka_producer: Optional[KafkaProducer] = None,
                 threshold: float = ANALYSIS_THRESHOLD):
        """
        Initialize the CommentAnalyzer.
        
        Args:
            llm_client: OpenAI client for analyzing comments
            kafka_producer: Kafka producer for publishing results
            threshold: Threshold for flagging comments
        """
        self.llm_client = llm_client or OpenAIClient()
        self.kafka_producer = kafka_producer or KafkaProducer(topic=FLAGGED_COMMENTS_TOPIC)
        self.threshold = threshold
        logger.info(f"CommentAnalyzer initialized with threshold: {threshold}")
        
    def analyze_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a comment and publish the results to Kafka if flagged.
        
        Args:
            comment_data: Raw comment data
            
        Returns:
            The analysis result
        """
        try:
            # Extract the comment text
            comment_text = comment_data.get('content', '')
            comment_id = comment_data.get('id')
            
            if not comment_text:
                logger.warning(f"Empty comment text for comment ID {comment_id}, skipping analysis")
                return {"error": "Empty comment text"}
                
            logger.info(f"Analyzing comment ID {comment_id}")
            
            # Analyze the comment
            analysis_result = self.llm_client.analyze_text(comment_text)
            
            # Check if the comment should be flagged
            is_flagged = analysis_result.get('is_flagged', False)
            
            # Log the analysis results
            if is_flagged:
                logger.warning(f"Comment ID {comment_id} flagged as problematic")
                
                # Publish the flagged comment to Kafka
                self._publish_flagged_comment(comment_data, analysis_result)
            else:
                logger.info(f"Comment ID {comment_id} not flagged")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing comment: {e}")
            return {"error": str(e)}
            
    def _publish_flagged_comment(self, comment_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> None:
        """
        Publish a flagged comment to Kafka.
        
        Args:
            comment_data: Raw comment data
            analysis_result: Analysis result
        """
        try:
            # Create a message with the comment data and analysis result
            message = {
                "id": comment_data.get('id'),
                "content": comment_data.get('content'),
                "author": comment_data.get('author'),
                "timestamp": comment_data.get('timestamp'),
                "article_id": comment_data.get('article_id'),
                "analysis": analysis_result
            }
            
            # Publish to Kafka
            self.kafka_producer.send_message(message)
            
            logger.info(f"Published flagged comment ID {comment_data.get('id')} to Kafka")
            
        except Exception as e:
            logger.error(f"Error publishing flagged comment to Kafka: {e}")
