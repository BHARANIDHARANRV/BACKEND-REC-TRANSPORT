#!/usr/bin/env python3
"""
Local server startup script for RecTransport API
Run this script to start the FastAPI server locally
"""

import uvicorn
import os
from main import app

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting RecTransport API server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}/docs")
    print(f"🔧 Health check: http://{host}:{port}/health")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    ) 