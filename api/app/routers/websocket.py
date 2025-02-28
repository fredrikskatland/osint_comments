# api/app/routers/websocket.py
"""
Router for WebSocket connections.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_service import websocket_manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time logging and updates.
    """
    await websocket_manager.connect(websocket)
    try:
        # Send a welcome message
        await websocket_manager.log("Connected to WebSocket server", level="info", operation="system")
        
        # Keep the connection alive
        while True:
            # Wait for messages from the client (not used currently, but could be used for commands)
            data = await websocket.receive_text()
            # Echo back the message (for testing)
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
