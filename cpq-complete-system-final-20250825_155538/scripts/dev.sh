#!/bin/bash

# CPQ System Development Startup Script
echo "🚀 Starting CPQ System in development mode..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites are met${NC}"

# Function to setup backend
setup_backend() {
    echo -e "${BLUE}🐍 Setting up backend...${NC}"
    cd apps/api
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    
    # Initialize database
    echo -e "${YELLOW}🗄️ Initializing database...${NC}"
    python scripts/init_db.py
    
    cd ../..
    echo -e "${GREEN}✅ Backend setup complete${NC}"
}

# Function to setup frontend
setup_frontend() {
    echo -e "${BLUE}🌐 Setting up frontend...${NC}"
    cd apps/web
    
    # Install dependencies
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
    
    cd ../..
    echo -e "${GREEN}✅ Frontend setup complete${NC}"
}

# Function to start development servers
start_dev_servers() {
    echo -e "${BLUE}🚀 Starting development servers...${NC}"
    
    # Install concurrently at root level if not present
    if ! npm list concurrently >/dev/null 2>&1; then
        echo -e "${YELLOW}📦 Installing concurrently...${NC}"
        npm install
    fi
    
    # Start both servers
    echo -e "${GREEN}🎉 Starting both frontend and backend servers...${NC}"
    echo -e "${BLUE}Frontend: http://localhost:5173${NC}"
    echo -e "${BLUE}Backend: http://localhost:5000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
    
    npm run dev
}

# Main execution
main() {
    # Check if --setup flag is provided
    if [[ "$1" == "--setup" ]]; then
        echo -e "${BLUE}🔧 Running full setup...${NC}"
        setup_backend
        setup_frontend
        echo -e "${GREEN}🎉 Setup complete! Run './scripts/dev.sh' to start development servers${NC}"
        exit 0
    fi
    
    # Check if backend virtual environment exists
    if [ ! -d "apps/api/venv" ]; then
        echo -e "${YELLOW}⚠️ Backend not set up. Running setup first...${NC}"
        setup_backend
    fi
    
    # Check if frontend node_modules exists
    if [ ! -d "apps/web/node_modules" ]; then
        echo -e "${YELLOW}⚠️ Frontend not set up. Running setup first...${NC}"
        setup_frontend
    fi
    
    # Start development servers
    start_dev_servers
}

# Show usage if help requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "CPQ System Development Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --setup    Run full setup (install dependencies, init database)"
    echo "  --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0          # Start development servers"
    echo "  $0 --setup  # Run full setup first"
    exit 0
fi

# Run main function
main "$@"