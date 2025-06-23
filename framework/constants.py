"""
Test Constants
Centralizes all magic numbers and hardcoded values used throughout the test suite.
"""

from typing import List, Dict, Any


class APIConstants:
    """API-related constants"""
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5
    MAX_RETRY_TIME_SECONDS = 10.0

    # HTTP Status Codes
    HTTP_OK = 200
    HTTP_NOT_FOUND = 404
    HTTP_BAD_REQUEST = 400
    HTTP_INTERNAL_SERVER_ERROR = 500


class PetTestConstants:
    """Pet-specific test constants"""
    # Pet IDs
    NONEXISTENT_PET_ID = 999999999
    TEST_PET_ID_BASE = 1000000
    INVALID_NEGATIVE_ID = -1
    INVALID_ZERO_ID = 0
    INVALID_FLOAT_ID = 3.14
    INVALID_LARGE_ID = 99999999999999999999

    # Test data limits
    MAX_PET_NAME_LENGTH = 1000
    MAX_PHOTO_URLS = 100

    # Valid pet statuses
    VALID_STATUSES = ["available", "pending", "sold"]

    # Invalid test data
    INVALID_ID_VALUES: List[Any] = [
        "not_a_number",
        None,
        INVALID_NEGATIVE_ID,
        INVALID_ZERO_ID,
        INVALID_LARGE_ID,
        INVALID_FLOAT_ID
    ]

    INVALID_STATUSES = ["invalid_status", 123, None, ""]

    BOUNDARY_TEST_VALUES = {
        "empty_name": "",
        "long_name": "x" * MAX_PET_NAME_LENGTH,
        "invalid_url": "invalid-url",
        "many_urls": ["http://example.com"] * MAX_PHOTO_URLS
    }


class TestDataConstants:
    """Test data generation constants"""
    DEFAULT_PET_NAMES = [
        "Buddy", "Max", "Charlie", "Lucy", "Cooper",
        "Bailey", "Rocky", "Sadie", "Molly", "Tucker"
    ]

    DEFAULT_PHOTO_URLS = [
        "https://example.com/pet1.jpg",
        "https://example.com/pet2.jpg",
        "https://example.com/pet3.jpg"
    ]

    CATEGORY_NAMES = [
        "Dogs", "Cats", "Birds", "Fish", "Reptiles",
        "Small Pets", "Farm Animals"
    ]

    TAG_NAMES = [
        "friendly", "playful", "calm", "energetic",
        "trained", "house-broken", "good-with-kids"
    ]


class ValidationConstants:
    """Data validation constants"""
    REQUIRED_PET_FIELDS = ["id", "name", "photoUrls", "status"]
    OPTIONAL_PET_FIELDS = ["category", "tags"]

    # Fields that should match exactly in assertions
    EXACT_MATCH_FIELDS = ["id", "name", "status"]

    # Fields that can have slight variations (like URLs)
    FLEXIBLE_MATCH_FIELDS = ["photoUrls"]


class LoggingConstants:
    """Logging-related constants"""
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s - %(message)s'
    LOG_DATE_FORMAT = '%H:%M:%S'

    # Test phases for logging
    PHASE_SETUP = "SETUP"
    PHASE_EXECUTION = "EXECUTION"
    PHASE_TEARDOWN = "TEARDOWN"
    PHASE_VERIFICATION = "VERIFICATION"

    # Status indicators (without emojis for better parsing)
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILURE = "FAILURE"
    STATUS_WARNING = "WARNING"
    STATUS_SKIPPED = "SKIPPED"


class ErrorMessages:
    """Standardized error messages"""
    PET_NOT_FOUND = "Pet with ID {pet_id} not found"
    INVALID_PET_ID = "Invalid pet ID format: {pet_id}"
    MISSING_REQUIRED_FIELD = "Missing required field: {field_name}"
    INVALID_FIELD_TYPE = "Invalid type for field {field_name}: expected {expected_type}, got {actual_type}"
    UPDATE_VERIFICATION_FAILED = "Pet update verification failed: expected changes not reflected"
    API_CONNECTION_FAILED = "Failed to connect to Pet Store API"
    RETRY_LIMIT_EXCEEDED = "Maximum retry limit exceeded for operation"

    @staticmethod
    def format_pet_not_found(pet_id: int) -> str:
        return ErrorMessages.PET_NOT_FOUND.format(pet_id=pet_id)

    @staticmethod
    def format_invalid_pet_id(pet_id: Any) -> str:
        return ErrorMessages.INVALID_PET_ID.format(pet_id=pet_id)

    @staticmethod
    def format_missing_field(field_name: str) -> str:
        return ErrorMessages.MISSING_REQUIRED_FIELD.format(field_name=field_name)

    @staticmethod
    def format_invalid_field_type(field_name: str, expected_type: str, actual_type: str) -> str:
        return ErrorMessages.INVALID_FIELD_TYPE.format(
            field_name=field_name,
            expected_type=expected_type,
            actual_type=actual_type
        )


class TestCategories:
    """Test category markers for pytest"""
    PET_API = "pet_api"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    STABILITY = "stability"
    PERFORMANCE = "performance"
    REGRESSION = "regression"
    SMOKE = "smoke"
    BOUNDARY = "boundary"

    # Test suites
    CRUD_OPERATIONS = "crud"
    DATA_VALIDATION = "validation"
    ERROR_HANDLING = "error_handling"
    BOUNDARY_TESTING = "boundary"


class StabilityMetrics:
    """Constants for stability tracking and analysis"""
    STABLE_SUCCESS_RATE_THRESHOLD = 95.0  # 95%
    UNSTABLE_SUCCESS_RATE_THRESHOLD = 80.0  # 80%

    # Retry analysis thresholds
    EXCELLENT_RETRY_RATE = 0.1  # Less than 0.1 retries per request
    GOOD_RETRY_RATE = 0.5  # Less than 0.5 retries per request
    POOR_RETRY_RATE = 1.0  # More than 1 retry per request

    # Performance thresholds (in seconds)
    FAST_RESPONSE_TIME = 1.0
    ACCEPTABLE_RESPONSE_TIME = 3.0
    SLOW_RESPONSE_TIME = 5.0


class FileConstants:
    """File and directory constants"""
    LOGS_DIR = "tests/logs"
    REPORTS_DIR = "reports"
    TEST_DATA_DIR = "tests/test_data"

    LOG_FILE_PREFIX = "test_run_"
    REPORT_FILE_PREFIX = "test_summary_"

    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


# Usage examples in docstring
"""
Usage Examples:

# In tests:
from tests.constants import PetTestConstants, APIConstants

def test_get_nonexistent_pet():
    response = client.get_pet_by_id(PetTestConstants.NONEXISTENT_PET_ID)
    assert response.status_code == APIConstants.HTTP_NOT_FOUND

# In API client:
def get_pet_with_retry(self, pet_id: int, max_retries: int = APIConstants.MAX_RETRIES):
    # Implementation

# In assertions:
def assert_status_code(self, response, expected_code=APIConstants.HTTP_OK):
    # Implementation

# Error handling:
if pet_id < 0:
    raise ValueError(ErrorMessages.format_invalid_pet_id(pet_id))
"""