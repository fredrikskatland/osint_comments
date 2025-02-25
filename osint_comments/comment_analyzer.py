# comment_analyzer.py
import logging
import time
from typing import Dict, Any, Optional

from config import ANALYSIS_THRESHOLD, FLAGGED_COMMENTS_TOPIC
from llm_client import OpenAIClient
from kafka_producer import KafkaProducerClient
from analysis_models import CommentAnalysis

logger = logging.getLogger(__name__)

class CommentAnalyzer:
    """
    Analyzes comments for harmful content and publishes the results to Kafka.
    """
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, 
                 kafka_producer: Optional[KafkaProducerClient] = None,
                 threshold: float = ANALYSIS_THRESHOLD):
        """
        Initialize the CommentAnalyzer.
        
        Args:
            openai_client: OpenAI client for analyzing comments
            kafka_producer: Kafka producer for publishing results
            threshold: Threshold for flagging comments
        """
        self.openai_client = openai_client or OpenAIClient()
        self.kafka_producer = kafka_producer or KafkaProducerClient()
        self.threshold = threshold
        logger.info(f"CommentAnalyzer initialized with threshold: {threshold}")
        
    def process_comment(self, comment_data: Dict[str, Any]) -> CommentAnalysis:
        """
        Process a comment by analyzing it and publishing the results to Kafka.
        
        Args:
            comment_data: Raw comment data from Kafka
            
        Returns:
            The CommentAnalysis instance
        """
        try:
            # Extract the comment text
            comment_text = comment_data.get('message', '')
            comment_id = comment_data.get('id')
            
            if not comment_text:
                logger.warning(f"Empty comment text for comment ID {comment_id}, skipping analysis")
                return None
                
            logger.info(f"Processing comment ID {comment_id}")
            logger.debug(f"Comment text: {comment_text[:100]}...")
            
            # Analyze the comment
            analysis_result = self.openai_client.analyze_comment(comment_text)
            
            # Create a CommentAnalysis instance
            comment_analysis = CommentAnalysis.from_raw_analysis(
                comment_data=comment_data,
                analysis=analysis_result,
                threshold=self.threshold
            )
            
            # Log the analysis results
            if comment_analysis.is_flagged:
                logger.warning(
                    f"Comment ID {comment_id} flagged as problematic: "
                    f"{comment_analysis.max_category} ({comment_analysis.max_score:.2f})"
                )
            else:
                logger.info(
                    f"Comment ID {comment_id} not flagged: "
                    f"max score {comment_analysis.max_score:.2f} for {comment_analysis.max_category}"
                )
                
            # Publish the analysis results to Kafka
            self._publish_analysis(comment_analysis)
            
            return comment_analysis
            
        except Exception as e:
            logger.error(f"Error processing comment: {e}")
            return None
            
    def _publish_analysis(self, analysis: CommentAnalysis) -> None:
        """
        Publish the analysis results to Kafka.
        
        Args:
            analysis: The CommentAnalysis instance to publish
        """
        try:
            # Convert the analysis to a dictionary
            analysis_dict = analysis.to_dict()
            
            # Publish to Kafka
            self.kafka_producer.send_message(FLAGGED_COMMENTS_TOPIC, analysis_dict)
            
            logger.info(f"Published analysis for comment ID {analysis.comment_id} to Kafka")
            
        except Exception as e:
            logger.error(f"Error publishing analysis to Kafka: {e}")
