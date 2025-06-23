"""
Data Validator Utility
Validates test data and API responses for the deliberately flaky Pet Store API
"""

import logging
from typing import Dict, Any, List, Optional, Union
from framework.constants import PetTestConstants, ValidationConstants, LoggingConstants
from framework.exceptions import (
    PetValidationError, InvalidPetIdError, validate_pet_data, validate_pet_id
)


class DataValidator:
    """
    Validates pet data structures and API responses
    Designed for testing against a deliberately flaky/unreliable API
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def validate_pet_structure(self, pet_data: Dict[str, Any], strict: bool = True) -> bool:
        """
        Validate basic pet data structure

        Args:
            pet_data: Pet data to validate
            strict: If True, raises exceptions. If False, just logs and returns bool
        """
        try:
            # Use framework's validator instead of duplicating logic
            validate_pet_data(pet_data)
            self.logger.info("Pet data structure validation passed", extra={
                "validation_type": "structure",
                "status": LoggingConstants.STATUS_SUCCESS,
                "pet_id": pet_data.get("id", "unknown")
            })
            return True

        except PetValidationError as e:
            if strict:
                raise
            self.logger.error("Pet data structure validation failed", extra={
                "validation_type": "structure",
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e),
                "pet_id": pet_data.get("id", "unknown")
            })
            return False
        except Exception as e:
            error_msg = f"Unexpected validation error: {e}"
            if strict:
                raise PetValidationError("validation", pet_data, error_msg)
            self.logger.error("Unexpected validation error", extra={
                "validation_type": "structure",
                "status": LoggingConstants.STATUS_FAILURE,
                "error": str(e)
            })
            return False

    def validate_api_response_structure(self, response_data: Dict[str, Any],
                                      expected_fields: List[str] = None) -> bool:
        """
        Validate API response has expected structure
        Useful for the flaky API that sometimes returns unexpected data
        """
        expected_fields = expected_fields or ValidationConstants.REQUIRED_PET_FIELDS

        if not isinstance(response_data, dict):
            self.logger.error("API response structure validation failed", extra={
                "validation_type": "api_response",
                "status": LoggingConstants.STATUS_FAILURE,
                "error": f"Response data must be dictionary, got {type(response_data).__name__}"
            })
            return False

        missing_fields = [field for field in expected_fields if field not in response_data]
        if missing_fields:
            self.logger.error("API response missing expected fields", extra={
                "validation_type": "api_response",
                "status": LoggingConstants.STATUS_FAILURE,
                "missing_fields": missing_fields
            })
            return False

        self.logger.info("API response structure validation passed", extra={
            "validation_type": "api_response",
            "status": LoggingConstants.STATUS_SUCCESS,
            "validated_fields": expected_fields
        })
        return True

    def compare_pet_data(self, original: Dict[str, Any], updated: Dict[str, Any],
                        fields_to_compare: List[str] = None) -> Dict[str, Any]:
        """
        Compare two pet data dictionaries and return differences
        Very useful for the flaky API that claims success but doesn't update
        """
        fields_to_compare = fields_to_compare or ValidationConstants.EXACT_MATCH_FIELDS

        comparison_result = {
            "differences_found": False,
            "changed_fields": {},
            "unchanged_fields": {},
            "missing_fields": [],
            "validation_errors": []
        }

        for field in fields_to_compare:
            if field not in original:
                comparison_result["missing_fields"].append(f"Original missing: {field}")
                continue

            if field not in updated:
                comparison_result["missing_fields"].append(f"Updated missing: {field}")
                continue

            original_value = original[field]
            updated_value = updated[field]

            if original_value != updated_value:
                comparison_result["differences_found"] = True
                comparison_result["changed_fields"][field] = {
                    "original": original_value,
                    "updated": updated_value
                }
                self.logger.info("Field change detected", extra={
                    "field": field,
                    "original_value": original_value,
                    "updated_value": updated_value,
                    "operation": "compare_pet_data"
                })
            else:
                comparison_result["unchanged_fields"][field] = original_value

        # Special handling for the flaky API behavior
        if not comparison_result["differences_found"] and not comparison_result["missing_fields"]:
            self.logger.warning("No differences found in pet data comparison", extra={
                "status": LoggingConstants.STATUS_WARNING,
                "possible_cause": "flaky_api_behavior",
                "description": "API returned 200 but may not have updated data"
            })

        return comparison_result

    def validate_update_was_applied(self, original: Dict[str, Any], updated: Dict[str, Any],
                                  expected_changes: Dict[str, Any]) -> bool:
        """
        Validate that expected updates were actually applied
        Critical for testing the flaky API that returns 200 but doesn't update
        """
        validation_passed = True
        issues = []

        for field, expected_value in expected_changes.items():
            if field not in updated:
                issues.append(f"Field '{field}' missing from updated data")
                validation_passed = False
                continue

            actual_value = updated[field]
            if actual_value != expected_value:
                issues.append(f"Field '{field}': expected {expected_value}, got {actual_value}")
                validation_passed = False
                continue

            # Check that it actually changed from original
            if field in original and original[field] == actual_value:
                issues.append(f"Field '{field}' unchanged from original value: {actual_value}")
                validation_passed = False

        if issues:
            self.logger.error("Update validation failed", extra={
                "validation_type": "update_verification",
                "status": LoggingConstants.STATUS_FAILURE,
                "issues": issues,
                "possible_cause": "flaky_api_behavior"
            })
        else:
            self.logger.info("Update validation passed", extra={
                "validation_type": "update_verification",
                "status": LoggingConstants.STATUS_SUCCESS,
                "verified_changes": list(expected_changes.keys())
            })

        return validation_passed

    def validate_data_consistency(self, pet_data: Dict[str, Any]) -> List[str]:
        """
        Check for data consistency issues
        Helps catch flaky API behavior that returns malformed data
        """
        issues = []

        # Check for obviously invalid combinations
        if pet_data.get("status") == "sold" and not pet_data.get("photoUrls"):
            issues.append("Sold pet should have photos")

        # Check for suspicious ID patterns using constants
        pet_id = pet_data.get("id", 0)
        if pet_id > PetTestConstants.TEST_PET_ID_BASE * 1000:  # Very large ID
            issues.append(f"Suspicious pet ID: {pet_id}")

        # Check for empty but required string fields
        name = pet_data.get("name", "")
        if isinstance(name, str) and not name.strip():
            issues.append("Pet name is empty or whitespace")

        # Check photoUrls format
        photo_urls = pet_data.get("photoUrls", [])
        if isinstance(photo_urls, list):
            for i, url in enumerate(photo_urls):
                if not isinstance(url, str):
                    issues.append(f"PhotoUrl[{i}] is not a string: {type(url).__name__}")

        if issues:
            self.logger.warning("Data consistency issues detected", extra={
                "validation_type": "consistency_check",
                "status": LoggingConstants.STATUS_WARNING,
                "issues": issues,
                "pet_id": pet_data.get("id", "unknown")
            })
        else:
            self.logger.info("Data consistency check passed", extra={
                "validation_type": "consistency_check",
                "status": LoggingConstants.STATUS_SUCCESS,
                "pet_id": pet_data.get("id", "unknown")
            })

        return issues

    def is_data_suspicious(self, pet_data: Dict[str, Any]) -> bool:
        """
        Check if data looks suspicious (might be from flaky API behavior)
        """
        # Check for patterns that indicate flaky API behavior
        suspicious_indicators = []

        # All fields exactly the same (copy/paste behavior)
        name = pet_data.get("name", "")
        if name and len(set(str(pet_data.get(field, "")) for field in ["name", "status"])) == 1:
            suspicious_indicators.append("All text fields identical")

        # ID patterns that suggest auto-generation gone wrong
        pet_id = pet_data.get("id", 0)
        if str(pet_id).endswith("000000"):  # Too many zeros
            suspicious_indicators.append("Suspicious ID pattern")

        # Status/photoUrls mismatch
        status = pet_data.get("status", "")
        photo_urls = pet_data.get("photoUrls", [])
        if status == "available" and len(photo_urls) > 10:  # Too many photos
            suspicious_indicators.append("Suspicious photo count for status")

        if suspicious_indicators:
            self.logger.warning("Suspicious data pattern detected", extra={
                "validation_type": "suspicious_data_check",
                "status": LoggingConstants.STATUS_WARNING,
                "indicators": suspicious_indicators,
                "pet_id": pet_data.get("id", "unknown")
            })
            return True

        return False