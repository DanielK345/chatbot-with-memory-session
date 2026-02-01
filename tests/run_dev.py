"""Development server with auto-reload for local testing."""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    
    # Run with auto-reload enabled for development
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes
        reload_dirs=["app"],  # Only watch app directory for changes
        log_level="info"
    )
