"""
Basic connection and framework validation tests - REFACTORED
IMPROVEMENTS: Uses constants, specific exceptions, and machine-readable logging
"""
import pytest
import logging

# ✅ NEW: Import refactored framework components
from framework.base_test import BaseTest
from framework.constants import APIConstants, LoggingConstants, TestCategories
from framework.exceptions import APIConnectionError, ConfigurationError


class TestAPIConnection:
    """Test basic API connectivity and framework setup - REFACTORED"""

    @pytest.fixture(autouse=True)
    def setup_base_test(self, api_client):
        """✅ SIMPLIFIED: No test_session dependency"""
        self.base_test = BaseTest()
        self.base_test.client = api_client
        self.base_test.setup_test()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Setting up API connection test", extra={
            "event": "test_setup",
            "test_class": self.__class__.__name__,
            "phase": LoggingConstants.PHASE_SETUP
        })
        yield
        self.base_test.teardown_test()

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE, TestCategories.PET_API])
    def test_api_client_initialization(self, api_client, test_category):
        """REFACTORED: Test that API client initializes correctly with structured logging"""
        self.logger.info("Testing API client initialization", extra={
            "operation": "api_client_initialization",
            "test_category": test_category
        })

        try:
            assert api_client is not None, "API client should not be None"
            assert api_client.base_url is not None, "Base URL should be configured"
            assert api_client.api_key is not None, "API key should be configured"
            assert api_client.timeout == APIConstants.DEFAULT_TIMEOUT, f"Timeout should be {APIConstants.DEFAULT_TIMEOUT}"  # ✅ Using constant

            self.logger.info("API client initialized successfully", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "base_url": api_client.base_url,
                "timeout": api_client.timeout,
                "operation": "api_client_initialization"
            })
        except AssertionError as e:
            self.logger.error("API client initialization failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "operation": "api_client_initialization"
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during API client initialization", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE, TestCategories.PET_API])
    def test_api_health_check(self, api_client, test_category):
        """REFACTORED: Test that API is reachable with specific exception handling"""
        self.logger.info("Performing API health check", extra={
            "operation": "api_health_check",
            "test_category": test_category
        })

        try:
            health_status = api_client.health_check()
            assert health_status is True, "API health check should return True"

            self.logger.info("API health check passed", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "health_status": health_status,
                "operation": "api_health_check"
            })
        except APIConnectionError as e:  # ✅ Specific exception
            self.logger.error("API health check failed due to connection", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": "APIConnectionError",
                "error": str(e),
                "operation": "api_health_check"
            })
            pytest.fail(f"API connection failed: {e}")
        except AssertionError as e:
            self.logger.error("API health check assertion failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "operation": "api_health_check"
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during health check", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE])
    def test_framework_setup(self, test_category):
        """REFACTORED: Test that test framework is set up correctly with structured validation"""
        self.logger.info("Testing framework setup", extra={
            "operation": "framework_setup_validation",
            "test_category": test_category
        })

        validation_results = []

        try:
            # Test that we have access to the base_test
            assert self.base_test is not None, "BaseTest should be available"
            validation_results.append("base_test_available")

            # Test that cleanup manager is initialized
            assert hasattr(self.base_test, 'test_data_manager'), "BaseTest should have test_data_manager"
            assert self.base_test.test_data_manager is not None, "test_data_manager should be initialized"
            validation_results.append("test_data_manager_initialized")

            # Test that retry stats are initialized
            assert hasattr(self.base_test, 'stability_tracker'), "BaseTest should have stability_tracker"
            assert self.base_test.stability_tracker is not None, "stability_tracker should be initialized"
            validation_results.append("stability_tracker_initialized")

            # Test that validator is available
            assert hasattr(self.base_test, 'response_validator'), "BaseTest should have response_validator"
            assert self.base_test.response_validator is not None, "response_validator should be initialized"
            validation_results.append("response_validator_initialized")

            # Test that logger is working
            assert hasattr(self.base_test, 'logger'), "BaseTest should have a logger"
            assert isinstance(self.base_test.logger, logging.Logger), "logger should be a Logger instance"
            validation_results.append("logging_system_working")

            self.logger.info("Framework setup validation completed successfully", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "validation_results": validation_results,
                "validated_components": len(validation_results),
                "operation": "framework_setup_validation"
            })

        except AssertionError as e:
            self.logger.error("Framework setup validation failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "validation_results": validation_results,
                "operation": "framework_setup_validation"
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during framework validation", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE])
    def test_logging_system(self, test_category):
        """REFACTORED: Test that logging system works with structured logging"""
        self.logger.info("Testing logging system functionality", extra={
            "operation": "logging_system_test",
            "test_category": test_category
        })

        try:
            # Test different log levels with structured data
            self.logger.debug("Debug level logging test", extra={
                "log_level": "debug",
                "test_type": "logging_functionality"
            })

            self.logger.info("Info level logging test", extra={
                "log_level": "info",
                "test_type": "logging_functionality"
            })

            self.logger.warning("Warning level logging test", extra={
                "log_level": "warning",
                "test_type": "logging_functionality"
            })

            # Test structured data logging
            test_data = {"test": "data", "number": 123, "boolean": True}
            self.logger.info("Structured data logging test", extra={
                "test_data": test_data,
                "operation": "structured_logging_test"
            })

            self.logger.info("Logging system test completed successfully", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "operation": "logging_system_test",
                "log_levels_tested": ["debug", "info", "warning"],
                "structured_logging": True
            })

        except Exception as e:
            self.logger.error("Logging system test failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE])
    def test_api_endpoints_configuration(self, api_client, test_category):
        """REFACTORED: Test that API endpoints are properly configured with error handling"""
        self.logger.info("Testing API endpoints configuration", extra={
            "operation": "endpoints_configuration_test",
            "test_category": test_category
        })

        try:
            # Test that endpoints are accessible
            from config.settings import endpoints

            assert endpoints.pets is not None, "Pet endpoint should be configured"
            assert endpoints.pet_by_id(123) is not None, "Pet by ID endpoint should be configured"

            # ✅ Test with constants
            test_pet_id = 123
            pet_by_id_url = endpoints.pet_by_id(test_pet_id)

            self.logger.info("API endpoints configuration validated", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "pets_endpoint": endpoints.pets,
                "pet_by_id_template": pet_by_id_url,
                "test_pet_id": test_pet_id,
                "operation": "endpoints_configuration_test"
            })

        except ImportError as e:
            self.logger.error("Endpoints configuration import failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": "ImportError",
                "error": str(e)
            })
            raise ConfigurationError("endpoints", f"Import failed: {e}")
        except AssertionError as e:
            self.logger.error("Endpoints configuration validation failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "operation": "endpoints_configuration_test"
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during endpoints validation", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE])
    def test_utilities_integration(self, test_category):
        """REFACTORED: Test that utilities are properly integrated with updated imports"""
        self.logger.info("Testing utilities integration", extra={
            "operation": "utilities_integration_test",
            "test_category": test_category
        })

        integration_results = []

        try:
            # ✅ Test updated utility imports
            from framework.utilities.data_validator import DataValidator
            from tests.test_data.pet_data_factory import PetDataFactory

            # Test data factory
            sample_pet = PetDataFactory.create_complete_pet()  # ✅ Updated method name
            assert "id" in sample_pet, "Factory should create pet with ID"
            assert "name" in sample_pet, "Factory should create pet with name"
            integration_results.append("pet_data_factory_working")

            # ✅ Test data validator with updated API
            validator = DataValidator(self.logger)
            is_valid = validator.validate_pet_structure(sample_pet, strict=False)
            assert isinstance(is_valid, bool), "Validator should return boolean"
            integration_results.append("data_validator_working")

            # Test response validator through base_test
            assert self.base_test.response_validator is not None, "Response validator should be available"
            integration_results.append("response_validator_accessible")

            # Test stability tracker
            metrics = self.base_test.stability_tracker.get_metrics()
            assert isinstance(metrics, dict), "Stability tracker should return metrics dict"
            integration_results.append("stability_tracker_working")

            # ✅ Test assertion helper
            assert self.base_test.assertion_helper is not None, "Assertion helper should be available"
            integration_results.append("assertion_helper_accessible")

            self.logger.info("Utilities integration test completed successfully", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "integration_results": integration_results,
                "utilities_tested": len(integration_results),
                "operation": "utilities_integration_test"
            })

        except ImportError as e:
            self.logger.error("Utilities import failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": "ImportError",
                "error": str(e),
                "integration_results": integration_results
            })
            raise ConfigurationError("utilities", f"Import failed: {e}")
        except AssertionError as e:
            self.logger.error("Utilities integration validation failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "integration_results": integration_results
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during utilities integration test", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise

    @pytest.mark.parametrize("test_category", [TestCategories.SMOKE])
    def test_constants_integration(self, test_category):
        """NEW: Test that constants are properly accessible and have expected values"""
        self.logger.info("Testing constants integration", extra={
            "operation": "constants_integration_test",
            "test_category": test_category
        })

        try:
            # Test API constants
            assert APIConstants.HTTP_OK == 200, "HTTP_OK should be 200"
            assert APIConstants.HTTP_NOT_FOUND == 404, "HTTP_NOT_FOUND should be 404"
            assert APIConstants.DEFAULT_TIMEOUT > 0, "DEFAULT_TIMEOUT should be positive"

            # Test logging constants
            assert hasattr(LoggingConstants, 'STATUS_SUCCESS'), "Should have STATUS_SUCCESS"
            assert hasattr(LoggingConstants, 'STATUS_FAILURE'), "Should have STATUS_FAILURE"

            # Test test categories
            assert hasattr(TestCategories, 'SMOKE'), "Should have SMOKE category"
            assert hasattr(TestCategories, 'PET_API'), "Should have PET_API category"

            self.logger.info("Constants integration test completed successfully", extra={
                "status": LoggingConstants.STATUS_SUCCESS,
                "api_constants_validated": True,
                "logging_constants_validated": True,
                "test_categories_validated": True,
                "operation": "constants_integration_test"
            })

        except AssertionError as e:
            self.logger.error("Constants integration validation failed", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "operation": "constants_integration_test"
            })
            raise
        except Exception as e:
            self.logger.error("Unexpected error during constants integration test", extra={
                "status": LoggingConstants.STATUS_FAILURE,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            raise
