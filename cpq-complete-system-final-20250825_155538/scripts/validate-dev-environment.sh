#!/bin/bash

# CPQ System Development Environment Validation Script
# This script validates that the complete development environment is properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="http://localhost:5173"
BACKEND_URL="http://localhost:5000"
API_HEALTH_ENDPOINT="/api/health"
TIMEOUT=10

# Validation results
VALIDATION_RESULTS=()
ERROR_COUNT=0
WARNING_COUNT=0

# Function to log validation results
log_result() {
    local status=$1
    local component=$2
    local message=$3
    
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC} - $component: $message"
            VALIDATION_RESULTS+=("✅ $component: PASS - $message")
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC} - $component: $message"
            VALIDATION_RESULTS+=("❌ $component: FAIL - $message")
            ((ERROR_COUNT++))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC} - $component: $message"
            VALIDATION_RESULTS+=("⚠️  $component: WARN - $message")
            ((WARNING_COUNT++))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC} - $component: $message"
            VALIDATION_RESULTS+=("ℹ️  $component: INFO - $message")
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is listening
check_port() {
    local port=$1
    if command_exists lsof; then
        lsof -i :$port >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -tuln | grep ":$port " >/dev/null 2>&1
    else
        # Fallback: try to connect
        timeout 2 bash -c "</dev/tcp/localhost/$port" >/dev/null 2>&1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local expected_status=$2
    local timeout=${3:-$TIMEOUT}
    
    if command_exists curl; then
        local response=$(curl -s -w "%{http_code}" -m $timeout "$url" 2>/dev/null || echo "000")
        local status_code="${response: -3}"
        if [[ "$status_code" == "$expected_status" ]]; then
            return 0
        else
            echo "Expected $expected_status, got $status_code"
            return 1
        fi
    else
        echo "curl not available"
        return 1
    fi
}

# Function to validate JSON response
validate_json_response() {
    local url=$1
    local expected_field=$2
    local expected_value=$3
    
    if command_exists curl && command_exists jq; then
        local response=$(curl -s -m $TIMEOUT "$url" 2>/dev/null)
        local field_value=$(echo "$response" | jq -r ".$expected_field" 2>/dev/null)
        
        if [[ "$field_value" == "$expected_value" ]]; then
            return 0
        else
            echo "Expected $expected_field='$expected_value', got '$field_value'"
            return 1
        fi
    else
        echo "curl or jq not available"
        return 1
    fi
}

echo -e "${BLUE}🔍 CPQ System Development Environment Validation${NC}"
echo "================================================================"
echo "Starting comprehensive environment validation..."
echo ""

# 1. Check Prerequisites
echo -e "${PURPLE}📋 Checking Prerequisites...${NC}"

if command_exists python3; then
    python_version=$(python3 --version 2>&1)
    log_result "PASS" "Python 3" "Available - $python_version"
else
    log_result "FAIL" "Python 3" "Not installed or not in PATH"
fi

if command_exists node; then
    node_version=$(node --version 2>&1)
    log_result "PASS" "Node.js" "Available - $node_version"
else
    log_result "FAIL" "Node.js" "Not installed or not in PATH"
fi

if command_exists npm; then
    npm_version=$(npm --version 2>&1)
    log_result "PASS" "npm" "Available - v$npm_version"
else
    log_result "FAIL" "npm" "Not installed or not in PATH"
fi

echo ""

# 2. Check Development Server Processes
echo -e "${PURPLE}🖥️  Checking Development Servers...${NC}"

if check_port 5173; then
    log_result "PASS" "Frontend Server" "Running on port 5173"
else
    log_result "FAIL" "Frontend Server" "Not running on port 5173"
fi

if check_port 5000; then
    log_result "PASS" "Backend Server" "Running on port 5000"
else
    log_result "FAIL" "Backend Server" "Not running on port 5000"
fi

echo ""

# 3. Check HTTP Endpoints
echo -e "${PURPLE}🌐 Checking HTTP Endpoints...${NC}"

# Frontend accessibility
if check_http "$FRONTEND_URL" "200"; then
    log_result "PASS" "Frontend HTTP" "Accessible at $FRONTEND_URL"
else
    log_result "FAIL" "Frontend HTTP" "Not accessible or returned unexpected status"
fi

# Backend health endpoint
backend_health_url="$BACKEND_URL$API_HEALTH_ENDPOINT"
if check_http "$backend_health_url" "200"; then
    log_result "PASS" "Backend HTTP" "Health endpoint accessible at $backend_health_url"
else
    log_result "FAIL" "Backend HTTP" "Health endpoint not accessible"
fi

echo ""

# 4. Check API Health Response
echo -e "${PURPLE}🏥 Checking API Health...${NC}"

if validate_json_response "$backend_health_url" "status" "healthy"; then
    log_result "PASS" "API Health" "Backend reports healthy status"
else
    if command_exists curl; then
        response=$(curl -s -m $TIMEOUT "$backend_health_url" 2>/dev/null || echo "No response")
        log_result "FAIL" "API Health" "Backend not healthy or invalid response: $response"
    else
        log_result "FAIL" "API Health" "Cannot validate - curl not available"
    fi
fi

echo ""

# 5. Check Proxy Configuration
echo -e "${PURPLE}🔄 Checking Proxy Configuration...${NC}"

proxy_health_url="$FRONTEND_URL$API_HEALTH_ENDPOINT"
if check_http "$proxy_health_url" "200"; then
    log_result "PASS" "Proxy Config" "Frontend can proxy API requests to backend"
else
    log_result "FAIL" "Proxy Config" "Frontend cannot proxy API requests to backend"
fi

echo ""

# 6. Check CORS Configuration
echo -e "${PURPLE}🔒 Checking CORS Configuration...${NC}"

if command_exists curl; then
    cors_response=$(curl -s -m $TIMEOUT \
        -H "Origin: $FRONTEND_URL" \
        -H "Content-Type: application/json" \
        -w "%{http_code}" \
        "$backend_health_url" 2>/dev/null || echo "000")
    
    cors_status="${cors_response: -3}"
    if [[ "$cors_status" == "200" ]]; then
        log_result "PASS" "CORS Config" "Backend accepts requests from frontend origin"
    else
        log_result "FAIL" "CORS Config" "Backend rejects requests from frontend origin (status: $cors_status)"
    fi
else
    log_result "WARN" "CORS Config" "Cannot validate - curl not available"
fi

echo ""

# 7. Check Database Connectivity
echo -e "${PURPLE}🗄️  Checking Database Connectivity...${NC}"

if command_exists curl; then
    # Test an endpoint that requires database access
    db_test_url="$BACKEND_URL/api/products"
    db_response=$(curl -s -w "%{http_code}" -m $TIMEOUT \
        -H "Authorization: Bearer invalid-token" \
        "$db_test_url" 2>/dev/null || echo "000")
    
    db_status="${db_response: -3}"
    if [[ "$db_status" == "401" ]]; then
        log_result "PASS" "Database" "Database connection working (authentication required)"
    elif [[ "$db_status" -ge 500 ]]; then
        log_result "FAIL" "Database" "Database connection error (status: $db_status)"
    else
        log_result "WARN" "Database" "Unexpected response status: $db_status"
    fi
else
    log_result "WARN" "Database" "Cannot validate - curl not available"
fi

echo ""

# 8. Check File System Structure
echo -e "${PURPLE}📁 Checking File System Structure...${NC}"

# Check critical directories and files
critical_paths=(
    "apps/api/app.py"
    "apps/api/config.py"
    "apps/api/requirements.txt"
    "apps/web/package.json"
    "apps/web/vite.config.ts"
    "apps/web/playwright.config.ts"
    "package.json"
)

for path in "${critical_paths[@]}"; do
    if [[ -f "$path" ]]; then
        log_result "PASS" "File Structure" "$path exists"
    else
        log_result "FAIL" "File Structure" "$path missing"
    fi
done

echo ""

# 9. Check Configuration Files
echo -e "${PURPLE}⚙️  Checking Configuration Values...${NC}"

# Check Vite config proxy target
if [[ -f "apps/web/vite.config.ts" ]]; then
    if grep -q "target: 'http://localhost:5000'" "apps/web/vite.config.ts"; then
        log_result "PASS" "Vite Config" "Proxy target correctly set to localhost:5000"
    else
        log_result "FAIL" "Vite Config" "Proxy target not set to localhost:5000"
    fi
else
    log_result "FAIL" "Vite Config" "vite.config.ts not found"
fi

# Check Flask config CORS origins
if [[ -f "apps/api/config.py" ]]; then
    if grep -q "http://localhost:5173" "apps/api/config.py"; then
        log_result "PASS" "Flask Config" "CORS origin correctly includes localhost:5173"
    else
        log_result "FAIL" "Flask Config" "CORS origin does not include localhost:5173"
    fi
else
    log_result "FAIL" "Flask Config" "config.py not found"
fi

echo ""

# 10. Generate Summary Report
echo -e "${PURPLE}📊 Validation Summary${NC}"
echo "================================================================"

total_checks=$((${#VALIDATION_RESULTS[@]}))
pass_count=$((total_checks - ERROR_COUNT - WARNING_COUNT))

echo -e "Total Checks: ${BLUE}$total_checks${NC}"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Warnings: ${YELLOW}$WARNING_COUNT${NC}"
echo -e "Errors: ${RED}$ERROR_COUNT${NC}"

echo ""
echo "Health Score: $pass_count/$total_checks ($((pass_count * 100 / total_checks))%)"

echo ""
echo -e "${PURPLE}📋 Detailed Results:${NC}"
for result in "${VALIDATION_RESULTS[@]}"; do
    echo "  $result"
done

echo ""

# Final recommendation
if [[ $ERROR_COUNT -eq 0 ]]; then
    echo -e "${GREEN}🎉 Environment Validation PASSED${NC}"
    echo "Your development environment is properly configured!"
    
    if [[ $WARNING_COUNT -gt 0 ]]; then
        echo -e "${YELLOW}Note: There are $WARNING_COUNT warnings that should be addressed.${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}❌ Environment Validation FAILED${NC}"
    echo "Found $ERROR_COUNT critical issues that must be resolved."
    echo ""
    echo -e "${YELLOW}Recommendations:${NC}"
    echo "1. Ensure both frontend and backend servers are running"
    echo "2. Check that ports 5173 and 5000 are not blocked"
    echo "3. Verify proxy configuration in vite.config.ts"
    echo "4. Verify CORS configuration in config.py"
    echo "5. Run './scripts/dev.sh --setup' to initialize the environment"
    
    exit 1
fi