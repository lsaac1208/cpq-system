#!/bin/bash

# CPQ System Setup Script
echo "🔧 Setting up CPQ System..."

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
    echo -e "${RED}❌ Python 3.11+ is required${NC}"
    echo -e "${YELLOW}Please install Python 3.11 or higher${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js 18+ is required${NC}"
    echo -e "${YELLOW}Please install Node.js 18 or higher${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is required${NC}"
    echo -e "${YELLOW}Please install npm${NC}"
    exit 1
fi

# Check versions
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
NODE_VERSION=$(node --version | cut -c2-)

echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"
echo -e "${GREEN}✅ Node.js version: $NODE_VERSION${NC}"

# Install root dependencies
echo -e "${BLUE}📦 Installing root dependencies...${NC}"
npm install

# Setup backend
echo -e "${BLUE}🐍 Setting up backend...${NC}"
cd apps/api

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✅ Backend dependencies installed${NC}"

# Go back to root
cd ../..

# Setup frontend  
echo -e "${BLUE}🌐 Setting up frontend...${NC}"
cd apps/web

# Install dependencies
echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
npm install

echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# Go back to root
cd ../..

# Initialize database
echo -e "${BLUE}🗄️ Initializing database...${NC}"
cd apps/api
source venv/bin/activate
python scripts/init_db.py
cd ../..

echo -e "${GREEN}✅ Database initialized with sample data${NC}"

# Create .env files if they don't exist
if [ ! -f "apps/api/.env" ]; then
    echo -e "${YELLOW}📝 Creating backend .env file...${NC}"
    cp apps/api/.env.example apps/api/.env
fi

if [ ! -f "apps/web/.env" ]; then
    echo -e "${YELLOW}📝 Frontend .env file already exists${NC}"
fi

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}To start development:${NC}"
echo -e "  ${YELLOW}./scripts/dev.sh${NC}      # Start both servers"
echo -e "  ${YELLOW}npm run dev${NC}           # Alternative way"
echo ""
echo -e "${BLUE}Individual commands:${NC}"
echo -e "  ${YELLOW}npm run dev:api${NC}       # Backend only"
echo -e "  ${YELLOW}npm run dev:web${NC}       # Frontend only"
echo ""
echo -e "${BLUE}Demo credentials:${NC}"
echo -e "  ${YELLOW}Admin: admin / admin123${NC}"
echo -e "  ${YELLOW}Sales: sales / sales123${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo -e "  ${YELLOW}Frontend: http://localhost:5173${NC}"
echo -e "  ${YELLOW}Backend:  http://localhost:5000${NC}"
echo -e "  ${YELLOW}API Health: http://localhost:5000/health${NC}"