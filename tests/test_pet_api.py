"""
Pet Store API Test Suite - CLEAN REFACTORED VERSION

This module contains comprehensive tests for the Pet Store API endpoints.
COMPLETELY CLEANED: No test_session dependencies, all constants, specific exceptions
"""

import pytest
import time
import logging

# ✅ Import refactored framework components
from framework.base_test import BaseTest
from framework.constants import (
    PetTestConstants, APIConstants, TestCategories,
    LoggingConstants, StabilityMetrics
)
from framework.exceptions import (
    PetNotFoundError, APIConnectionError, InvalidPetIdError,
    RetryLimitExceededError, PetUpdateError, PetValidationError
)


class TestPetAPIWorkflow:
    """Test complete pet lifecycle workflows - CLEAN VERSION"""

    @pytest.fixture(autouse=True)
    def setup_pet_test(self, api_client):
        """CLEAN: No test_session dependency"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        self.logger = logging.getLogger(self.__class__.__name__)
        yield
        self.base_test.teardown_test()

    @pytest.mark.parametrize("test_category", [
        TestCategories.PET_API,
        TestCategories.POSITIVE,
        TestCategories.REGRESSION
    ])
    def test_complete_pet_lifecycle(self, sample_pet_data, updated_pet_data, test_category):
        """Complete pet lifecycle with constants and specific exceptions"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Step 1: Create pet
        self.logger.info("Creating pet for lifecycle test", extra={
            "step": 1,
            "operation": "create_pet",
            "pet_id": pet_id,
            "test_category": test_category
        })

        try:
            create_response = self.base_test.client.create_pet(sample_pet_data)
            self.base_test.assert_status_code(create_response, APIConstants.HTTP_OK)
            self.base_test.assert_pet_data_matches(create_response, sample_pet_data)
        except (APIConnectionError, PetValidationError) as e:
            self.logger.error("Pet creation failed", extra={
                "step": 1,
                "error_type": type(e).__name__,
                "error": str(e),
                "pet_id": pet_id
            })
            pytest.fail(f"Pet creation failed: {e}")

        # Step 2: Retrieve created pet
        self.logger.info("Retrieving created pet with retry logic", extra={
            "step": 2,
            "operation": "get_pet_with_retry",
            "pet_id": pet_id
        })

        try:
            get_response_1 = self.base_test.get_pet_with_retry(
                pet_id,
                max_retries=APIConstants.MAX_RETRIES
            )
            self.base_test.assert_status_code(get_response_1, APIConstants.HTTP_OK)
            self.base_test.assert_pet_data_matches(get_response_1, sample_pet_data)
        except RetryLimitExceededError as e:
            self.logger.error("Failed to retrieve pet after creation", extra={
                "step": 2,
                "error_type": "RetryLimitExceededError",
                "max_retries": APIConstants.MAX_RETRIES,
                "pet_id": pet_id
            })
            pytest.fail(f"Failed to retrieve pet after creation: {e}")
        except PetNotFoundError as e:
            self.logger.error("Created pet not found", extra={
                "step": 2,
                "error_type": "PetNotFoundError",
                "pet_id": pet_id,
                "possible_cause": "flaky_api_auto_cleanup"
            })
            pytest.fail(f"Created pet not found: {e}")

        # Step 3: Update pet
        self.logger.info("Updating pet", extra={
            "step": 3,
            "operation": "update_pet",
            "pet_id": pet_id
        })

        try:
            update_response = self.base_test.client.update_pet(updated_pet_data)
            self.base_test.assert_status_code(update_response, APIConstants.HTTP_OK)
        except APIConnectionError as e:
            self.logger.error("Pet update failed due to connection", extra={
                "step": 3,
                "error_type": "APIConnectionError",
                "error": str(e)
            })
            pytest.fail(f"API connection failed during pet update: {e}")

        # Step 4: Verify update
        self.logger.info("Verifying update with retry logic", extra={
            "step": 4,
            "operation": "verify_update",
            "pet_id": pet_id
        })

        try:
            get_response_2 = self.base_test.get_pet_with_retry(
                pet_id,
                max_retries=APIConstants.MAX_RETRIES
            )

            if get_response_2.status_code == APIConstants.HTTP_OK:
                try:
                    self.base_test.assert_pet_data_updated(get_response_2, sample_pet_data, updated_pet_data)
                    self.logger.info("Pet lifecycle completed successfully", extra={
                        "operation": "complete_lifecycle",
                        "status": LoggingConstants.STATUS_SUCCESS,
                        "pet_id": pet_id
                    })
                except PetUpdateError as e:
                    self.logger.error("API update failure detected", extra={
                        "error_type": "PetUpdateError",
                        "description": "PUT returned 200 but data wasn't updated",
                        "possible_cause": "flaky_api_behavior",
                        "pet_id": pet_id
                    })
                    pytest.fail(f"API update inconsistency detected: {e}")
            else:
                self.logger.error("Could not retrieve pet after update", extra={
                    "step": 4,
                    "status_code": get_response_2.status_code,
                    "pet_id": pet_id
                })
                pytest.fail(f"Failed to retrieve pet for update verification (status: {get_response_2.status_code})")

        except RetryLimitExceededError as e:
            self.logger.error("Failed to verify pet update", extra={
                "step": 4,
                "error_type": "RetryLimitExceededError",
                "error": str(e)
            })
            pytest.fail(f"Failed to verify pet update: {e}")

    @pytest.mark.parametrize("test_category", [TestCategories.PET_API, TestCategories.POSITIVE])
    def test_create_and_read_pet(self, sample_pet_data, test_category):
        """Test basic create and read operations"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create pet
        self.logger.info("Creating pet", extra={
            "operation": "create_pet",
            "pet_id": pet_id
        })

        try:
            create_response = self.base_test.client.create_pet(sample_pet_data)
            self.base_test.assert_status_code(create_response, APIConstants.HTTP_OK)
            self.base_test.assert_pet_data_matches(create_response, sample_pet_data)
        except (APIConnectionError, PetValidationError) as e:
            pytest.fail(f"Pet creation failed: {e}")

        # Read pet with retry logic
        self.logger.info("Reading pet with retry logic", extra={
            "operation": "read_pet_with_retry",
            "pet_id": pet_id
        })

        try:
            get_response = self.base_test.get_pet_with_retry(pet_id)
            self.base_test.assert_status_code(get_response, APIConstants.HTTP_OK)
            self.base_test.assert_pet_data_matches(get_response, sample_pet_data)

            self.logger.info("Create and read test completed successfully", extra={
                "operation": "create_and_read",
                "status": LoggingConstants.STATUS_SUCCESS,
                "pet_id": pet_id
            })
        except (RetryLimitExceededError, PetNotFoundError) as e:
            pytest.fail(f"Pet read failed: {e}")

    @pytest.mark.parametrize("test_category", [TestCategories.PET_API, TestCategories.NEGATIVE])
    def test_get_nonexistent_pet(self, test_category):
        """Test retrieving non-existent pet"""
        self.logger.info("Testing non-existent pet retrieval", extra={
            "operation": "get_nonexistent_pet",
            "pet_id": PetTestConstants.NONEXISTENT_PET_ID
        })

        try:
            response = self.base_test.client.get_pet_by_id(PetTestConstants.NONEXISTENT_PET_ID)
            self.base_test.assert_status_code(response, APIConstants.HTTP_NOT_FOUND)
            self.logger.info("Non-existent pet correctly returned 404", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "expected_behavior": True
            })
        except APIConnectionError as e:
            pytest.fail(f"API connection failed: {e}")


class TestPetAPIDataValidation:
    """Test data validation and edge cases - CLEAN VERSION"""

    @pytest.fixture(autouse=True)
    def setup_validation_test(self, api_client):
        """Setup for validation tests - CLEAN"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        self.logger = logging.getLogger(self.__class__.__name__)
        yield
        self.base_test.teardown_test()

    @pytest.mark.parametrize("invalid_id", PetTestConstants.INVALID_ID_VALUES)
    @pytest.mark.parametrize("test_category", [TestCategories.PET_API, TestCategories.NEGATIVE])
    def test_create_pet_invalid_id_types(self, invalid_id, test_category):
        """Test creating pet with invalid ID types"""
        invalid_pet_data = {
            "id": invalid_id,
            "name": "Test Pet",
            "photoUrls": [],
            "status": "available"
        }

        self.logger.info("Testing invalid pet ID", extra={
            "operation": "create_pet_invalid_id",
            "invalid_id": invalid_id,
            "invalid_id_type": type(invalid_id).__name__
        })

        try:
            # Try framework validation first
            from framework.exceptions import validate_pet_id
            validate_pet_id(invalid_id)
            pytest.fail(f"Expected InvalidPetIdError for ID: {invalid_id}")
        except InvalidPetIdError:
            self.logger.info("Invalid ID correctly rejected by validation", extra={
                "validation_result": "rejected",
                "invalid_id": invalid_id,
                "expected_behavior": True
            })
            return

        # If validation passed, try API call
        try:
            response = self.base_test.client.create_pet(invalid_pet_data)
            if response.status_code < APIConstants.HTTP_BAD_REQUEST:
                pytest.fail(f"Expected error status for invalid ID {invalid_id}, got {response.status_code}")
            else:
                self.logger.info("Invalid ID correctly rejected by API", extra={
                    "api_result": "rejected",
                    "status_code": response.status_code,
                    "invalid_id": invalid_id
                })
        except APIConnectionError as e:
            self.logger.info("Invalid ID caused connection error", extra={
                "result": "connection_error",
                "error": str(e),
                "expected_behavior": True
            })


class TestPetAPIStability:
    """Test API stability and retry behavior - CLEAN VERSION"""

    @pytest.fixture(autouse=True)
    def setup_stability_test(self, api_client):
        """Setup for stability tests - CLEAN"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        self.logger = logging.getLogger(self.__class__.__name__)
        yield
        self.base_test.teardown_test()

    @pytest.mark.parametrize("test_category", [TestCategories.PET_API, TestCategories.STABILITY])
    def test_api_retry_behavior(self, sample_pet_data, test_category):
        """Test retry behavior and collect stability metrics"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create pet
        try:
            create_response = self.base_test.client.create_pet(sample_pet_data)
            self.base_test.assert_status_code(create_response, APIConstants.HTTP_OK)
        except (APIConnectionError, PetValidationError) as e:
            pytest.fail(f"Setup failed for stability test: {e}")

        # Perform stability testing
        successful_operations = 0
        STABILITY_TEST_ATTEMPTS = 5

        for i in range(STABILITY_TEST_ATTEMPTS):
            self.logger.info("Stability test attempt", extra={
                "attempt": i + 1,
                "total_attempts": STABILITY_TEST_ATTEMPTS,
                "pet_id": pet_id
            })

            try:
                get_response = self.base_test.get_pet_with_retry(
                    pet_id,
                    max_retries=APIConstants.MAX_RETRIES
                )
                if get_response.status_code == APIConstants.HTTP_OK:
                    successful_operations += 1
            except RetryLimitExceededError:
                self.logger.warning("Stability test attempt failed after retries", extra={
                    "attempt": i + 1,
                    "result": "failed_after_retries"
                })
            except APIConnectionError as e:
                self.logger.error("Connection error during stability test", extra={
                    "attempt": i + 1,
                    "error": str(e)
                })

        # Log stability metrics
        success_rate = (successful_operations / STABILITY_TEST_ATTEMPTS) * 100
        self.logger.info("Stability test completed", extra={
            "success_rate": success_rate,
            "successful_operations": successful_operations,
            "total_attempts": STABILITY_TEST_ATTEMPTS,
            "operation": "stability_test_summary"
        })

        # Assert minimum stability
        assert successful_operations > 0, "No operations succeeded even with retries"
        self.logger.info("API stability test completed", extra={
            "final_result": LoggingConstants.STATUS_SUCCESS,
            "success_rate": success_rate
        })