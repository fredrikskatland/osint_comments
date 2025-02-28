# api/app/main.py
"""
Main FastAPI application for the OSINT Comments project.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import crawler, comments, analysis, websocket

app = FastAPI(
    title="OSINT Comments API",
    description="API for the OSINT Comments project",
    version="0.1.0"
)

# Add CORS middleware to allow requests from the Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers
)

# Include routers
app.include_router(crawler.router, prefix="/api/crawler", tags=["crawler"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the OSINT Comments API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
