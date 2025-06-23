"""
Custom Exceptions for Pet Store API Test Framework
Provides specific exception types for better error handling and debugging.
"""

from typing import Any, Optional, Dict


class PetStoreAPIException(Exception):
    """Base exception for Pet Store API related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (Details: {detail_str})"
        return self.message


class PetNotFoundError(PetStoreAPIException):
    """Raised when a pet with the specified ID is not found"""

    def __init__(self, pet_id: int, message: str = None):
        self.pet_id = pet_id
        default_message = f"Pet with ID {pet_id} not found"
        super().__init__(message or default_message, {"pet_id": pet_id})


class PetValidationError(PetStoreAPIException):
    """Raised when pet data validation fails"""

    def __init__(self, field_name: str, field_value: Any, reason: str):
        self.field_name = field_name
        self.field_value = field_value
        self.reason = reason
        message = f"Validation failed for field '{field_name}': {reason}"
        super().__init__(message, {
            "field_name": field_name,
            "field_value": field_value,
            "reason": reason
        })


class PetCreationError(PetStoreAPIException):
    """Raised when pet creation fails"""

    def __init__(self, pet_data: Dict[str, Any], status_code: int, response_text: str = ""):
        self.pet_data = pet_data
        self.status_code = status_code
        self.response_text = response_text

        pet_id = pet_data.get('id', 'unknown')
        message = f"Failed to create pet with ID {pet_id} (HTTP {status_code})"
        super().__init__(message, {
            "pet_id": pet_id,
            "status_code": status_code,
            "response_text": response_text
        })


class PetUpdateError(PetStoreAPIException):
    """Raised when pet update fails or update verification fails"""

    def __init__(self, pet_id: int, expected_changes: Dict[str, Any],
                 actual_data: Dict[str, Any] = None, status_code: int = None):
        self.pet_id = pet_id
        self.expected_changes = expected_changes
        self.actual_data = actual_data
        self.status_code = status_code

        if status_code:
            message = f"Pet update failed for ID {pet_id} (HTTP {status_code})"
        else:
            message = f"Pet update verification failed for ID {pet_id}: expected changes not reflected"

        super().__init__(message, {
            "pet_id": pet_id,
            "expected_changes": expected_changes,
            "actual_data": actual_data,
            "status_code": status_code
        })


class InvalidPetIdError(PetStoreAPIException):
    """Raised when an invalid pet ID is provided"""

    def __init__(self, pet_id: Any, reason: str = "Invalid format"):
        self.pet_id = pet_id
        self.reason = reason
        message = f"Invalid pet ID '{pet_id}': {reason}"
        super().__init__(message, {"pet_id": pet_id, "reason": reason})


class APIConnectionError(PetStoreAPIException):
    """Raised when API connection fails"""

    def __init__(self, url: str, original_exception: Exception):
        self.url = url
        self.original_exception = original_exception
        message = f"Failed to connect to API at {url}: {str(original_exception)}"
        super().__init__(message, {
            "url": url,
            "original_error": str(original_exception),
            "error_type": type(original_exception).__name__
        })


class RetryLimitExceededError(PetStoreAPIException):
    """Raised when maximum retry attempts are exceeded"""

    def __init__(self, operation: str, max_retries: int, last_status_code: int = None):
        self.operation = operation
        self.max_retries = max_retries
        self.last_status_code = last_status_code

        message = f"Operation '{operation}' failed after {max_retries} retry attempts"
        if last_status_code:
            message += f" (last status: {last_status_code})"

        super().__init__(message, {
            "operation": operation,
            "max_retries": max_retries,
            "last_status_code": last_status_code
        })


class TestDataGenerationError(PetStoreAPIException):
    """Raised when test data generation fails"""

    def __init__(self, data_type: str, reason: str):
        self.data_type = data_type
        self.reason = reason
        message = f"Failed to generate {data_type} test data: {reason}"
        super().__init__(message, {"data_type": data_type, "reason": reason})


class TestFrameworkError(PetStoreAPIException):
    """Raised when the test framework itself encounters an error"""

    def __init__(self, component: str, operation: str, reason: str):
        self.component = component
        self.operation = operation
        self.reason = reason
        message = f"Test framework error in {component} during {operation}: {reason}"
        super().__init__(message, {
            "component": component,
            "operation": operation,
            "reason": reason
        })


class StabilityTestError(PetStoreAPIException):
    """Raised when stability tests fail due to poor API reliability"""

    def __init__(self, success_rate: float, threshold: float, total_attempts: int):
        self.success_rate = success_rate
        self.threshold = threshold
        self.total_attempts = total_attempts

        message = (f"API stability below threshold: {success_rate:.1f}% success rate "
                   f"(threshold: {threshold:.1f}%) over {total_attempts} attempts")

        super().__init__(message, {
            "success_rate": success_rate,
            "threshold": threshold,
            "total_attempts": total_attempts
        })


class ConfigurationError(PetStoreAPIException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, config_key: str, reason: str):
        self.config_key = config_key
        self.reason = reason
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(message, {"config_key": config_key, "reason": reason})


# Exception hierarchy for better catching:
"""
Exception Hierarchy:

PetStoreAPIException (base)
├── PetNotFoundError
├── PetValidationError
├── PetCreationError
├── PetUpdateError
├── InvalidPetIdError
├── APIConnectionError
├── RetryLimitExceededError
├── TestDataGenerationError
├── TestFrameworkError
├── StabilityTestError
└── ConfigurationError

Usage Examples:

# Specific catching:
try:
    response = client.get_pet_by_id(pet_id)
except PetNotFoundError as e:
    logger.info(f"Pet not found as expected: {e.pet_id}")
except APIConnectionError as e:
    logger.error(f"Connection failed: {e.url}")

# Category catching:
try:
    response = client.create_pet(pet_data)
except (PetCreationError, PetValidationError) as e:
    logger.error(f"Pet creation failed: {e}")

# All framework errors:
try:
    test_operation()
except PetStoreAPIException as e:
    logger.error(f"Framework error: {e}")
    logger.debug(f"Error details: {e.details}")
"""


def validate_pet_id(pet_id: Any) -> int:
    """
    Validate and convert pet ID to integer.
    Raises InvalidPetIdError for invalid IDs.
    """
    if pet_id is None:
        raise InvalidPetIdError(pet_id, "Pet ID cannot be None")

    if isinstance(pet_id, str):
        try:
            pet_id = int(pet_id)
        except ValueError:
            raise InvalidPetIdError(pet_id, "Pet ID must be a valid integer")

    if not isinstance(pet_id, int):
        raise InvalidPetIdError(pet_id, f"Pet ID must be integer, got {type(pet_id).__name__}")

    if pet_id <= 0:
        raise InvalidPetIdError(pet_id, "Pet ID must be positive")

    if pet_id > 999999999:  # Reasonable upper limit
        raise InvalidPetIdError(pet_id, "Pet ID too large")

    return pet_id


def validate_pet_data(pet_data: Dict[str, Any]) -> None:
    """
    Validate basic pet data structure.
    Raises PetValidationError for invalid data.
    """
    if not isinstance(pet_data, dict):
        raise PetValidationError("pet_data", pet_data, "Must be a dictionary")

    required_fields = ["id", "name", "photoUrls", "status"]
    for field in required_fields:
        if field not in pet_data:
            raise PetValidationError(field, None, "Required field missing")

    # Validate ID
    validate_pet_id(pet_data["id"])

    # Validate name
    if not isinstance(pet_data["name"], str):
        raise PetValidationError("name", pet_data["name"], "Must be a string")

    if not pet_data["name"].strip():
        raise PetValidationError("name", pet_data["name"], "Cannot be empty")

    # Validate photoUrls
    if not isinstance(pet_data["photoUrls"], list):
        raise PetValidationError("photoUrls", pet_data["photoUrls"], "Must be a list")

    # Validate status
    valid_statuses = ["available", "pending", "sold"]
    if pet_data["status"] not in valid_statuses:
        raise PetValidationError("status", pet_data["status"],
                                 f"Must be one of: {valid_statuses}")