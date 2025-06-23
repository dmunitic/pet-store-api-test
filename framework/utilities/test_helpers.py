"""
Test helper utilities for common test patterns and operations.
"""
import time
import logging
from typing import Callable, Any, Dict, List, Optional
from functools import wraps
from contextlib import contextmanager

from framework.api_client import APIResponse


def retry_on_condition(max_retries: int = 3, delay: float = 0.5,
                       condition: Callable[[Any], bool] = None):
    """
    Decorator for retrying function calls based on a condition

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        condition: Function that takes the result and returns True if retry is needed
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f'framework.utilities.retry.{func.__name__}')

            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)

                    # If no condition specified, success on any result
                    if condition is None or not condition(result):
                        if attempt > 0:
                            logger.info(f"✅ {func.__name__} succeeded after {attempt + 1} attempts")
                        return result

                    # Condition indicates retry needed
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1} needs retry, waiting {delay}s...")
                        time.sleep(delay)

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries} attempts: {e}")
                        raise

            # All attempts exhausted
            logger.error(f"❌ {func.__name__} failed after {max_retries} attempts")
            return result

        return wrapper

    return decorator


class StabilityTracker:
    """Track API stability metrics across multiple operations"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.retry_counts = []
        self.start_time = time.time()
        self.logger = logging.getLogger(f'framework.utilities.stability.{operation_name}')

    def record_attempt(self, success: bool, retry_count: int = 0):
        """Record the result of an operation attempt"""
        self.attempts += 1
        self.retry_counts.append(retry_count)

        if success:
            self.successes += 1
            self.logger.debug(f"✅ {self.operation_name} succeeded (retries: {retry_count})")
        else:
            self.failures += 1
            self.logger.debug(f"❌ {self.operation_name} failed (retries: {retry_count})")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current stability metrics"""
        if self.attempts == 0:
            return {"error": "No attempts recorded"}

        success_rate = (self.successes / self.attempts) * 100
        avg_retries = sum(self.retry_counts) / len(self.retry_counts)
        duration = time.time() - self.start_time

        return {
            "operation": self.operation_name,
            "total_attempts": self.attempts,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": round(success_rate, 1),
            "average_retries": round(avg_retries, 2),
            "duration_seconds": round(duration, 2),
            "first_try_success_rate": round((self.retry_counts.count(0) / self.attempts) * 100, 1)
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        metrics = self.get_metrics()
        if "error" in metrics:
            return metrics["error"]

        return (f"{metrics['operation']}: {metrics['success_rate']}% success "
                f"({metrics['successes']}/{metrics['total_attempts']}), "
                f"{metrics['average_retries']} avg retries, "
                f"{metrics['first_try_success_rate']}% first-try success")


@contextmanager
def timing_context(operation_name: str, logger: logging.Logger = None):
    """Context manager for timing operations"""
    if logger is None:
        logger = logging.getLogger('framework.utilities.timing')

    start_time = time.time()
    logger.debug(f"⏱️ Starting {operation_name}")

    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"⏱️ {operation_name} completed in {duration:.2f}s")


class TestDataManager:
    """Manage test data lifecycle during test execution"""

    def __init__(self, logger: logging.Logger = None):
        self.created_pets: List[int] = []
        self.logger = logger or logging.getLogger('framework.utilities.test_data')

    def track_pet(self, pet_id: int):
        """Track a pet for cleanup"""
        if pet_id not in self.created_pets:
            self.created_pets.append(pet_id)
            self.logger.debug(f"Tracking pet {pet_id} for cleanup")

    def cleanup_all(self, api_client, ignore_errors: bool = True):
        """Cleanup all tracked test data"""
        if not self.created_pets:
            return

        self.logger.info(f"Cleaning up {len(self.created_pets)} test pets")

        cleanup_results = {"success": 0, "failed": 0, "not_found": 0}

        for pet_id in self.created_pets:
            try:
                response = api_client.delete_pet(pet_id)
                if response.status_code == 200:
                    cleanup_results["success"] += 1
                elif response.status_code == 404:
                    cleanup_results["not_found"] += 1
                else:
                    cleanup_results["failed"] += 1
                    if not ignore_errors:
                        self.logger.error(f"Failed to cleanup pet {pet_id}: {response.status_code}")
            except Exception as e:
                cleanup_results["failed"] += 1
                if not ignore_errors:
                    self.logger.error(f"Exception cleaning up pet {pet_id}: {e}")

        self.logger.info(f"Cleanup results: {cleanup_results}")
        self.created_pets.clear()
        return cleanup_results


class AssertionHelper:
    """Enhanced assertion methods with better error messages"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger('framework.utilities.assertions')

    def assert_response_success(self, response: APIResponse, context: str = ""):
        """Assert response is successful with context"""
        context_msg = f" ({context})" if context else ""

        if response.is_success:
            self.logger.debug(f"✅ Response success assertion passed{context_msg}")
        else:
            error_msg = f"Expected successful response, got {response.status_code}{context_msg}"
            if response.text:
                error_msg += f". Response: {response.text}"
            self.logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg)

    def assert_field_equals(self, response: APIResponse, field: str, expected_value: Any, context: str = ""):
        """Assert specific field value in response"""
        self.assert_response_success(response, f"checking field {field}")

        try:
            data = response.json()
        except Exception as e:
            raise AssertionError(f"Cannot parse response JSON: {e}")

        actual_value = data.get(field)
        context_msg = f" ({context})" if context else ""

        if actual_value == expected_value:
            self.logger.debug(f"✅ Field assertion passed: {field} = {expected_value}{context_msg}")
        else:
            error_msg = f"Field '{field}' mismatch{context_msg}: expected {expected_value}, got {actual_value}"
            self.logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg)

    def assert_has_fields(self, response: APIResponse, required_fields: List[str], context: str = ""):
        """Assert response contains all required fields"""
        self.assert_response_success(response, f"checking required fields")

        try:
            data = response.json()
        except Exception as e:
            raise AssertionError(f"Cannot parse response JSON: {e}")

        missing_fields = [field for field in required_fields if field not in data]
        context_msg = f" ({context})" if context else ""

        if not missing_fields:
            self.logger.debug(f"✅ Required fields assertion passed{context_msg}: {required_fields}")
        else:
            error_msg = f"Missing required fields{context_msg}: {missing_fields}"
            self.logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg)


def log_test_step(step_name: str, logger: logging.Logger = None):
    """Decorator to log test steps clearly"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_logger = logger or logging.getLogger('framework.utilities.test_steps')
            test_logger.info(f"🔧 TEST STEP: {step_name}")

            try:
                result = func(*args, **kwargs)
                test_logger.info(f"✅ STEP COMPLETED: {step_name}")
                return result
            except Exception as e:
                test_logger.error(f"❌ STEP FAILED: {step_name} - {str(e)}")
                raise

        return wrapper

    return decorator


class APITestSuite:
    """Base class for organized API test suites"""

    def __init__(self, api_client, logger: logging.Logger = None):
        self.api_client = api_client
        self.logger = logger or logging.getLogger('framework.utilities.test_suite')
        self.test_data_manager = TestDataManager(logger)
        self.stability_tracker = StabilityTracker("test_suite")
        self.assertion_helper = AssertionHelper(logger)

    def setup_suite(self):
        """Setup method for test suite"""
        self.logger.info(f"🚀 Setting up test suite: {self.__class__.__name__}")

    def teardown_suite(self):
        """Teardown method for test suite"""
        self.logger.info(f"🧹 Tearing down test suite: {self.__class__.__name__}")
        self.test_data_manager.cleanup_all(self.api_client)

        # Log stability metrics
        metrics_summary = self.stability_tracker.get_summary()
        if "No attempts" not in metrics_summary:
            self.logger.info(f"📊 Suite stability: {metrics_summary}")