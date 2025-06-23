"""
Base Test Class
"""


import logging
import time
from typing import List, Dict, Any, Optional
from framework.api_client import PetStoreAPIClient, APIResponse
from framework.utilities.validators import ResponseValidator
from framework.utilities.test_helpers import (
    TestDataManager,
    StabilityTracker,
    AssertionHelper,
    timing_context,
    log_test_step
)


class BaseTest:
    """
    Base Test Class
    """

    def __init__(self):
        self.client: Optional[PetStoreAPIClient] = None  # Fixed: Use Optional type annotation
        self.logger = logging.getLogger(f'framework.base_test.{self.__class__.__name__}')

        # Use utility classes instead of inline implementation
        self.test_data_manager = TestDataManager(self.logger)
        self.stability_tracker = StabilityTracker("base_test")
        self.response_validator = ResponseValidator(self.logger)
        self.assertion_helper = AssertionHelper(self.logger)

    def setup_method(self) -> None:
        """Setup method called before each test method by pytest"""
        if not self.client:
            self.client = PetStoreAPIClient()

        self.logger.info(f"BaseTest setup completed for {self.__class__.__name__}")

    def teardown_method(self) -> None:
        """Teardown method called after each test method by pytest"""
        # Use utility for cleanup instead of custom implementation
        if self.client:  # Type guard to ensure client exists
            self.test_data_manager.cleanup_all(self.client)

        # Use utility for stability reporting
        stability_summary = self.stability_tracker.get_summary()
        if "No attempts" not in stability_summary:
            self.logger.info(f"Test stability: {stability_summary}")

        self.logger.info(f"BaseTest teardown completed for {self.__class__.__name__}")

    def setup_test(self) -> None:
        """Manual setup method (for non-pytest usage)"""
        if not hasattr(self, 'client') or not self.client:
            self.client = PetStoreAPIClient()
        self.logger.info(f"Manual test setup completed for {self.__class__.__name__}")

    def teardown_test(self) -> None:
        """Manual cleanup method (for non-pytest usage)"""
        if self.client:  # Type guard
            self.test_data_manager.cleanup_all(self.client)

        stability_summary = self.stability_tracker.get_summary()
        if "No attempts" not in stability_summary:
            self.logger.info(f"Test stability: {stability_summary}")
        self.logger.info(f"Manual test teardown completed for {self.__class__.__name__}")

    def track_pet_for_cleanup(self, pet_id: int) -> None:
        """Track pet for cleanup after test - now uses utility"""
        self.test_data_manager.track_pet(pet_id)

    def _ensure_client(self) -> PetStoreAPIClient:
        """Ensure client is initialized and return it (type-safe helper)"""
        if not self.client:
            self.client = PetStoreAPIClient()
        return self.client

    @log_test_step("GET pet with retry logic")
    def get_pet_with_retry(self, pet_id: int, max_retries: int = 3, delay: float = 0.5) -> APIResponse:
        """
        GET pet with retry logic using utility tracking.
        Much cleaner than the original implementation.
        """
        client = self._ensure_client()  # Type-safe client access
        self.logger.info(f"Starting GET for pet {pet_id} with up to {max_retries} retries")

        retry_count = 0
        last_response = None

        with timing_context(f"GET pet {pet_id} with retries", self.logger):
            for attempt in range(max_retries):
                self.logger.debug(f"GET attempt {attempt + 1}/{max_retries} for pet {pet_id}")

                response = client.get_pet_by_id(pet_id)
                last_response = response

                if response.status_code == 200:
                    # Success - record metrics and return
                    self.stability_tracker.record_attempt(True, attempt)

                    if attempt > 0:
                        self.logger.info(f"✅ GET succeeded after {attempt + 1} attempts for pet {pet_id}")
                    else:
                        self.logger.info(f"✅ GET succeeded on first attempt for pet {pet_id}")

                    return response

                # Failed attempt
                self.logger.warning(
                    f"⚠️ GET attempt {attempt + 1} failed (status: {response.status_code}) for pet {pet_id}")
                retry_count = attempt + 1

                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    self.logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        # All attempts failed - record failure and return last response
        self.stability_tracker.record_attempt(False, retry_count)
        self.logger.error(f"❌ GET failed after {max_retries} attempts for pet {pet_id}")

        # Type guard: ensure we have a response to return
        if last_response is None:
            # This should never happen, but satisfy type checker
            client = self._ensure_client()
            last_response = client.get_pet_by_id(pet_id)

        return last_response

    # Simplified assertion methods using utilities
    def assert_status_code(self, response: APIResponse, expected_code: int, message: Optional[str] = None) -> None:
        """Assert response status code using validator utility"""
        context = message or f"status code check"

        if self.response_validator.validate_status_code(response, expected_code, context):
            self.logger.debug(f"✅ Status code assertion passed: {response.status_code}")
        else:
            error_msg = message or f"Expected status code {expected_code}, got {response.status_code}"
            self.logger.error(f"❌ Status code assertion failed: {error_msg}")
            raise AssertionError(error_msg)

    def assert_pet_data_matches(self, response: APIResponse, expected_data: Dict[str, Any],
                                fields_to_check: Optional[List[str]] = None) -> None:
        """Assert pet data matches using validator utility"""
        fields_to_check = fields_to_check or ["id", "name", "status", "photoUrls"]

        if self.response_validator.validate_pet_data(response, expected_data, fields_to_check):
            self.logger.info(f"✅ Pet data validation passed for {len(fields_to_check)} fields")
        else:
            raise AssertionError("Pet data validation failed - see logs for details")

    def assert_pet_data_updated(self, response: APIResponse, original_data: Dict[str, Any],
                                updated_data: Dict[str, Any]) -> None:
        """Assert pet data was updated using validator utility"""
        # Extract the changes we expect to see
        expected_changes = {}
        for field in ["name", "status", "photoUrls"]:
            if field in updated_data and field in original_data:
                if updated_data[field] != original_data[field]:
                    expected_changes[field] = updated_data[field]

        if self.response_validator.validate_update_occurred(original_data, response, expected_changes):
            self.logger.info("✅ Pet update verification passed")
        else:
            raise AssertionError("Pet update validation failed - see logs for details")

    def get_stability_report(self) -> str:
        """Get stability metrics using utility"""
        return self.stability_tracker.get_summary()

    def get_detailed_stability_report(self) -> str:
        """Get detailed stability report using utility"""
        metrics = self.stability_tracker.get_metrics()
        if "error" in metrics:
            return "📊 No stability data available"

        report = f"""
📊 Detailed API Stability Report:
   Total operations: {metrics['total_attempts']}
   Success rate: {metrics['success_rate']}%
   Average retries: {metrics['average_retries']}
   First-try success: {metrics['first_try_success_rate']}%
   Duration: {metrics['duration_seconds']}s

   Reliability: {'🟢 Stable' if metrics['average_retries'] < 1.0 else
        '🟡 Unstable' if metrics['average_retries'] < 2.0 else
        '🔴 Highly unstable'}
        """
        return report


class EnhancedAPITestSuite(BaseTest):
    """
    Enhanced test suite class that provides additional utilities.
    This demonstrates how to extend the base test with more functionality.
    """

    def __init__(self):
        super().__init__()
        self.test_results: List[Dict[str, Any]] = []  # Added type annotation

    @log_test_step("Complete pet lifecycle test")
    def run_pet_lifecycle_test(self, initial_pet_data: Dict[str, Any],
                               updated_pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a complete pet lifecycle test with comprehensive tracking.
        This shows how the utilities make complex workflows much cleaner.
        """
        client = self._ensure_client()  # Type-safe client access
        pet_id = initial_pet_data["id"]
        self.track_pet_for_cleanup(pet_id)

        results = {
            "pet_id": pet_id,
            "steps": [],
            "overall_success": True
        }

        try:
            # Step 1: Create pet
            with timing_context("Create pet operation"):
                create_response = client.create_pet(initial_pet_data)
                self.assert_status_code(create_response, 200)
                self.assert_pet_data_matches(create_response, initial_pet_data)
                results["steps"].append("✅ Pet created successfully")

            # Step 2: Read pet with retry
            with timing_context("Read pet with retry"):
                read_response = self.get_pet_with_retry(pet_id)
                self.assert_status_code(read_response, 200)
                self.assert_pet_data_matches(read_response, initial_pet_data)
                results["steps"].append("✅ Pet read successfully")

            # Step 3: Update pet
            with timing_context("Update pet operation"):
                update_response = client.update_pet(updated_pet_data)
                self.assert_status_code(update_response, 200)
                results["steps"].append("✅ Pet updated successfully")

            # Step 4: Verify update
            with timing_context("Verify update"):
                verify_response = self.get_pet_with_retry(pet_id)
                self.assert_status_code(verify_response, 200)
                self.assert_pet_data_updated(verify_response, initial_pet_data, updated_pet_data)
                results["steps"].append("✅ Pet update verified successfully")

        except Exception as e:
            results["overall_success"] = False
            results["steps"].append(f"❌ Test failed: {str(e)}")
            self.logger.error(f"Pet lifecycle test failed: {e}")
            raise

        # Record test results
        self.test_results.append(results)
        return results