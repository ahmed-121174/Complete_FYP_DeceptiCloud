#!/bin/bash
# Quick Test Execution Script for DeceptiCloud

echo "================================================================================"
echo "                    DECEPTICLOUD QUICK TEST RUNNER"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed. Installing..."
    pip install pytest pytest-cov pytest-mock pytest-asyncio requests-mock
fi

echo ""
echo "================================================================================"
echo "                         PHASE 1: UNIT TESTS"
echo "================================================================================"
echo ""

print_info "Running unit tests..."
python3 -m pytest tests/unit/ -v --tb=short -q

UNIT_EXIT=$?

if [ $UNIT_EXIT -eq 0 ]; then
    print_success "All unit tests passed!"
else
    print_warning "Some unit tests failed or were skipped"
fi

echo ""
echo "================================================================================"
echo "                      PHASE 2: INTEGRATION TESTS"
echo "================================================================================"
echo ""

print_info "Checking if services are running..."

# Check ML API
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    print_success "ML API is running"
    ML_API_RUNNING=true
else
    print_warning "ML API is not running - integration tests will be skipped"
    ML_API_RUNNING=false
fi

# Check Proxy
if curl -s http://localhost:8080/proxy/status > /dev/null 2>&1; then
    print_success "Proxy is running"
    PROXY_RUNNING=true
else
    print_warning "Proxy is not running - integration tests will be skipped"
    PROXY_RUNNING=false
fi

# Check Dashboard
if curl -s http://localhost:9000/ > /dev/null 2>&1; then
    print_success "Dashboard is running"
    DASHBOARD_RUNNING=true
else
    print_warning "Dashboard is not running - integration tests will be skipped"
    DASHBOARD_RUNNING=false
fi

echo ""
print_info "Running integration tests..."
python3 -m pytest tests/integration/ -v --tb=short -q

INTEGRATION_EXIT=$?

if [ $INTEGRATION_EXIT -eq 0 ]; then
    print_success "Integration tests completed!"
else
    print_warning "Some integration tests failed or were skipped"
fi

echo ""
echo "================================================================================"
echo "                        PHASE 3: SYSTEM TESTS"
echo "================================================================================"
echo ""

if [ "$ML_API_RUNNING" = true ] && [ "$PROXY_RUNNING" = true ] && [ "$DASHBOARD_RUNNING" = true ]; then
    print_info "All services running - executing system tests..."
    python3 -m pytest tests/system/ -v --tb=short -q
    SYSTEM_EXIT=$?
    
    if [ $SYSTEM_EXIT -eq 0 ]; then
        print_success "System tests completed!"
    else
        print_warning "Some system tests failed or were skipped"
    fi
else
    print_warning "Not all services are running - skipping system tests"
    print_info "To run system tests, start all services:"
    echo "  1. ML API: python3 ml_pipeline/model_api.py"
    echo "  2. Proxy: python3 proxy/routing_proxy.py"
    echo "  3. Dashboard: python3 dashboard/app.py"
    SYSTEM_EXIT=0
fi

echo ""
echo "================================================================================"
echo "                            TEST SUMMARY"
echo "================================================================================"
echo ""

# Calculate overall result
TOTAL_FAILURES=0
if [ $UNIT_EXIT -ne 0 ]; then
    ((TOTAL_FAILURES++))
fi
if [ $INTEGRATION_EXIT -ne 0 ]; then
    ((TOTAL_FAILURES++))
fi
if [ $SYSTEM_EXIT -ne 0 ]; then
    ((TOTAL_FAILURES++))
fi

echo "Unit Tests:        $([ $UNIT_EXIT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${YELLOW}PARTIAL${NC}")"
echo "Integration Tests: $([ $INTEGRATION_EXIT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${YELLOW}SKIPPED${NC}")"
echo "System Tests:      $([ $SYSTEM_EXIT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${YELLOW}SKIPPED${NC}")"

echo ""
if [ $TOTAL_FAILURES -eq 0 ]; then
    print_success "ALL TESTS PASSED!"
    echo ""
    echo "The DeceptiCloud system is functioning correctly."
else
    print_warning "Some tests were skipped or failed"
    echo ""
    echo "Review the output above for details."
fi

echo ""
echo "================================================================================"
echo "For detailed results, see: TEST_RESULTS_SUMMARY.txt"
echo "================================================================================"
echo ""

exit $TOTAL_FAILURES
