"""
Clean conftest.py with Pytest HTML reporting (no global variables)
Uses pytest's built-in mechanisms for reporting
"""

import pytest
import logging
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add imports for refactored components
from framework.api_client import PetStoreAPIClient
from framework.constants import LoggingConstants, APIConstants
from framework.exceptions import APIConnectionError, InvalidPetIdError
from tests.test_data.pet_data_factory import PetDataFactory

# ✅ CREATE LOGGER ONCE at module level (NO GLOBAL VARIABLES)
logger = logging.getLogger("conftest")


def pytest_configure(config) -> None:
    """Configure pytest with logging - NO GLOBAL VARIABLES"""
    # Ensure directories exist
    log_dir = Path("tests/logs")
    reports_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create single timestamped log file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"test_run_{timestamp}.log"

    # ✅ Try to configure HTML reporting if pytest-html is available
    html_report = reports_dir / f"test_report_{timestamp}.html"
    try:
        # Configure HTML reporting programmatically
        config.option.htmlpath = str(html_report)
        config.option.self_contained_html = True  # Embed CSS/JS
        logger.info("HTML reporting configured", extra={
            "html_report_path": str(html_report)
        })
    except (AttributeError, ImportError):
        logger.warning("pytest-html not available, skipping HTML report")

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
        framework_logger = logging.getLogger(logger_name)
        framework_logger.setLevel(logging.DEBUG)
        framework_logger.propagate = True

    # Log session start with machine-readable format
    logger.info("Pytest session started", extra={
        "event": "session_start",
        "log_file": str(log_file),
        "reports_dir": str(reports_dir),
        "html_report": str(html_report) if 'html_report' in locals() else None
    })


def pytest_unconfigure(config) -> None:
    """Clean session end - NO GLOBAL VARIABLES"""
    logger.info("Pytest session ended", extra={
        "event": "session_end"
    })

    # Ensure all logs are flushed
    for handler in logging.root.handlers:
        handler.flush()


# ✅ CLEAN pytest hooks - no global state tracking
def pytest_runtest_setup(item) -> None:
    """Log test setup"""
    logger.info("Test setup started", extra={
        "event": "test_setup",
        "test_id": item.nodeid,
        "phase": LoggingConstants.PHASE_SETUP
    })


def pytest_runtest_call(item) -> None:
    """Log test execution"""
    logger.info("Test execution started", extra={
        "event": "test_execution",
        "test_id": item.nodeid,
        "phase": LoggingConstants.PHASE_EXECUTION
    })


def pytest_runtest_teardown(item) -> None:
    """Log test teardown"""
    logger.info("Test teardown started", extra={
        "event": "test_teardown",
        "test_id": item.nodeid,
        "phase": LoggingConstants.PHASE_TEARDOWN
    })


def pytest_runtest_logreport(report) -> None:
    """Log test results - NO GLOBAL STATE"""
    if report.when == "call":
        if report.outcome == "passed":
            logger.info("Test passed", extra={
                "event": "test_result",
                "result": LoggingConstants.STATUS_SUCCESS,
                "test_id": report.nodeid,
                "duration": getattr(report, 'duration', 0)
            })
        elif report.outcome == "failed":
            error = str(report.longrepr) if hasattr(report, 'longrepr') and report.longrepr else "Unknown error"
            logger.error("Test failed", extra={
                "event": "test_result",
                "result": LoggingConstants.STATUS_FAILURE,
                "test_id": report.nodeid,
                "error": error
            })
        elif report.outcome == "skipped":
            skip_reason = "Unknown reason"
            if hasattr(report, 'longrepr') and report.longrepr:
                if hasattr(report.longrepr, 'reprcrash') and hasattr(report.longrepr.reprcrash, 'message'):
                    skip_reason = str(report.longrepr.reprcrash.message)
                elif isinstance(report.longrepr, tuple) and len(report.longrepr) > 2:
                    skip_reason = str(report.longrepr[2])
                else:
                    skip_reason = str(report.longrepr)

            logger.warning("Test skipped", extra={
                "event": "test_result",
                "result": LoggingConstants.STATUS_SKIPPED,
                "test_id": report.nodeid,
                "skip_reason": skip_reason
            })


# ✅ Enhanced HTML report customization (if pytest-html is available)
def pytest_html_report_title(report):
    """Customize HTML report title"""
    report.title = "Pet Store API Test Framework - Test Results"


def pytest_html_results_summary(prefix, summary, postfix):
    """Customize HTML report summary"""
    prefix.extend([
        "<h2>Pet Store API Test Framework</h2>",
        "<p>Comprehensive API testing with retry logic and stability analysis</p>"
    ])


@pytest.fixture(scope="session")
def api_client():
    """Create API client for the test session"""
    logger.info("Creating API client for test session", extra={
        "event": "api_client_creation",
        "phase": "setup"
    })

    client = PetStoreAPIClient()

    # Test API connection with machine-readable logging
    logger.info("Testing API connection", extra={
        "event": "api_connection_test",
        "phase": "setup"
    })

    try:
        response = client.get_pet_by_id(1)
        if response.status_code in [APIConstants.HTTP_OK, APIConstants.HTTP_NOT_FOUND]:
            logger.info("API connection successful", extra={
                "event": "api_connection_success",
                "status_code": response.status_code,
                "phase": "setup",
                "health_check_result": "api_reachable"
            })
        else:
            logger.warning("API returned unexpected status", extra={
                "event": "api_connection_warning",
                "status_code": response.status_code,
                "phase": "setup",
                "health_check_result": "unexpected_status"
            })
    except (APIConnectionError, InvalidPetIdError) as e:
        logger.error("API connection failed with known error", extra={
            "event": "api_connection_failure",
            "error_type": type(e).__name__,
            "error": str(e),
            "phase": "setup",
            "health_check_result": "known_error"
        })
    except Exception as e:
        logger.error("API connection failed with unexpected error", extra={
            "event": "api_connection_failure",
            "error_type": type(e).__name__,
            "error": str(e),
            "phase": "setup",
            "health_check_result": "unexpected_error"
        })

    yield client

    logger.info("API client session completed", extra={
        "event": "api_client_completion",
        "phase": "teardown"
    })
    client.close()


@pytest.fixture
def sample_pet_data() -> dict:
    """Generate sample pet data using the factory"""
    pet_data = PetDataFactory.create_complete_pet()

    logger.info("Generated sample pet data", extra={
        "event": "test_data_generation",
        "data_type": "sample_pet",
        "pet_id": pet_data['id']
    })
    logger.debug("Sample pet data details", extra={
        "pet_data": pet_data
    })
    return pet_data


@pytest.fixture
def updated_pet_data(sample_pet_data: dict) -> dict:
    """Generate updated pet data using the factory"""
    updated_data = PetDataFactory.create_updated_pet(sample_pet_data)

    logger.info("Generated updated pet data", extra={
        "event": "test_data_generation",
        "data_type": "updated_pet",
        "pet_id": updated_data['id']
    })
    logger.debug("Updated pet data details", extra={
        "updated_pet_data": updated_data
    })
    return updated_data


@pytest.fixture
def invalid_pet_data() -> list:
    """Generate various invalid pet data for negative testing"""
    invalid_pets = PetDataFactory.create_invalid_pets()

    logger.info("Generated invalid pet data samples", extra={
        "event": "test_data_generation",
        "data_type": "invalid_pets",
        "sample_count": len(invalid_pets)
    })
    return invalid_pets


@pytest.fixture
def boundary_test_data() -> dict:
    """Generate boundary test cases"""
    boundary_data = PetDataFactory.create_boundary_test_data()

    logger.info("Generated boundary test data", extra={
        "event": "test_data_generation",
        "data_type": "boundary_test",
        "case_count": len(boundary_data)
    })
    return boundary_data
