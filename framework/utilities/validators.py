"""
Validation utilities for API responses and data structures.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from framework.api_client import APIResponse


class ResponseValidator:
    """Utilities for validating API responses"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger('framework.utilities.validators')

    def validate_status_code(self, response: APIResponse, expected: int,
                             context: str = "") -> bool:
        """Validate response status code with detailed logging"""
        success = response.status_code == expected

        if success:
            self.logger.debug(f"✅ Status code validation passed: {expected} {context}")
        else:
            self.logger.error(f"❌ Status code validation failed: expected {expected}, "
                              f"got {response.status_code} {context}")

        return success

    def validate_json_structure(self, response: APIResponse,
                                required_fields: List[str]) -> Dict[str, Any]:
        """Validate JSON response has required fields"""
        if not response.is_success:
            raise ValueError(f"Cannot validate JSON structure - response status: {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            raise ValueError(f"Response is not valid JSON: {e}")

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        self.logger.debug(f"✅ JSON structure validation passed for fields: {required_fields}")
        return data

    def validate_pet_data(self, response: APIResponse, expected_pet: Dict[str, Any],
                          fields_to_check: List[str] = None) -> bool:
        """Validate pet data in response matches expected values"""
        if not response.is_success:
            self.logger.error(f"Cannot validate pet data - response status: {response.status_code}")
            return False

        try:
            actual_pet = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse response JSON: {e}")
            return False

        # Default fields to validate
        if fields_to_check is None:
            fields_to_check = ["id", "name", "status", "photoUrls"]

        validation_results = []
        for field in fields_to_check:
            if field not in expected_pet:
                continue

            expected_value = expected_pet[field]
            actual_value = actual_pet.get(field)

            if actual_value == expected_value:
                validation_results.append(f"✅ {field}")
                self.logger.debug(f"Field '{field}' matches: {actual_value}")
            else:
                validation_results.append(f"❌ {field}")
                self.logger.error(f"Field '{field}' mismatch: expected {expected_value}, got {actual_value}")

        success = all(result.startswith("✅") for result in validation_results)
        self.logger.info(f"Pet data validation: {', '.join(validation_results)}")

        return success

    def validate_update_occurred(self, before_data: Dict[str, Any],
                                 after_response: APIResponse,
                                 expected_changes: Dict[str, Any]) -> bool:
        """Validate that update actually occurred by comparing before/after"""
        if not after_response.is_success:
            self.logger.error(f"Cannot validate update - response status: {after_response.status_code}")
            return False

        try:
            after_data = after_response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse after-update response: {e}")
            return False

        changes_verified = []
        for field, expected_new_value in expected_changes.items():
            before_value = before_data.get(field)
            after_value = after_data.get(field)

            if before_value != expected_new_value and after_value == expected_new_value:
                changes_verified.append(f"✅ {field}: {before_value} → {after_value}")
            else:
                changes_verified.append(f"❌ {field}: expected {expected_new_value}, got {after_value}")

        success = all(result.startswith("✅") for result in changes_verified)
        self.logger.info(f"Update validation: {', '.join(changes_verified)}")

        return success


class DataValidator:
    """Utilities for validating data structures and formats"""

    @staticmethod
    def is_valid_pet_id(pet_id: Any) -> bool:
        """Check if pet ID is valid format"""
        try:
            id_int = int(pet_id)
            return id_int > 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_pet_status(status: Any) -> bool:
        """Check if pet status is valid"""
        valid_statuses = ["available", "pending", "sold"]
        return isinstance(status, str) and status in valid_statuses

    @staticmethod
    def is_valid_photo_urls(photo_urls: Any) -> bool:
        """Check if photoUrls field is valid"""
        if not isinstance(photo_urls, list):
            return False
        return all(isinstance(url, str) for url in photo_urls)

    @staticmethod
    def validate_pet_schema(pet_data: Dict[str, Any]) -> List[str]:
        """Validate pet data against expected schema, return list of errors"""
        errors = []

        # Required fields
        required_fields = ["id", "name", "photoUrls", "status"]
        for field in required_fields:
            if field not in pet_data:
                errors.append(f"Missing required field: {field}")

        # Field type validation
        if "id" in pet_data and not DataValidator.is_valid_pet_id(pet_data["id"]):
            errors.append(f"Invalid pet ID: {pet_data['id']}")

        if "name" in pet_data and not isinstance(pet_data["name"], str):
            errors.append(f"Pet name must be string, got: {type(pet_data['name'])}")

        if "photoUrls" in pet_data and not DataValidator.is_valid_photo_urls(pet_data["photoUrls"]):
            errors.append(f"Invalid photoUrls format: {pet_data['photoUrls']}")

        if "status" in pet_data and not DataValidator.is_valid_pet_status(pet_data["status"]):
            errors.append(f"Invalid pet status: {pet_data['status']}")

        return errors


class ErrorAnalyzer:
    """Analyze and categorize API errors for better debugging"""

    @staticmethod
    def categorize_error(response: APIResponse) -> str:
        """Categorize error response for debugging"""
        if response.is_success:
            return "SUCCESS"

        if response.is_client_error:
            if response.status_code == 400:
                return "BAD_REQUEST - Invalid data format"
            elif response.status_code == 404:
                return "NOT_FOUND - Resource doesn't exist"
            elif response.status_code == 409:
                return "CONFLICT - Resource already exists"
            else:
                return f"CLIENT_ERROR - {response.status_code}"

        if response.is_server_error:
            if response.status_code == 500:
                return "SERVER_ERROR - Internal server error"
            elif response.status_code == 503:
                return "SERVICE_UNAVAILABLE - Server temporarily unavailable"
            else:
                return f"SERVER_ERROR - {response.status_code}"

        return f"UNKNOWN_ERROR - {response.status_code}"

    @staticmethod
    def get_error_suggestion(response: APIResponse) -> str:
        """Get suggestion for fixing the error"""
        category = ErrorAnalyzer.categorize_error(response)

        suggestions = {
            "BAD_REQUEST": "Check request data format and required fields",
            "NOT_FOUND": "Verify the resource ID exists or create it first",
            "CONFLICT": "Resource already exists, try updating instead",
            "SERVER_ERROR": "Server issue - consider retry logic",
            "SERVICE_UNAVAILABLE": "API temporarily down - implement retry with backoff"
        }

        for key, suggestion in suggestions.items():
            if category.startswith(key):
                return suggestion

        return "Check API documentation for this status code"