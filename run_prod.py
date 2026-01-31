"""Production server using gunicorn with uvicorn workers."""

import os
import subprocess
import sys

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 4))
    
    # Gunicorn command
    cmd = [
        "gunicorn",
        "app.main:app",
        "-w", str(workers),  # Number of worker processes
        "-k", "uvicorn.workers.UvicornWorker",  # Use uvicorn workers
        "--bind", f"{host}:{port}",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
    ]
    
    # Add reload for development if requested
    if os.getenv("RELOAD", "false").lower() == "true":
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running gunicorn: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Gunicorn not found. Install with: pip install gunicorn")
        print("Or use run_dev.py for development (uvicorn with auto-reload)")
        sys.exit(1)
