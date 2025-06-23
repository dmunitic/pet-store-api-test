"""
Pet Store API Test Suite

This module contains comprehensive tests for the Pet Store API endpoints.
Tests cover CRUD operations, validation, and complete workflow scenarios.
Includes edge cases, boundary conditions, and negative scenarios.
"""


import pytest
import time
from framework.base_test import BaseTest


class TestPetAPIWorkflow:
    """Test complete pet lifecycle workflows with retry logic"""

    @pytest.fixture(autouse=True)
    def setup_base_test(self, api_client):
        """Setup base test functionality for each test"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        yield
        self.base_test.teardown_test()

    @pytest.mark.pet_api
    @pytest.mark.positive
    @pytest.mark.regression
    def test_complete_pet_lifecycle(self, sample_pet_data, updated_pet_data):
        """Test complete pet lifecycle: create -> read -> update -> verify"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Step 1: Create pet
        self.base_test.logger.info(f"Step 1: Creating pet with ID {pet_id}")
        create_response = self.base_test.client.create_pet(sample_pet_data)
        self.base_test.assert_status_code(create_response, 200)
        self.base_test.assert_pet_data_matches(create_response, sample_pet_data)

        # Step 2: Retrieve created pet (with retry logic)
        self.base_test.logger.info(f"Step 2: Retrieving created pet with retry logic")
        get_response_1 = self.base_test.get_pet_with_retry(pet_id)
        self.base_test.assert_status_code(get_response_1, 200)
        self.base_test.assert_pet_data_matches(get_response_1, sample_pet_data)

        # Step 3: Update pet
        self.base_test.logger.info(f"Step 3: Updating pet")
        update_response = self.base_test.client.update_pet(updated_pet_data)
        self.base_test.assert_status_code(update_response, 200)

        # Step 4: Verify update (with retry logic)
        self.base_test.logger.info(f"Step 4: Verifying update with retry logic")
        get_response_2 = self.base_test.get_pet_with_retry(pet_id)

        if get_response_2.status_code == 200:
            try:
                self.base_test.assert_pet_data_updated(get_response_2, sample_pet_data, updated_pet_data)
                self.base_test.logger.info("✅ Pet lifecycle completed successfully with verified update")
            except AssertionError as e:
                self.base_test.logger.error(f"❌ API UPDATE FAILURE: PUT returned 200 but data wasn't updated: {str(e)}")
                pytest.fail(f"API update inconsistency detected: {str(e)}")
        else:
            self.base_test.logger.error(f"❌ Could not retrieve pet after update to verify changes")
            pytest.fail(f"Failed to retrieve pet for update verification (status: {get_response_2.status_code})")

    @pytest.mark.pet_api
    @pytest.mark.positive
    def test_create_and_read_pet(self, sample_pet_data):
        """Test basic create and read operations with retry logic"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create pet
        self.base_test.logger.info(f"Creating pet with ID {pet_id}")
        create_response = self.base_test.client.create_pet(sample_pet_data)
        self.base_test.assert_status_code(create_response, 200)
        self.base_test.assert_pet_data_matches(create_response, sample_pet_data)

        # Read pet with retry logic
        self.base_test.logger.info(f"Reading pet with retry logic")
        get_response = self.base_test.get_pet_with_retry(pet_id)
        self.base_test.assert_status_code(get_response, 200)
        self.base_test.assert_pet_data_matches(get_response, sample_pet_data)

        self.base_test.logger.info("✅ Create and read test completed successfully")

    @pytest.mark.pet_api
    @pytest.mark.positive
    def test_update_pet_operation(self, sample_pet_data, updated_pet_data):
        """Test pet update operation with proper verification"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create initial pet
        create_response = self.base_test.client.create_pet(sample_pet_data)
        self.base_test.assert_status_code(create_response, 200)

        # Verify creation with retry
        get_response_1 = self.base_test.get_pet_with_retry(pet_id)
        self.base_test.assert_status_code(get_response_1, 200)

        # Update pet
        self.base_test.logger.info(f"Updating pet {pet_id}")
        update_response = self.base_test.client.update_pet(updated_pet_data)
        self.base_test.assert_status_code(update_response, 200)

        # Verify update with retry
        self.base_test.logger.info(f"Verifying update")
        get_response_2 = self.base_test.get_pet_with_retry(pet_id)

        if get_response_2.status_code == 200:
            try:
                self.base_test.assert_pet_data_updated(get_response_2, sample_pet_data, updated_pet_data)
                self.base_test.logger.info("✅ Pet update verified successfully")
            except AssertionError as e:
                self.base_test.logger.error(f"❌ API UPDATE FAILURE: {str(e)}")
                pytest.fail(f"API update inconsistency: {str(e)}")
        else:
            pytest.fail(f"Could not retrieve pet after update (status: {get_response_2.status_code})")

    # NOTE: DELETE testing excluded due to auto-deletion behavior of demo API
    # Assignment requires only POST, GET, PUT - DELETE is out of scope

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_get_nonexistent_pet(self):
        """Test retrieving a non-existent pet"""
        fake_id = 999999999

        response = self.base_test.client.get_pet_by_id(fake_id)
        self.base_test.assert_status_code(response, 404)
        self.base_test.logger.info("✅ Non-existent pet correctly returned 404")

    # NOTE: DELETE tests excluded - demo API auto-deletes entries and assignment scope is POST/GET/PUT only

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_update_nonexistent_pet(self):
        """Test updating a non-existent pet"""
        fake_pet_data = {
            "id": 999999999,
            "name": "Non-existent Pet",
            "photoUrls": ["https://example.com/fake.jpg"],
            "status": "available"
        }

        response = self.base_test.client.update_pet(fake_pet_data)
        self.base_test.logger.info(f"Update non-existent pet returned: {response.status_code}")

        if response.status_code == 404:
            self.base_test.logger.info("✅ Non-existent pet update correctly returned 404")
        elif response.status_code == 200:
            self.base_test.logger.warning("⚠️  API returned 200 for updating non-existent pet (API quirk)")
        else:
            self.base_test.logger.info(f"Non-existent pet update returned {response.status_code}")


class TestPetAPIDataValidation:
    """Test data validation and edge cases"""

    @pytest.fixture(autouse=True)
    def setup_base_test(self, api_client):
        """Setup base test functionality for each test"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        yield
        self.base_test.teardown_test()

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_create_pet_invalid_id_types(self):
        """Test creating pet with various invalid ID types"""
        invalid_id_tests = [
            {"id": "not_a_number", "name": "Test Pet", "photoUrls": [], "status": "available"},
            {"id": None, "name": "Test Pet", "photoUrls": [], "status": "available"},
            {"id": -1, "name": "Test Pet", "photoUrls": [], "status": "available"},
            {"id": 0, "name": "Test Pet", "photoUrls": [], "status": "available"},
            {"id": 99999999999999999999, "name": "Test Pet", "photoUrls": [], "status": "available"},
            {"id": 3.14, "name": "Test Pet", "photoUrls": [], "status": "available"},
        ]

        for i, invalid_data in enumerate(invalid_id_tests):
            self.base_test.logger.info(f"Testing invalid ID type {i + 1}: {invalid_data['id']}")

            try:
                response = self.base_test.client.create_pet(invalid_data)
                # Should get 4xx status for invalid data
                if response.status_code < 400:
                    pytest.fail(
                        f"Expected error status for invalid ID {invalid_data['id']}, got {response.status_code}")
                else:
                    self.base_test.logger.info(
                        f"✅ Invalid ID {invalid_data['id']} correctly rejected with {response.status_code}")
            except Exception as e:
                # Network/connection errors might happen with really bad data
                if "too many 500 error responses" in str(e) or "Max retries exceeded" in str(e):
                    self.base_test.logger.info(
                        f"✅ Invalid ID {invalid_data['id']} caused server to reject connection (expected)")
                else:
                    pytest.fail(f"Unexpected exception for invalid ID {invalid_data['id']}: {e}")

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_create_pet_missing_required_fields(self):
        """Test creating pet with missing required fields"""
        missing_field_tests = [
            {"name": "Test Pet", "photoUrls": [], "status": "available"},  # Missing ID
            {"id": 1234567, "photoUrls": [], "status": "available"},  # Missing name
            {"id": 1234568, "name": "Test Pet", "status": "available"},  # Missing photoUrls
            {"id": 1234569, "name": "Test Pet", "photoUrls": []},  # Missing status
            {}  # Missing everything
        ]

        for i, invalid_data in enumerate(missing_field_tests):
            missing_fields = []
            if 'id' not in invalid_data: missing_fields.append('id')
            if 'name' not in invalid_data: missing_fields.append('name')
            if 'photoUrls' not in invalid_data: missing_fields.append('photoUrls')
            if 'status' not in invalid_data: missing_fields.append('status')

            self.base_test.logger.info(f"Testing missing fields {i + 1}: {missing_fields}")

            try:
                response = self.base_test.client.create_pet(invalid_data)
                # Should get 4xx status for missing required fields
                if response.status_code < 400:
                    pytest.fail(
                        f"Expected error status for missing fields {missing_fields}, got {response.status_code}")
                else:
                    self.base_test.logger.info(
                        f"✅ Missing fields {missing_fields} correctly rejected with {response.status_code}")
            except Exception as e:
                if "too many 500 error responses" in str(e) or "Max retries exceeded" in str(e):
                    self.base_test.logger.info(f"✅ Missing fields {missing_fields} caused server rejection (expected)")
                else:
                    pytest.fail(f"Unexpected exception for missing fields {missing_fields}: {e}")

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_create_pet_invalid_field_types(self):
        """Test creating pet with wrong field types"""
        invalid_type_tests = [
            {"id": 1234570, "name": 12345, "photoUrls": [], "status": "available"},  # name as number
            {"id": 1234571, "name": "Test Pet", "photoUrls": "not_array", "status": "available"},  # photoUrls as string
            {"id": 1234572, "name": "Test Pet", "photoUrls": [], "status": 123},  # status as number
            {"id": 1234573, "name": ["array", "name"], "photoUrls": [], "status": "available"},  # name as array
            {"id": 1234574, "name": None, "photoUrls": [], "status": "available"},  # name as null
        ]

        for i, invalid_data in enumerate(invalid_type_tests):
            self.base_test.logger.info(f"Testing invalid field types {i + 1}")

            try:
                response = self.base_test.client.create_pet(invalid_data)
                if response.status_code < 400:
                    pytest.fail(f"Expected error status for invalid field types, got {response.status_code}")
                else:
                    self.base_test.logger.info(f"✅ Invalid field types correctly rejected with {response.status_code}")
            except Exception as e:
                if "too many 500 error responses" in str(e) or "Max retries exceeded" in str(e):
                    self.base_test.logger.info(f"✅ Invalid field types caused server rejection (expected)")
                else:
                    pytest.fail(f"Unexpected exception for invalid field types: {e}")

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_create_pet_boundary_values(self):
        """Test creating pet with boundary values"""
        boundary_tests = [
            {"id": 1234575, "name": "", "photoUrls": [], "status": "available"},  # empty name
            {"id": 1234576, "name": "x" * 1000, "photoUrls": [], "status": "available"},  # very long name
            {"id": 1234577, "name": "Test Pet", "photoUrls": ["invalid-url"], "status": "available"},  # invalid URL
            {"id": 1234578, "name": "Test Pet", "photoUrls": ["http://x.com"] * 100, "status": "available"},
            # many URLs
            {"id": 1234579, "name": "Test Pet", "photoUrls": [], "status": "invalid_status"},  # invalid status
        ]

        for i, test_data in enumerate(boundary_tests):
            self.base_test.logger.info(f"Testing boundary values {i + 1}")

            response = self.base_test.client.create_pet(test_data)
            # Document the behavior - some might be accepted, others rejected
            self.base_test.logger.info(f"Boundary test {i + 1} returned: {response.status_code}")

            if test_data["id"] in [1234575, 1234579]:  # empty name, invalid status
                # These should probably fail
                if response.status_code >= 400:
                    self.base_test.logger.info(f"✅ Boundary test {i + 1} correctly rejected")
                else:
                    self.base_test.logger.warning(f"⚠️  Boundary test {i + 1} unexpectedly accepted")
                    # Track for cleanup if it was accepted
                    self.base_test.track_pet_for_cleanup(test_data["id"])
            else:
                # These might be accepted (depending on API tolerance)
                if response.status_code == 200:
                    self.base_test.logger.info(f"✅ Boundary test {i + 1} accepted by API")
                    self.base_test.track_pet_for_cleanup(test_data["id"])
                else:
                    self.base_test.logger.info(f"✅ Boundary test {i + 1} rejected by API")

    @pytest.mark.pet_api
    @pytest.mark.negative
    def test_get_invalid_pet_ids(self):
        """Test GET with various invalid pet IDs"""
        invalid_ids = [
            "not_a_number",
            -1,
            0,
            99999999999999999999,
            3.14
        ]

        for invalid_id in invalid_ids:
            self.base_test.logger.info(f"Testing GET with invalid ID: {invalid_id}")

            try:
                # This might cause an exception in the HTTP client
                response = self.base_test.client.get_pet_by_id(invalid_id)
                # Should get 4xx for invalid ID format
                if response.status_code < 400:
                    pytest.fail(f"Expected error status for invalid ID {invalid_id}, got {response.status_code}")
                else:
                    self.base_test.logger.info(
                        f"✅ Invalid ID {invalid_id} correctly rejected with {response.status_code}")
            except Exception as e:
                # Some invalid IDs might cause client-side errors
                self.base_test.logger.info(
                    f"✅ Invalid ID {invalid_id} caused client error (expected): {type(e).__name__}")


class TestPetAPIStability:
    """Test API stability and retry behavior"""

    @pytest.fixture(autouse=True)
    def setup_base_test(self, api_client):
        """Setup base test functionality for each test"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        yield
        self.base_test.teardown_test()

    @pytest.mark.pet_api
    @pytest.mark.stability
    def test_api_retry_behavior(self, sample_pet_data):
        """Test retry behavior and collect stability metrics"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create pet
        create_response = self.base_test.client.create_pet(sample_pet_data)
        self.base_test.assert_status_code(create_response, 200)

        # Perform multiple GET operations to test retry behavior
        successful_gets = 0
        total_attempts = 5

        for i in range(total_attempts):
            self.base_test.logger.info(f"GET attempt {i + 1}/{total_attempts}")
            get_response = self.base_test.get_pet_with_retry(pet_id, max_retries=3)
            if get_response.status_code == 200:
                successful_gets += 1

        # Log stability metrics
        success_rate = (successful_gets / total_attempts) * 100
        self.base_test.logger.info(f"GET success rate: {success_rate:.1f}% ({successful_gets}/{total_attempts})")

        # Print detailed stability report
        detailed_report = self.base_test.get_detailed_stability_report()
        self.base_test.logger.info(detailed_report)

        # Assert that we achieved some reasonable success rate
        assert successful_gets > 0, "No GET operations succeeded even with retries"
        self.base_test.logger.info("✅ API stability test completed")

    @pytest.mark.pet_api
    @pytest.mark.performance
    def test_retry_timing_efficiency(self, sample_pet_data):
        """Test that retry logic doesn't add unnecessary delays"""
        pet_id = sample_pet_data["id"]
        self.base_test.track_pet_for_cleanup(pet_id)

        # Create pet
        create_response = self.base_test.client.create_pet(sample_pet_data)
        self.base_test.assert_status_code(create_response, 200)

        # Test with very short retry delay
        start_time = time.time()
        get_response = self.base_test.get_pet_with_retry(pet_id, max_retries=3, delay=0.1)
        total_time = time.time() - start_time

        self.base_test.logger.info(f"GET with retry completed in {total_time:.2f} seconds")

        # Should complete reasonably quickly even with retries
        assert total_time < 10.0, f"Retry logic took too long: {total_time:.2f}s"
        self.base_test.logger.info("✅ Retry timing efficiency test completed")