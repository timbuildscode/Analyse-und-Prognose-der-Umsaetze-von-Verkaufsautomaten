#!/bin/bash

# Start the FastAPI server

echo "Starting API..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo " uv is not installed. Please install uv first."
    exit 1
fi

# Install dependencies 
echo "Installing dependencies..."
uv sync

# Start the API server on port 8000
echo "Starting server..."
cd "$(dirname "$0")"
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000