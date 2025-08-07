# Makefile for Customer Management System Testing

.PHONY: help install test test-unit test-integration test-performance test-coverage test-parallel test-report clean lint format

# Default target
help:
	@echo "Customer Management System - Test Automation"
	@echo "============================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install          Install testing dependencies"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-parallel    Run tests in parallel"
	@echo "  test-report      Generate comprehensive test report"
	@echo "  test-failed      Run only previously failed tests"
	@echo "  test-watch       Run tests in watch mode"
	@echo "  validate         Validate test environment"
	@echo "  clean            Clean test artifacts"
	@echo "  lint             Run code linting"
	@echo "  format           Format code"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make test-coverage          # Run tests with coverage"
	@echo "  make test-unit              # Run only unit tests"
	@echo "  make test TEST=TestCustomerData  # Run specific test class"

# Variables
PYTHON := python3
PIP := pip3
PYTEST := python3 -m pytest
TEST_FILE := test_customer_info.py
COVERAGE_DIR := htmlcov
REPORTS_DIR := reports

# Install testing dependencies
install:
	@echo "Installing testing dependencies..."
	$(PIP) install -r requirements-test.txt
	@echo "✓ Testing dependencies installed"

# Validate test environment
validate:
	@echo "Validating test environment..."
	$(PYTHON) run_tests.py validate

# Run all tests
test:
	@echo "Running all tests..."
	$(PYTHON) run_tests.py all -v

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	$(PYTHON) run_tests.py unit -v

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	$(PYTHON) run_tests.py integration -v

# Run performance tests only
test-performance:
	@echo "Running performance tests..."
	$(PYTHON) run_tests.py performance -v

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage report..."
	$(PYTHON) run_tests.py all -v -c
	@echo "Coverage report generated in $(COVERAGE_DIR)/"

# Run tests in parallel
test-parallel:
	@echo "Running tests in parallel..."
	$(PYTHON) run_tests.py parallel -v

# Generate comprehensive test report
test-report: clean-reports
	@echo "Generating comprehensive test report..."
	@mkdir -p $(REPORTS_DIR)
	$(PYTHON) run_tests.py report
	@echo "Test report generated in $(REPORTS_DIR)/"

# Run only failed tests
test-failed:
	@echo "Running previously failed tests..."
	$(PYTHON) run_tests.py failed -v

# Run tests in watch mode (requires pytest-watch)
test-watch:
	@echo "Running tests in watch mode..."
	ptw --runner "$(PYTHON) run_tests.py all"

# Run specific test (usage: make test-specific TEST=TestClassName::test_method)
test-specific:
	@echo "Running specific test: $(TEST)"
	$(PYTHON) run_tests.py test $(TEST) -v

# Run tests by keyword (usage: make test-keyword KEYWORD=validation)
test-keyword:
	@echo "Running tests matching keyword: $(KEYWORD)"
	$(PYTHON) run_tests.py keyword $(KEYWORD) -v

# Debug single test with pdb
test-debug:
	@echo "Running test with debugger: $(TEST)"
	$(PYTEST) $(TEST_FILE)::$(TEST) -v -s --pdb

# Quick smoke test
test-smoke:
	@echo "Running smoke tests..."
	$(PYTEST) $(TEST_FILE)::TestCustomerData::test_valid_customer_creation -v
	$(PYTEST) $(TEST_FILE)::TestInMemoryCustomerRepository::test_create_customer -v
	$(PYTEST) $(TEST_FILE)::TestCustomerInfoLogic::test_set_customer_data -v

# Performance benchmarking
test-benchmark:
	@echo "Running performance benchmarks..."
	$(PYTEST) $(TEST_FILE)::TestPerformance -v --benchmark-only

# Code quality checks
lint:
	@echo "Running code linting..."
	flake8 $(TEST_FILE) --max-line-length=100
	@echo "✓ Linting completed"

# Format code
format:
	@echo "Formatting code..."
	black $(TEST_FILE) --line-length=100
	@echo "✓ Code formatted"

# Type checking
typecheck:
	@echo "Running type checking..."
	mypy $(TEST_FILE) --ignore-missing-imports
	@echo "✓ Type checking completed"

# Clean test artifacts
clean: clean-pytest clean-coverage clean-reports
	@echo "✓ Cleaned all test artifacts"

clean-pytest:
	@echo "Cleaning pytest cache..."
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete

clean-coverage:
	@echo "Cleaning coverage files..."
	@rm -rf $(COVERAGE_DIR)/
	@rm -f .coverage
	@rm -f coverage.xml

clean-reports:
	@echo "Cleaning test reports..."
	@rm -rf $(REPORTS_DIR)/
	@rm -f test_report.html
	@rm -f test_report.xml

# Setup pre-commit hooks
setup-hooks:
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit:
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	$(PIP) install -r requirements-test.txt
	$(PIP) install pre-commit black flake8 mypy
	@echo "✓ Development dependencies installed"

# Create test database for integration tests
setup-test-db:
	@echo "Setting up test database..."
	@mkdir -p test_data/
	$(PYTHON) -c "from test_customer_info import setup_test_database; setup_test_database()"
	@echo "✓ Test database created"

# Documentation
docs-test:
	@echo "Generating test documentation..."
	$(PYTEST) $(TEST_FILE) --collect-only --quiet | grep "::test" > test_list.txt
	@echo "✓ Test documentation generated in test_list.txt"

# CI/CD targets
ci-test: install validate test-coverage
	@echo "✓ CI tests completed"

# Release testing
test-release: clean install test-coverage test-performance
	@echo "✓ Release testing completed"

# Help with specific test categories
help-tests:
	@echo "Test Organization:"
	@echo "=================="
	@echo ""
	@echo "Unit Tests (TestCustomerData, TestCompanionData, etc.):"
	@echo "  - Test individual components in isolation"
	@echo "  - Fast execution, no external dependencies"
	@echo "  - Run with: make test-unit"
	@echo ""
	@echo "Integration Tests (TestIntegration):"
	@echo "  - Test component interactions"
	@echo "  - May involve database operations"
	@echo "  - Run with: make test-integration"
	@echo ""
	@echo "Performance Tests (TestPerformance):"
	@echo "  - Test system performance and scalability"
	@echo "  - May take longer to execute"
	@echo "  - Run with: make test-performance"
	@echo ""
	@echo "UI Tests (TestCustomerInfoView):"
	@echo "  - Test user interface components"
	@echo "  - Require Qt testing framework"
	@echo "  - Run with: make test-keyword KEYWORD=ui"

# Development workflow
dev-cycle: format lint typecheck test-unit
	@echo "✓ Development cycle completed"

# Full quality check
quality-check: format lint typecheck test-coverage
	@echo "✓ Quality check completed"
