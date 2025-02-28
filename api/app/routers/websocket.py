# api/app/routers/websocket.py
"""
Router for WebSocket connections.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_service import websocket_manager

router = APIRouter()

import logging
import traceback

logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time logging and updates.
    """
    client = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"WebSocket connection request from {client}")
    
    try:
        await websocket_manager.connect(websocket)
        logger.info(f"WebSocket connection established with {client}")
        
        # Send a welcome message
        await websocket_manager.log(f"Connected to WebSocket server from {client}", level="info", operation="system")
        
        # Keep the connection alive
        while True:
            # Wait for messages from the client (not used currently, but could be used for commands)
            data = await websocket.receive_text()
            # Echo back the message (for testing)
            await websocket.send_text(f"Message received: {data}")
            
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected from {client}: code={e.code}")
        websocket_manager.disconnect(websocket)
        
    except Exception as e:
        logger.error(f"WebSocket error with {client}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            websocket_manager.disconnect(websocket)
        except:
            pass
