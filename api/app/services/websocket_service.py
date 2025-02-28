# api/app/services/websocket_service.py
"""
WebSocket service for real-time logging and updates.
"""
import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class LogMessage:
    """
    Represents a log message in the system.
    """
    def __init__(
        self, 
        message: str, 
        level: str = "info", 
        operation: str = "system", 
        entity_id: Optional[str] = None
    ):
        self.timestamp = datetime.now().isoformat()
        self.message = message
        self.level = level  # info, warning, error
        self.operation = operation  # crawl, gather, analyze
        self.entity_id = entity_id  # article_id, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "message": self.message,
            "level": self.level,
            "operation": self.operation,
            "entity_id": self.entity_id
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages.
    """
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.log_history: List[LogMessage] = []
        self.max_history_size = 1000  # Maximum number of log messages to keep
    
    async def connect(self, websocket: WebSocket):
        """Connect a new client"""
        client = f"{websocket.client.host}:{websocket.client.port}"
        logger.info(f"Accepting WebSocket connection from {client}")
        
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            logger.info(f"WebSocket connection accepted from {client}")
            
            # Send recent log history to the new client
            logger.info(f"Sending {len(self.log_history)} log history items to {client}")
            for log in self.log_history:
                try:
                    await websocket.send_text(log.to_json())
                except Exception as e:
                    logger.error(f"Error sending log history to {client}: {str(e)}")
                    logger.error(traceback.format_exc())
                    break
                    
            logger.info(f"Log history sent to {client}")
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection from {client}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        try:
            client = f"{websocket.client.host}:{websocket.client.port}" if hasattr(websocket, 'client') else "unknown"
            logger.info(f"Disconnecting WebSocket client {client}")
            
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket client {client} disconnected")
            else:
                logger.warning(f"WebSocket client {client} not found in active connections")
                
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket client: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def broadcast(self, log_message: LogMessage):
        """Broadcast a message to all connected clients"""
        # Add to history
        self.log_history.append(log_message)
        
        # Trim history if needed
        if len(self.log_history) > self.max_history_size:
            self.log_history = self.log_history[-self.max_history_size:]
        
        # Log the broadcast
        logger.debug(f"Broadcasting message to {len(self.active_connections)} clients: {log_message.message}")
        
        # Broadcast to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                client = f"{connection.client.host}:{connection.client.port}" if hasattr(connection, 'client') else "unknown"
                await connection.send_text(log_message.to_json())
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            try:
                client = f"{connection.client.host}:{connection.client.port}" if hasattr(connection, 'client') else "unknown"
                logger.info(f"Removing disconnected client {client}")
                self.active_connections.remove(connection)
            except Exception as e:
                logger.error(f"Error removing disconnected client: {str(e)}")
    
    async def log(
        self, 
        message: str, 
        level: str = "info", 
        operation: str = "system", 
        entity_id: Optional[str] = None
    ):
        """Log a message and broadcast it to all clients"""
        log_message = LogMessage(message, level, operation, entity_id)
        await self.broadcast(log_message)

# Create a singleton instance
websocket_manager = WebSocketManager()
