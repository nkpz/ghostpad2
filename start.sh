#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Ghostpad...${NC}"

# Install uv if not available
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}Installing uv...${NC}"
    pip install uv
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    uv venv
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
uv sync


# Build frontend if dist doesn't exist or if any file in src is newer than dist
if [ ! -d "frontend/dist" ] || [ "frontend/package.json" -nt "frontend/dist" ] || find frontend/src -type f -newer frontend/dist | grep -q .; then
    echo -e "${BLUE}Building React frontend...${NC}"
    cd frontend
    # Check if node_modules exists, if not install
    if [ ! -d "node_modules" ]; then
        npm install
    fi
#    npm run build
    npm run build-dev
    cd ..
fi

echo -e "${GREEN}Starting server at http://127.0.0.1:8000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"

# Run the application in the virtual environment
# uv run python main.py
uv run python api/main.py
