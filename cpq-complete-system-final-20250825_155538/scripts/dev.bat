@echo off
REM CPQ System Development Startup Script for Windows
echo 🚀 Starting CPQ System in development mode...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed or not in PATH
    pause
    exit /b 1
)

echo ✅ All prerequisites are met

REM Handle setup flag
if "%1"=="--setup" goto setup

REM Check if backend virtual environment exists
if not exist "apps\api\venv" (
    echo ⚠️ Backend not set up. Running setup first...
    goto setup_backend
)

REM Check if frontend node_modules exists  
if not exist "apps\web\node_modules" (
    echo ⚠️ Frontend not set up. Running setup first...
    goto setup_frontend
)

goto start_servers

:setup
echo 🔧 Running full setup...
goto setup_backend

:setup_backend
echo 🐍 Setting up backend...
cd apps\api

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo 📦 Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Initialize database
echo 🗄️ Initializing database...
python scripts\init_db.py

cd ..\..
echo ✅ Backend setup complete

if "%1"=="--setup" goto setup_frontend
goto start_servers

:setup_frontend
echo 🌐 Setting up frontend...
cd apps\web

REM Install dependencies
echo 📦 Installing Node.js dependencies...
npm install

cd ..\..
echo ✅ Frontend setup complete

if "%1"=="--setup" (
    echo 🎉 Setup complete! Run 'scripts\dev.bat' to start development servers
    pause
    exit /b 0
)

:start_servers
echo 🚀 Starting development servers...

REM Install concurrently at root level if not present
npm list concurrently >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing concurrently...
    npm install
)

REM Start both servers
echo 🎉 Starting both frontend and backend servers...
echo Frontend: http://localhost:5173
echo Backend: http://localhost:5000
echo Press Ctrl+C to stop both servers

npm run dev

pause