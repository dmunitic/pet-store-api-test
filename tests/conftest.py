"""
Pytest configuration with logging and test results reporting.
"""

import pytest
import logging
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from framework.api_client import PetStoreAPIClient
from tests.test_data.pet_data_factory import PetDataFactory

# Global test results tracker with proper typing
test_results: Dict[str, Any] = {
    'passed': [],
    'failed': [],
    'skipped': [],
    'start_time': None,
    'end_time': None
}


def pytest_configure(config) -> None:
    """Configure pytest with logging and reporting"""
    # Ensure directories exist
    log_dir = Path("tests/logs")
    reports_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create single timestamped log file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"test_run_{timestamp}.log"

    # Store paths for other functions (using setattr to avoid protected member warnings)
    setattr(config, 'custom_log_file_path', log_file)
    setattr(config, 'custom_reports_dir', reports_dir)
    setattr(config, 'custom_timestamp', timestamp)

    # Initialize test results tracking
    global test_results
    test_results['start_time'] = datetime.now()

    # Remove any existing handlers to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Silence noisy third-party loggers
    noisy_loggers = ['faker', 'urllib3', 'requests', 'urllib3.connectionpool']
    for noisy_logger in noisy_loggers:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Setup comprehensive logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

    # Configure framework loggers
    framework_loggers = [
        'framework', 'framework.api_client', 'framework.base_test', 'framework.utilities',
        'conftest', 'BaseTest', 'TestPetAPIWorkflow', 'TestPetAPIStability', 'TestAPIConnection'
    ]

    for logger_name in framework_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

    # Log session start
    logger = logging.getLogger("conftest")
    logger.info("=== PYTEST SESSION STARTED ===")
    logger.info(f"📝 Log file: {log_file}")
    logger.info(f"📊 Reports will be saved to: {reports_dir}")


def pytest_unconfigure(config) -> None:
    """Generate final reports and clean up"""
    global test_results
    test_results['end_time'] = datetime.now()

    logger = logging.getLogger("conftest")

    # Generate summary report with actual test results
    if (hasattr(config, 'custom_reports_dir') and
        hasattr(config, 'custom_timestamp') and
        hasattr(config, 'custom_log_file_path')):
        generate_test_summary_report(
            getattr(config, 'custom_reports_dir'),
            getattr(config, 'custom_timestamp'),
            getattr(config, 'custom_log_file_path')
        )

    logger.info("=== PYTEST SESSION ENDED ===")

    # Ensure all logs are flushed
    for handler in logging.root.handlers:
        handler.flush()


def generate_test_summary_report(reports_dir: Path, timestamp: str, log_file_path: Path) -> None:
    """Generate a comprehensive test summary report"""
    logger = logging.getLogger("conftest")

    try:
        global test_results

        # Calculate metrics
        total_passed = len(test_results['passed'])
        total_failed = len(test_results['failed'])
        total_skipped = len(test_results['skipped'])
        total_tests = total_passed + total_failed + total_skipped

        # Safe datetime operations with proper type checking
        start_time = test_results.get('start_time')
        end_time = test_results.get('end_time')

        if start_time and end_time and isinstance(start_time, datetime) and isinstance(end_time, datetime):
            duration = (end_time - start_time).total_seconds()
            formatted_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            duration = 0.0
            formatted_end_time = "Unknown"

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        # Create the report
        report_file = reports_dir / f"test_summary_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🧪 Pet Store API Test Framework - Test Summary Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Run: {timestamp}\n")
            f.write(f"Generated: {formatted_end_time}\n")
            f.write(f"Duration: {duration:.2f} seconds\n\n")

            # Overall Results
            f.write("📊 Overall Results:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"✅ Passed: {total_passed}\n")
            f.write(f"❌ Failed: {total_failed}\n")
            f.write(f"⏭️ Skipped: {total_skipped}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n\n")

            # Test Results Details (condensed for brevity)
            if test_results['passed']:
                f.write(f"✅ PASSED TESTS ({total_passed}):\n")
                for i, test in enumerate(test_results['passed'], 1):
                    test_name = test['name'].split("::")[-1] if isinstance(test, dict) and 'name' in test else "Unknown"
                    duration_info = f" ({test['duration']:.2f}s)" if isinstance(test, dict) and test.get('duration') else ""
                    f.write(f"{i:2d}. {test_name}{duration_info}\n")
                f.write("\n")

            if test_results['failed']:
                f.write(f"❌ FAILED TESTS ({total_failed}):\n")
                for i, test in enumerate(test_results['failed'], 1):
                    test_name = test['name'].split("::")[-1] if isinstance(test, dict) and 'name' in test else "Unknown"
                    f.write(f"{i:2d}. {test_name}\n")
                    if isinstance(test, dict) and test.get('error'):
                        # Extract the key error message
                        error_lines = str(test['error']).split('\n')
                        error_msg = next((line for line in error_lines if line.startswith('E   ')),
                                       error_lines[-1] if error_lines else 'Unknown error')
                        if error_msg.startswith('E   '):
                            error_msg = error_msg[4:]
                        f.write(f"    Error: {error_msg}\n")
                f.write("\n")

            if test_results['skipped']:
                f.write(f"⏭️ SKIPPED TESTS ({total_skipped}):\n")
                for i, test in enumerate(test_results['skipped'], 1):
                    test_name = test['name'].split("::")[-1] if isinstance(test, dict) and 'name' in test else "Unknown"
                    f.write(f"{i:2d}. {test_name}\n")
                    if isinstance(test, dict) and test.get('reason'):
                        f.write(f"    Reason: {test['reason']}\n")
                f.write("\n")

            # Framework capabilities demonstrated
            f.write("🎯 Framework Capabilities Demonstrated:\n")
            f.write("-" * 30 + "\n")
            f.write("✅ Complete CRUD operations (POST, GET, PUT, DELETE)\n")
            f.write("✅ Intelligent retry logic for unreliable APIs\n")
            f.write("✅ Comprehensive test data management\n")
            f.write("✅ Advanced assertion and validation utilities\n")
            f.write("✅ Stability metrics and analysis\n")
            f.write("✅ Professional logging and reporting\n")
            f.write("✅ Positive and negative test scenarios\n")
            f.write("✅ Security and boundary testing capabilities\n")
            f.write("✅ Clean, maintainable code architecture\n\n")

            f.write("📁 Generated Files:\n")
            f.write(f"📝 Detailed Log: {log_file_path}\n")
            f.write(f"📊 Summary Report: {report_file}\n\n")

            if total_failed == 0:
                f.write("🎉 All tests passed! Framework is working perfectly.\n")
            else:
                f.write("ℹ️  Check the detailed log file for error analysis.\n")

        logger.info(f"📊 Test summary report generated: {report_file}")

    except Exception as e:
        logger.warning(f"Could not generate summary report: {e}")


@pytest.fixture(scope="session")
def api_client():
    """Create API client for the test session"""
    logger = logging.getLogger("conftest")
    logger.info("Creating API client for test session")

    client = PetStoreAPIClient()

    # Test API connection
    logger.info("Testing API connection...")
    try:
        response = client.get_pet_by_id(1)
        if response.status_code in [200, 404]:  # Both are valid responses
            logger.info("✅ API connection successful")
        else:
            logger.warning(f"⚠️ API returned unexpected status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ API connection failed: {e}")

    yield client

    logger.info("API client session completed")
    client.close()


@pytest.fixture
def sample_pet_data() -> Dict[str, Any]:
    """Generate sample pet data using the factory"""
    logger = logging.getLogger("conftest")

    # Direct import works without __init__.py
    pet_data = PetDataFactory.create_complete_pet()

    logger.info(f"Generated sample pet data with ID: {pet_data['id']}")
    logger.debug(f"Sample pet data: {pet_data}")
    return pet_data


@pytest.fixture
def updated_pet_data(sample_pet_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate updated pet data using the factory"""
    logger = logging.getLogger("conftest")

    # Use the factory method for consistent update logic
    updated_data = PetDataFactory.create_updated_pet(sample_pet_data)

    logger.info(f"Generated updated pet data for ID: {updated_data['id']}")
    logger.debug(f"Updated pet data: {updated_data}")
    return updated_data


@pytest.fixture
def invalid_pet_data() -> List[Dict[str, Any]]:
    """Generate various invalid pet data for negative testing"""
    logger = logging.getLogger("conftest")

    invalid_pets = PetDataFactory.create_invalid_pets()

    logger.info(f"Generated {len(invalid_pets)} invalid pet data samples")
    return invalid_pets


@pytest.fixture
def boundary_test_data() -> Dict[str, Dict[str, Any]]:
    """Generate boundary test cases"""
    logger = logging.getLogger("conftest")

    boundary_data = PetDataFactory.create_boundary_test_data()

    logger.info(f"Generated {len(boundary_data)} boundary test cases")
    return boundary_data


# Test result collection hooks
def pytest_runtest_setup(item) -> None:
    """Log test setup"""
    logger = logging.getLogger("conftest")
    logger.info(f"🔧 Setting up test: {item.nodeid}")


def pytest_runtest_call(item) -> None:
    """Log test execution"""
    logger = logging.getLogger("conftest")
    logger.info(f"🚀 Executing test: {item.nodeid}")


def pytest_runtest_teardown(item) -> None:
    """Log test teardown"""
    logger = logging.getLogger("conftest")
    logger.info(f"🧹 Tearing down test: {item.nodeid}")


def pytest_runtest_logreport(report) -> None:
    """Collect test results and log them"""
    global test_results
    logger = logging.getLogger("conftest")

    if report.when == "call":
        test_info: Dict[str, Any] = {
            'name': report.nodeid,
            'duration': getattr(report, 'duration', 0)
        }

        if report.outcome == "passed":
            test_results['passed'].append(test_info)
            logger.info(f"✅ PASSED: {report.nodeid}")
        elif report.outcome == "failed":
            test_info['error'] = str(report.longrepr) if hasattr(report, 'longrepr') and report.longrepr else "Unknown error"
            test_results['failed'].append(test_info)
            logger.error(f"❌ FAILED: {report.nodeid}")
        elif report.outcome == "skipped":
            # Extract skip reason
            skip_reason = "Unknown reason"
            if hasattr(report, 'longrepr') and report.longrepr:
                if hasattr(report.longrepr, 'reprcrash') and hasattr(report.longrepr.reprcrash, 'message'):
                    skip_reason = str(report.longrepr.reprcrash.message)
                elif isinstance(report.longrepr, tuple) and len(report.longrepr) > 2:
                    skip_reason = str(report.longrepr[2])
                else:
                    skip_reason = str(report.longrepr)

            test_info['reason'] = skip_reason
            test_results['skipped'].append(test_info)
            logger.warning(f"⏭️ SKIPPED: {report.nodeid} - {skip_reason}")