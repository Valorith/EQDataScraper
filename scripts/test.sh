#!/bin/bash
#
# Comprehensive test runner for EQDataScraper
# Runs both backend and frontend tests with proper environment setup
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🧪 EQDataScraper Test Suite${NC}"
echo "================================="

# Default options
RUN_BACKEND=true
RUN_FRONTEND=true
RUN_COVERAGE=false
RUN_VERBOSE=false
INSTALL_DEPS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            RUN_FRONTEND=false
            shift
            ;;
        --frontend-only)
            RUN_BACKEND=false
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --verbose)
            RUN_VERBOSE=true
            shift
            ;;
        --install)
            INSTALL_DEPS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend-only    Run only backend tests"
            echo "  --frontend-only   Run only frontend tests"
            echo "  --coverage        Generate coverage reports"
            echo "  --verbose         Verbose output"
            echo "  --install         Install test dependencies first"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project directory
cd "$PROJECT_DIR"

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
    
    if [ "$RUN_BACKEND" = true ]; then
        echo "Installing backend test dependencies..."
        cd backend
        pip install -r requirements-test.txt
        cd ..
    fi
    
    if [ "$RUN_FRONTEND" = true ]; then
        echo "Installing frontend test dependencies..."
        npm install
    fi
fi

# Track test results
BACKEND_RESULT=0
FRONTEND_RESULT=0

# Run backend tests
if [ "$RUN_BACKEND" = true ]; then
    echo -e "${BLUE}🐍 Running Backend Tests${NC}"
    echo "------------------------"
    
    cd backend
    
    # Set test environment
    export TESTING=1
    export DATABASE_URL=""
    export PORT=5999
    export CACHE_EXPIRY_HOURS=1
    export PRICING_CACHE_EXPIRY_HOURS=1
    
    # Build pytest command
    PYTEST_CMD="python -m pytest"
    
    if [ "$RUN_VERBOSE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -v"
    fi
    
    if [ "$RUN_COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov --cov-report=term-missing --cov-report=html:htmlcov"
    fi
    
    # Run tests
    if eval $PYTEST_CMD; then
        echo -e "${GREEN}✅ Backend tests passed${NC}"
    else
        echo -e "${RED}❌ Backend tests failed${NC}"
        BACKEND_RESULT=1
    fi
    
    cd ..
fi

# Run frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    echo -e "${BLUE}🌐 Running Frontend Tests${NC}"
    echo "-------------------------"
    
    # Build vitest command
    if [ "$RUN_COVERAGE" = true ]; then
        VITEST_CMD="npm run test:coverage"
    else
        VITEST_CMD="npm run test:run"
    fi
    
    if [ "$RUN_VERBOSE" = true ]; then
        VITEST_CMD="$VITEST_CMD -- --reporter=verbose"
    fi
    
    # Run tests
    if eval $VITEST_CMD; then
        echo -e "${GREEN}✅ Frontend tests passed${NC}"
    else
        echo -e "${RED}❌ Frontend tests failed${NC}"
        FRONTEND_RESULT=1
    fi
fi

# Summary
echo ""
echo -e "${BLUE}📊 Test Summary${NC}"
echo "==============="

if [ "$RUN_BACKEND" = true ]; then
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo -e "Backend:  ${GREEN}PASSED${NC}"
    else
        echo -e "Backend:  ${RED}FAILED${NC}"
    fi
fi

if [ "$RUN_FRONTEND" = true ]; then
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "Frontend: ${GREEN}PASSED${NC}"
    else
        echo -e "Frontend: ${RED}FAILED${NC}"
    fi
fi

# Coverage reports
if [ "$RUN_COVERAGE" = true ]; then
    echo ""
    echo -e "${BLUE}📈 Coverage Reports${NC}"
    echo "==================="
    
    if [ "$RUN_BACKEND" = true ] && [ -d "backend/htmlcov" ]; then
        echo "Backend coverage: backend/htmlcov/index.html"
    fi
    
    if [ "$RUN_FRONTEND" = true ] && [ -d "coverage" ]; then
        echo "Frontend coverage: coverage/index.html"
    fi
fi

# Exit with error if any tests failed
OVERALL_RESULT=$((BACKEND_RESULT + FRONTEND_RESULT))

if [ $OVERALL_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some tests failed!${NC}"
    exit 1
fi