#!/usr/bin/env bash
set -euo pipefail

# Start Streamlit in headless mode on the $PORT provided by the platform
PORT=${PORT:-8501}

echo "Starting Streamlit on port ${PORT}"

exec streamlit run streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true
