#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Runner Script for Customer Management System
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path


def setup_test_environment():
    """Setup the test environment and paths."""
    # Add the project root to Python path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Set environment variables for testing
    os.environ['TESTING'] = '1'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # For headless Qt testing


def run_pytest_command(args_list):
    """Run pytest with given arguments."""
    cmd = [sys.executable, "-m", "pytest"] + args_list
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    args = ["test_customer_info.py"]

    if verbose:
        args.append("-v")

    if coverage:
        args.extend([
            "--cov=features.InvoicePage.customer_info",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    return run_pytest_command(args)


def run_unit_tests(verbose=False):
    """Run only unit tests."""
    args = [
        "test_customer_info.py",
        "-m", "not integration and not performance and not ui"
    ]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_integration_tests(verbose=False):
    """Run only integration tests."""
    args = [
        "test_customer_info.py::TestIntegration",
    ]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_performance_tests(verbose=False):
    """Run only performance tests."""
    args = [
        "test_customer_info.py::TestPerformance",
    ]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_specific_test(test_name, verbose=False):
    """Run a specific test."""
    args = [f"test_customer_info.py::{test_name}"]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_tests_by_keyword(keyword, verbose=False):
    """Run tests matching a keyword."""
    args = [
        "test_customer_info.py",
        "-k", keyword
    ]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_failed_tests(verbose=False):
    """Run only previously failed tests."""
    args = [
        "test_customer_info.py",
        "--lf"  # Last failed
    ]

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def run_tests_parallel(num_processes=None, verbose=False):
    """Run tests in parallel using pytest-xdist."""
    args = ["test_customer_info.py"]

    if num_processes:
        args.extend(["-n", str(num_processes)])
    else:
        args.extend(["-n", "auto"])

    if verbose:
        args.append("-v")

    return run_pytest_command(args)


def generate_test_report():
    """Generate a comprehensive test report."""
    args = [
        "test_customer_info.py",
        "--junitxml=test_report.xml",
        "--html=test_report.html",
        "--self-contained-html",
        "--cov=features.InvoicePage.customer_info",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "-v"
    ]

    return run_pytest_command(args)


def validate_test_environment():
    """Validate that the test environment is properly set up."""
    print("Validating test environment...")

    # Check required imports
    try:
        import pytest
        print(f"✓ pytest version: {pytest.__version__}")
    except ImportError:
        print("✗ pytest not installed. Install with: pip install pytest")
        return False

    try:
        import PySide6
        print(f"✓ PySide6 version: {PySide6.__version__}")
    except ImportError:
        print("✗ PySide6 not installed. Install with: pip install PySide6")
        return False

    # Check if test files exist
    test_file = Path("test_customer_info.py")
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return False
    else:
        print(f"✓ Test file found: {test_file}")

    # Check if source modules can be imported
    try:
        from features.InvoicePage.customer_info.customer_info_models import CustomerData
        print("✓ Source modules can be imported")
    except ImportError as e:
        print(f"✗ Cannot import source modules: {e}")
        return False

    print("✓ Test environment validation passed")
    return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Test Runner for Customer Management System")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")

    subparsers = parser.add_subparsers(dest="command", help="Test commands")

    # All tests
    subparsers.add_parser("all", help="Run all tests")

    # Unit tests
    subparsers.add_parser("unit", help="Run unit tests only")

    # Integration tests
    subparsers.add_parser("integration", help="Run integration tests only")

    # Performance tests
    subparsers.add_parser("performance", help="Run performance tests only")

    # Specific test
    specific_parser = subparsers.add_parser("test", help="Run specific test")
    specific_parser.add_argument("name", help="Test name (class::method)")

    # Keyword search
    keyword_parser = subparsers.add_parser("keyword", help="Run tests matching keyword")
    keyword_parser.add_argument("keyword", help="Keyword to search for")

    # Failed tests
    subparsers.add_parser("failed", help="Run previously failed tests")

    # Parallel tests
    parallel_parser = subparsers.add_parser("parallel", help="Run tests in parallel")
    parallel_parser.add_argument("-n", "--processes", type=int, help="Number of processes")

    # Generate report
    subparsers.add_parser("report", help="Generate comprehensive test report")

    # Validate environment
    subparsers.add_parser("validate", help="Validate test environment")

    args = parser.parse_args()

    # Setup test environment
    setup_test_environment()

    # Default to running all tests if no command specified
    if not args.command:
        args.command = "all"

    # Execute the appropriate command
    if args.command == "validate":
        success = validate_test_environment()
        return 0 if success else 1
    elif args.command == "all":
        return run_all_tests(args.verbose, args.coverage)
    elif args.command == "unit":
        return run_unit_tests(args.verbose)
    elif args.command == "integration":
        return run_integration_tests(args.verbose)
    elif args.command == "performance":
        return run_performance_tests(args.verbose)
    elif args.command == "test":
        return run_specific_test(args.name, args.verbose)
    elif args.command == "keyword":
        return run_tests_by_keyword(args.keyword, args.verbose)
    elif args.command == "failed":
        return run_failed_tests(args.verbose)
    elif args.command == "parallel":
        return run_tests_parallel(args.processes, args.verbose)
    elif args.command == "report":
        return generate_test_report()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
