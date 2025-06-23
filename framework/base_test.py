"""
Base Test Class
"""

import logging
import time
from typing import List, Dict, Any, Optional
from framework.api_client import PetStoreAPIClient, APIResponse
from framework.utilities.response_validator import ResponseValidator
from framework.utilities.test_helpers import (
    TestDataManager,
    StabilityTracker,
    AssertionHelper,
    timing_context,
    log_test_step
)

# Import new constants and exceptions
from framework.constants import APIConstants, PetTestConstants, LoggingConstants
from framework.exceptions import (
    PetNotFoundError, APIConnectionError, RetryLimitExceededError,
    PetUpdateError, InvalidPetIdError, validate_pet_id
)


class BaseTest:
    """
    Base Test Class
    """

    def __init__(self):
        self.client: Optional[PetStoreAPIClient] = None
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
    def get_pet_with_retry(self, pet_id: int, max_retries: int = None, delay: float = None) -> APIResponse:
        """
        GET pet with retry logic using utility tracking.
        """
        # Use constants with defaults
        max_retries = max_retries or APIConstants.MAX_RETRIES
        delay = delay or APIConstants.RETRY_DELAY

        # Validate input early
        try:
            validated_id = validate_pet_id(pet_id)
        except InvalidPetIdError as e:
            self.logger.error(f"Invalid pet ID in retry logic: {e}")
            raise

        client = self._ensure_client()
        self.logger.info(f"Starting GET for pet {validated_id} with up to {max_retries} retries")

        retry_count = 0
        last_response = None
        last_exception = None

        with timing_context(f"GET pet {validated_id} with retries", self.logger):
            for attempt in range(max_retries):
                self.logger.debug(f"GET attempt {attempt + 1}/{max_retries} for pet {validated_id}")

                try:
                    response = client.get_pet_by_id(validated_id)
                    last_response = response

                    if response.status_code == APIConstants.HTTP_OK:
                        # Success - record metrics and return
                        self.stability_tracker.record_attempt(True, attempt)

                        if attempt > 0:
                            self.logger.info(f"GET succeeded after {attempt + 1} attempts for pet {validated_id}")
                        else:
                            self.logger.info(f"GET succeeded on first attempt for pet {validated_id}")

                        return response

                    # Handle specific HTTP errors
                    elif response.status_code == APIConstants.HTTP_NOT_FOUND:
                        # Don't retry for 404 - pet truly doesn't exist
                        self.stability_tracker.record_attempt(False, attempt + 1)
                        raise PetNotFoundError(validated_id)

                    # Other errors - continue retrying
                    self.logger.warning(
                        f"GET attempt {attempt + 1} failed (status: {response.status_code}) for pet {validated_id}")
                    retry_count = attempt + 1

                except PetNotFoundError:
                    # Don't retry for pet not found
                    raise
                except APIConnectionError as e:
                    # Connection errors - might be worth retrying
                    last_exception = e
                    self.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                    retry_count = attempt + 1
                except Exception as e:
                    # Unexpected errors
                    last_exception = e
                    self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    retry_count = attempt + 1

                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    self.logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        # All attempts failed - record failure and raise appropriate exception
        self.stability_tracker.record_attempt(False, retry_count)
        self.logger.error(f"GET failed after {max_retries} attempts for pet {validated_id}")

        # Raise specific exception instead of returning failed response
        if last_exception:
            raise RetryLimitExceededError(
                operation=f"GET pet {validated_id}",
                max_retries=max_retries,
                last_status_code=last_response.status_code if last_response else None
            )

        # If we have a response but it's not successful
        if last_response:
            if last_response.status_code == APIConstants.HTTP_NOT_FOUND:
                raise PetNotFoundError(validated_id)
            else:
                raise RetryLimitExceededError(
                    operation=f"GET pet {validated_id}",
                    max_retries=max_retries,
                    last_status_code=last_response.status_code
                )

        # Should never reach here, but safety fallback
        raise RetryLimitExceededError(f"GET pet {validated_id}", max_retries)

    def assert_status_code(self, response: APIResponse, expected_code: int = None, message: Optional[str] = None) -> None:
        """Assert response status code using validator utility"""
        # Default to success status code
        expected_code = expected_code or APIConstants.HTTP_OK
        context = message or f"status code check"

        if self.response_validator.validate_status_code(response, expected_code, context):
            self.logger.info(f"Status code assertion passed: {response.status_code}")
        else:
            error_msg = message or f"Expected status code {expected_code}, got {response.status_code}"
            self.logger.error(f"Status code assertion failed: {error_msg}")
            raise AssertionError(error_msg)

    def assert_pet_data_matches(self, response: APIResponse, expected_data: Dict[str, Any],
                                fields_to_check: Optional[List[str]] = None) -> None:
        """Assert pet data matches using validator utility"""
        fields_to_check = fields_to_check or ["id", "name", "status", "photoUrls"]

        if self.response_validator.validate_pet_data(response, expected_data, fields_to_check):
            self.logger.info(f"Pet data validation passed for {len(fields_to_check)} fields")
        else:
            raise AssertionError("Pet data validation failed - see logs for details")

    def assert_pet_data_updated(self, response: APIResponse, original_data: Dict[str, Any],
                                updated_data: Dict[str, Any]) -> None:

        pet_id = original_data.get('id', 'unknown')

        # Extract the changes we expect to see
        expected_changes = {}
        for field in ["name", "status", "photoUrls"]:
            if field in updated_data and field in original_data:
                if updated_data[field] != original_data[field]:
                    expected_changes[field] = updated_data[field]

        try:
            if self.response_validator.validate_update_occurred(original_data, response, expected_changes):
                self.logger.info("Pet update verification passed")
            else:
                # Raise specific exception instead of generic AssertionError
                raise PetUpdateError(
                    pet_id=pet_id,
                    expected_changes=expected_changes,
                    actual_data=response.json() if response.status_code == APIConstants.HTTP_OK else None
                )
        except Exception as e:
            if isinstance(e, PetUpdateError):
                raise
            # Convert other validation errors to PetUpdateError
            raise PetUpdateError(pet_id, expected_changes) from e

    def get_stability_report(self) -> str:
        """Get stability metrics using utility"""
        return self.stability_tracker.get_summary()

    def get_detailed_stability_report(self) -> str:
        """
        Get detailed stability report using utility
        REFACTORED: Uses constants for thresholds
        """
        metrics = self.stability_tracker.get_metrics()
        if "error" in metrics:
            return "No stability data available"

        avg_retries = metrics.get('average_retries', 0)
        if avg_retries < 1.0:
            reliability = "Stable"
        elif avg_retries < 2.0:
            reliability = "Unstable"
        else:
            reliability = "Highly unstable"

        report = f"""
Detailed API Stability Report:
   Total operations: {metrics['total_attempts']}
   Success rate: {metrics['success_rate']}%
   Average retries: {avg_retries}
   First-try success: {metrics['first_try_success_rate']}%
   Duration: {metrics['duration_seconds']}s
   Reliability: {reliability}
        """
        return report


class EnhancedAPITestSuite(BaseTest):
    """
    Enhanced test suite class that provides additional utilities.
    """

    def __init__(self):
        super().__init__()
        self.test_results: List[Dict[str, Any]] = []

    @log_test_step("Complete pet lifecycle test")
    def run_pet_lifecycle_test(self, initial_pet_data: Dict[str, Any],
                               updated_pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a complete pet lifecycle test with comprehensive tracking.
        """
        client = self._ensure_client()
        pet_id = initial_pet_data["id"]

        # Validate pet ID early
        try:
            validated_id = validate_pet_id(pet_id)
        except InvalidPetIdError as e:
            self.logger.error(f"Invalid pet ID in lifecycle test: {e}")
            raise

        self.track_pet_for_cleanup(validated_id)

        results = {
            "pet_id": validated_id,
            "steps": [],
            "overall_success": True
        }

        try:
            # Step 1: Create pet
            with timing_context("Create pet operation"):
                create_response = client.create_pet(initial_pet_data)
                self.assert_status_code(create_response, APIConstants.HTTP_OK)
                self.assert_pet_data_matches(create_response, initial_pet_data)
                results["steps"].append("Pet created successfully")

            # Step 2: Read pet with retry
            with timing_context("Read pet with retry"):
                read_response = self.get_pet_with_retry(validated_id)
                self.assert_status_code(read_response, APIConstants.HTTP_OK)
                self.assert_pet_data_matches(read_response, initial_pet_data)
                results["steps"].append("Pet read successfully")

            # Step 3: Update pet
            with timing_context("Update pet operation"):
                update_response = client.update_pet(updated_pet_data)
                self.assert_status_code(update_response, APIConstants.HTTP_OK)
                results["steps"].append("Pet updated successfully")

            # Step 4: Verify update
            with timing_context("Verify update"):
                verify_response = self.get_pet_with_retry(validated_id)
                self.assert_status_code(verify_response, APIConstants.HTTP_OK)
                self.assert_pet_data_updated(verify_response, initial_pet_data, updated_pet_data)
                results["steps"].append("Pet update verified successfully")

        except (PetNotFoundError, APIConnectionError, PetUpdateError, RetryLimitExceededError) as e:
            # Specific exception handling
            results["overall_success"] = False
            results["steps"].append(f"Test failed: {type(e).__name__}: {str(e)}")
            self.logger.error(f"Pet lifecycle test failed with {type(e).__name__}: {e}")
            raise
        except Exception as e:
            # Unexpected errors
            results["overall_success"] = False
            results["steps"].append(f"Test failed with unexpected error: {str(e)}")
            self.logger.error(f"Pet lifecycle test failed unexpectedly: {e}")
            raise

        # Record test results
        self.test_results.append(results)
        return results