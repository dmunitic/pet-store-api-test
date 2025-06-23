"""
Basic connection and framework validation tests
"""
import pytest
import logging
from framework.base_test import BaseTest


class TestAPIConnection:
    """Test basic API connectivity and framework setup"""

    @pytest.fixture(autouse=True)
    def setup_base_test(self, api_client):
        """Setup base test functionality for each test"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        self.logger = logging.getLogger('tests.TestAPIConnection')
        self.logger.info("Setting up API connection test")
        yield
        self.base_test.teardown_test()

    @pytest.mark.smoke
    def test_api_client_initialization(self, api_client):
        """Test that API client initializes correctly"""
        self.logger.info("Testing API client initialization")

        assert api_client is not None, "API client should not be None"
        assert api_client.base_url is not None, "Base URL should be configured"
        assert api_client.api_key is not None, "API key should be configured"

        self.logger.info(f"✅ API client initialized successfully with base URL: {api_client.base_url}")

    @pytest.mark.smoke
    def test_api_health_check(self, api_client):
        """Test that API is reachable"""
        self.logger.info("Performing API health check")

        health_status = api_client.health_check()
        assert health_status is True, "API health check should return True"

        self.logger.info("✅ API health check passed - API is reachable")

    @pytest.mark.smoke
    def test_framework_setup(self):
        """Test that test framework is set up correctly"""
        self.logger.info("Testing framework setup")

        # Test that we have access to the base_test
        assert self.base_test is not None, "BaseTest should be available"
        self.logger.debug("✅ BaseTest is available")

        # Test that cleanup list is initialized
        assert hasattr(self.base_test, 'test_data_manager'), "BaseTest should have test_data_manager"
        assert self.base_test.test_data_manager is not None, "test_data_manager should be initialized"
        self.logger.debug("✅ Test data manager is properly initialized")

        # Test that retry stats are initialized
        assert hasattr(self.base_test, 'stability_tracker'), "BaseTest should have stability_tracker"
        assert self.base_test.stability_tracker is not None, "stability_tracker should be initialized"
        self.logger.debug("✅ Stability tracker is properly initialized")

        # Test that validator is available
        assert hasattr(self.base_test, 'response_validator'), "BaseTest should have response_validator"
        assert self.base_test.response_validator is not None, "response_validator should be initialized"
        self.logger.debug("✅ Response validator is properly initialized")

        # Test that logger is working
        assert hasattr(self.base_test, 'logger'), "BaseTest should have a logger"
        assert isinstance(self.base_test.logger, logging.Logger), "logger should be a Logger instance"
        self.logger.debug("✅ Logging system is properly configured")

        self.logger.info("✅ Framework setup test completed successfully")

    @pytest.mark.smoke
    def test_logging_system(self):
        """Test that logging system is working correctly"""
        self.logger.info("Testing logging system functionality")

        # Test different log levels
        self.logger.debug("Debug level logging test")
        self.logger.info("Info level logging test")
        self.logger.warning("Warning level logging test")

        # Test that we can log structured data
        test_data = {"test": "data", "number": 123}
        self.logger.info(f"Structured data logging test: {test_data}")

        self.logger.info("✅ Logging system test completed successfully")

    @pytest.mark.smoke
    def test_api_endpoints_configuration(self, api_client):
        """Test that API endpoints are properly configured"""
        self.logger.info("Testing API endpoints configuration")

        # Test that endpoints are accessible
        from config.settings import endpoints

        assert endpoints.pets is not None, "Pet endpoint should be configured"
        assert endpoints.pet_by_id(123) is not None, "Pet by ID endpoint should be configured"

        self.logger.info(f"✅ Endpoints configured - Pets: {endpoints.pets}")
        self.logger.info(f"✅ Pet by ID endpoint template working: {endpoints.pet_by_id(123)}")

        self.logger.info("✅ API endpoints configuration test completed successfully")

    @pytest.mark.smoke
    def test_utilities_integration(self):
        """Test that utilities are properly integrated"""
        self.logger.info("Testing utilities integration")

        # Test that we can use the utilities through base_test
        from framework.utilities.validators import DataValidator
        from tests.test_data.pet_data_factory import PetDataFactory

        # Test data factory
        sample_pet = PetDataFactory.create_basic_pet()
        assert "id" in sample_pet, "Factory should create pet with ID"
        assert "name" in sample_pet, "Factory should create pet with name"
        self.logger.debug("✅ Pet data factory working")

        # Test data validator
        validation_errors = DataValidator.validate_pet_schema(sample_pet)
        assert isinstance(validation_errors, list), "Validator should return list of errors"
        self.logger.debug("✅ Data validator working")

        # Test response validator through base_test
        assert self.base_test.response_validator is not None, "Response validator should be available"
        self.logger.debug("✅ Response validator accessible")

        # Test stability tracker
        metrics = self.base_test.stability_tracker.get_metrics()
        assert isinstance(metrics, dict), "Stability tracker should return metrics dict"
        self.logger.debug("✅ Stability tracker working")

        self.logger.info("✅ Utilities integration test completed successfully")