# api/app/services/websocket_service.py
"""
WebSocket service for real-time logging and updates.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

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
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Send recent log history to the new client
        for log in self.log_history:
            await websocket.send_text(log.to_json())
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        self.active_connections.remove(websocket)
    
    async def broadcast(self, log_message: LogMessage):
        """Broadcast a message to all connected clients"""
        # Add to history
        self.log_history.append(log_message)
        
        # Trim history if needed
        if len(self.log_history) > self.max_history_size:
            self.log_history = self.log_history[-self.max_history_size:]
        
        # Broadcast to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(log_message.to_json())
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
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
