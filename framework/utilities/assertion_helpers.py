"""
Assertion Helper Utilities
Provides enhanced assertion methods for test framework
"""

import logging
from typing import Any, Dict, List, Optional
from framework.api_client import APIResponse


class AssertionHelper:
    """
    Helper class for enhanced assertions
    Used by BaseTest for better assertion messages
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def assert_response_success(self, response: APIResponse, context: str = "") -> None:
        """Assert that response indicates success (2xx status)"""
        if not response.is_success:
            error_msg = f"Expected successful response, got {response.status_code}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        self.logger.debug(f"Success assertion passed: {response.status_code}")

    def assert_json_contains_keys(self, response: APIResponse, required_keys: List[str], context: str = "") -> None:
        """Assert that JSON response contains required keys"""
        try:
            json_data = response.json()
        except Exception as e:
            error_msg = f"Failed to parse JSON response: {e}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            error_msg = f"Missing required keys in JSON response: {missing_keys}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        self.logger.debug(f"JSON keys assertion passed: {required_keys}")

    def assert_json_values_match(self, response: APIResponse, expected_values: Dict[str, Any],
                                 context: str = "") -> None:
        """Assert that JSON response contains expected values"""
        try:
            json_data = response.json()
        except Exception as e:
            error_msg = f"Failed to parse JSON response: {e}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        mismatches = []
        for key, expected_value in expected_values.items():
            if key not in json_data:
                mismatches.append(f"Missing key: {key}")
            elif json_data[key] != expected_value:
                mismatches.append(f"Key '{key}': expected {expected_value}, got {json_data[key]}")

        if mismatches:
            error_msg = f"JSON value mismatches: {'; '.join(mismatches)}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        self.logger.debug(f"JSON values assertion passed for keys: {list(expected_values.keys())}")

    def assert_field_updated(self, original_data: Dict[str, Any], updated_response: APIResponse,
                             field_name: str, expected_value: Any, context: str = "") -> None:
        """Assert that a specific field was updated correctly"""
        try:
            updated_data = updated_response.json()
        except Exception as e:
            error_msg = f"Failed to parse updated response JSON: {e}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        # Check if field exists
        if field_name not in updated_data:
            error_msg = f"Field '{field_name}' not found in updated response"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        # Check if field was actually updated
        actual_value = updated_data[field_name]
        if actual_value != expected_value:
            error_msg = f"Field '{field_name}': expected {expected_value}, got {actual_value}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        # Optional: Check that it actually changed from original
        if field_name in original_data and original_data[field_name] == actual_value:
            self.logger.warning(f"Field '{field_name}' has same value as before update: {actual_value}")

        self.logger.debug(f"Field update assertion passed: {field_name} = {expected_value}")

    def assert_response_time_acceptable(self, response: APIResponse, max_time_seconds: float,
                                        context: str = "") -> None:
        """Assert that response time is within acceptable limits"""
        # Note: This requires response timing to be tracked elsewhere
        # For now, this is a placeholder for future enhancement
        self.logger.debug(f"Response time assertion: max allowed {max_time_seconds}s")

    def soft_assert(self, condition: bool, message: str, context: str = "") -> bool:
        """
        Soft assertion that logs errors but doesn't raise exceptions
        Returns True if assertion passed, False if failed
        """
        if not condition:
            error_msg = message
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(f"Soft assertion failed: {error_msg}")
            return False

        self.logger.debug(f"Soft assertion passed: {message}")
        return True

    def assert_list_contains_item(self, item_list: List[Any], expected_item: Any, context: str = "") -> None:
        """Assert that a list contains a specific item"""
        if expected_item not in item_list:
            error_msg = f"Expected item {expected_item} not found in list: {item_list}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        self.logger.debug(f"List contains item assertion passed: {expected_item}")

    def assert_list_length(self, item_list: List[Any], expected_length: int, context: str = "") -> None:
        """Assert that a list has the expected length"""
        actual_length = len(item_list)
        if actual_length != expected_length:
            error_msg = f"Expected list length {expected_length}, got {actual_length}"
            if context:
                error_msg = f"{context}: {error_msg}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg)

        self.logger.debug(f"List length assertion passed: {expected_length}")