#!/usr/bin/env python3
"""
Test runner script with logging and reporting.
"""

import os
import sys
import subprocess
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime


def setup_logging():
    """Setup logging for the test runner"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def ensure_directories():
    """Ensure required directories exist"""
    log_dir = Path("tests/logs")
    reports_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return log_dir, reports_dir


def run_tests(test_pattern=None, markers=None, verbose=True, capture_output=False):
    """
    Run tests with simplified logging

    Args:
        test_pattern: Specific test pattern to run
        markers: Pytest markers to filter tests
        verbose: Enable verbose output
        capture_output: Capture and return output instead of printing
    """
    logger = setup_logging()
    log_dir, reports_dir = ensure_directories()

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test pattern if specified
    if test_pattern:
        cmd.append(test_pattern)

    # Add marker filtering
    if markers:
        cmd.extend(["-m", markers])

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add basic options
    cmd.extend([
        "--tb=short",
        "--durations=10",
        "--color=yes"
    ])

    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, check=False)
            return result.returncode
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return 1


def run_full_suite():
    """Run the complete test suite with enhanced reporting"""
    logger = setup_logging()
    log_dir, reports_dir = ensure_directories()

    logger.info("🚀 Running Complete Test Suite...")

    # Generate timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Run pytest (conftest.py will handle logging automatically)
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--durations=10",
        "--color=yes"
    ]

    logger.info(f"📝 Detailed logs will be in: tests/logs/test_run_{timestamp}.log")
    logger.info(f"📊 Summary report will be in: reports/test_summary_{timestamp}.txt")

    return_code = subprocess.run(cmd, check=False).returncode

    if return_code == 0:
        logger.info("🎉 Complete test suite passed!")
    else:
        logger.warning("⚠️  Test suite completed with some issues")
        logger.info("Check the detailed logs and reports for more information")

    return return_code


def run_stability_analysis():
    """Run specific stability analysis tests"""
    logger = setup_logging()
    logger.info("🔍 Running API Stability Analysis...")

    return_code = run_tests(
        test_pattern="tests/test_pet_api.py::TestPetAPIStability",
        verbose=True
    )

    if return_code == 0:
        logger.info("✅ Stability analysis completed successfully")
    else:
        logger.warning("⚠️  Stability analysis completed with issues")

    return return_code


def run_regression_suite():
    """Run regression test suite"""
    logger = setup_logging()
    logger.info("🧪 Running Regression Test Suite...")

    return_code = run_tests(
        markers="regression",
        verbose=True
    )

    if return_code == 0:
        logger.info("✅ Regression suite completed successfully")
    else:
        logger.warning("⚠️  Regression suite completed with issues")

    return return_code


def run_positive_tests():
    """Run only positive test cases"""
    logger = setup_logging()
    logger.info("✅ Running Positive Test Cases...")

    return_code = run_tests(
        markers="positive",
        verbose=True
    )

    if return_code == 0:
        logger.info("✅ Positive tests completed successfully")
    else:
        logger.warning("⚠️  Positive tests completed with issues")

    return return_code


def run_negative_tests():
    """Run only negative test cases"""
    logger = setup_logging()
    logger.info("❌ Running Negative Test Cases...")

    return_code = run_tests(
        markers="negative",
        verbose=True
    )

    if return_code == 0:
        logger.info("✅ Negative tests completed successfully")
    else:
        logger.warning("⚠️  Negative tests completed with issues")

    return return_code


def main():
    """Main test runner with command line options"""
    parser = argparse.ArgumentParser(description="Pet Store API Test Runner")

    subparsers = parser.add_subparsers(dest="command", help="Test command to run")

    # Full suite
    subparsers.add_parser("full", help="Run complete test suite")

    # Stability analysis
    subparsers.add_parser("stability", help="Run API stability analysis")

    # Test type filters
    subparsers.add_parser("positive", help="Run positive test cases only")
    subparsers.add_parser("negative", help="Run negative test cases only")
    subparsers.add_parser("regression", help="Run regression test suite")

    # Custom test run
    custom_parser = subparsers.add_parser("custom", help="Run custom test pattern")
    custom_parser.add_argument("pattern", help="Test pattern to run")
    custom_parser.add_argument("-m", "--markers", help="Pytest markers to filter")

    # Single test
    single_parser = subparsers.add_parser("single", help="Run single test")
    single_parser.add_argument("test", help="Specific test to run")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Ensure we're in the right directory
    if not os.path.exists("tests"):
        print("Error: tests directory not found. Please run from project root.")
        return 1

    # Route to appropriate test runner
    if args.command == "full":
        return run_full_suite()
    elif args.command == "stability":
        return run_stability_analysis()
    elif args.command == "positive":
        return run_positive_tests()
    elif args.command == "negative":
        return run_negative_tests()
    elif args.command == "regression":
        return run_regression_suite()
    elif args.command == "custom":
        return run_tests(test_pattern=args.pattern, markers=args.markers)
    elif args.command == "single":
        return run_tests(test_pattern=args.test)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())