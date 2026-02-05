#!/bin/bash
# Construction AI Suite - Startup Script for macOS/Linux
#
# Usage: ./scripts/start.sh [--demo] [--clean]
# 
# Options:
#   --demo   Run in demo mode with sample data
#   --clean  Remove logs and previous state before starting
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Construction AI Suite - Starting Application${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Parse arguments
DEMO_MODE=false
CLEAN_MODE=false

for arg in "$@"; do
    case $arg in
        --demo)
            DEMO_MODE=true
            ;;
        --clean)
            CLEAN_MODE=true
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: ./scripts/start.sh [--demo] [--clean]"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"
python3 --version

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install/update dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r backend/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create required directories
echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p logs models data config
chmod 755 logs models data config
echo -e "${GREEN}✓ Directories ready${NC}"

# Setup environment
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Set DEMO_MODE if requested
        if [ "$DEMO_MODE" = true ]; then
            sed -i 's/^DEMO_MODE=false/DEMO_MODE=true/' .env
            echo -e "${GREEN}✓ Demo mode enabled in .env${NC}"
        fi
    else
        echo -e "${RED}⚠ .env.example not found - using defaults${NC}"
    fi
fi

# Load environment
set -a
if [ -f ".env" ]; then
    source .env
else
    echo -e "${YELLOW}⚠ No .env file found - using defaults${NC}"
fi
set +a

# Clean mode
if [ "$CLEAN_MODE" = true ]; then
    echo -e "${YELLOW}Cleaning logs and cache...${NC}"
    rm -rf logs/* __pycache__ backend/__pycache__ backend/app/__pycache__ .pytest_cache
    rm -rf backend/tests/__pycache__ frontend_phase10/node_modules/.vite
    echo -e "${GREEN}✓ Cache cleaned${NC}"
fi

# Verify Phase 14 is integrated
echo -e "${YELLOW}Verifying Phase 14 integration...${NC}"
python3 -c "from backend.app.phase14_logging import setup_logging; from backend.app.phase14_errors import safe_api_call; print('✓ Phase 14 modules available')" 2>/dev/null || {
    echo -e "${YELLOW}⚠ Phase 14 not integrated yet (optional for demo)${NC}"
}

# Start application
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Starting Construction AI Suite...${NC}"
echo ""
echo -e "${YELLOW}Application Configuration:${NC}"
echo "  Environment: ${FLASK_ENV:-development}"
echo "  Debug Mode: ${FLASK_DEBUG:-false}"
echo "  Log Level: ${LOG_LEVEL:-INFO}"
echo "  Demo Mode: ${DEMO_MODE}"
echo ""
echo -e "${YELLOW}Access Points:${NC}"
echo "  Backend API: http://localhost:5000"
echo "  Health Check: http://localhost:5000/health"
echo "  Phase 9 Outputs: http://localhost:5000/phase9/outputs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Location: $(pwd)/logs/"
echo "  View: tail -f logs/construction_ai.log"
echo ""
echo -e "${YELLOW}To stop the server, press Ctrl+C${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Run the application
cd backend
export PYTHONUNBUFFERED=1
export FLASK_APP=app/main.py

if [ "$DEMO_MODE" = true ]; then
    export DEMO_MODE=true
    echo -e "${GREEN}🎬 Running in DEMO MODE${NC}"
fi

python3 -m flask run --host=0.0.0.0 --port=5000
