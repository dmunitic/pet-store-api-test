"""
Response Validators
Validates API responses for the Pet Store test framework
"""

import logging
from typing import Dict, Any, List
from framework.api_client import APIResponse
from framework.constants import APIConstants


class ResponseValidator:
    """
    Validates API responses and data consistency
    Used by BaseTest for assertion methods
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def validate_status_code(self, response: APIResponse, expected_code: int, context: str = "") -> bool:
        """Validate response status code"""
        if response.status_code != expected_code:
            error_msg = f"Expected status {expected_code}, got {response.status_code}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            return False
        return True

    def validate_pet_data(self, response: APIResponse, expected_data: Dict[str, Any],
                         fields_to_check: List[str]) -> bool:
        """Validate that pet data in response matches expected data"""
        if response.status_code != APIConstants.HTTP_OK:
            self.logger.error(f"Cannot validate pet data - response status: {response.status_code}")
            return False

        try:
            actual_data = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse response JSON: {e}")
            return False

        # Check each required field
        for field in fields_to_check:
            if field not in actual_data:
                self.logger.error(f"Missing field '{field}' in response")
                return False

            if field not in expected_data:
                self.logger.warning(f"Field '{field}' not in expected data, skipping validation")
                continue

            expected_value = expected_data[field]
            actual_value = actual_data[field]

            if actual_value != expected_value:
                self.logger.error(f"Field '{field}' mismatch: expected {expected_value}, got {actual_value}")
                return False

        self.logger.debug(f"Pet data validation passed for fields: {fields_to_check}")
        return True

    def validate_update_occurred(self, original_data: Dict[str, Any], response: APIResponse,
                               expected_changes: Dict[str, Any]) -> bool:
        """Validate that pet update was applied correctly"""
        if response.status_code != APIConstants.HTTP_OK:
            self.logger.error(f"Cannot validate update - response status: {response.status_code}")
            return False

        try:
            updated_data = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse updated response JSON: {e}")
            return False

        # Check that expected changes were applied
        for field, expected_value in expected_changes.items():
            if field not in updated_data:
                self.logger.error(f"Field '{field}' missing from updated response")
                return False

            actual_value = updated_data[field]
            if actual_value != expected_value:
                self.logger.error(f"Update failed for field '{field}': expected {expected_value}, got {actual_value}")
                return False

            # Log the change for debugging
            original_value = original_data.get(field, "missing")
            self.logger.debug(f"Field '{field}' updated: {original_value} → {actual_value}")

        self.logger.debug(f"Update validation passed for {len(expected_changes)} fields")
        return True

    def validate_json_structure(self, response: APIResponse, required_keys: List[str]) -> bool:
        """Validate that JSON response has required structure"""
        try:
            json_data = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return False

        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            self.logger.error(f"Missing required keys in JSON: {missing_keys}")
            return False

        return True

    def validate_error_response(self, response: APIResponse, expected_error_message: str = None) -> bool:
        """Validate error response format and content"""
        if response.is_success:
            self.logger.error(f"Expected error response, got success status: {response.status_code}")
            return False

        # If we expect a specific error message, validate it
        if expected_error_message:
            try:
                error_data = response.json()
                # Common error response fields
                error_fields = ['message', 'error', 'detail', 'description']

                found_message = False
                for field in error_fields:
                    if field in error_data:
                        actual_message = str(error_data[field])
                        if expected_error_message.lower() in actual_message.lower():
                            found_message = True
                            break

                if not found_message:
                    self.logger.error(f"Expected error message '{expected_error_message}' not found in response")
                    return False

            except Exception as e:
                self.logger.warning(f"Could not parse error response JSON: {e}")
                # Still valid if we can't parse but got error status

        return True