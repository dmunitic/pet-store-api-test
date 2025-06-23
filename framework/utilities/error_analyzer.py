"""
Error Analyzer Utility
Analyzes and categorizes errors from the deliberately flaky Pet Store API
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from framework.api_client import APIResponse
from framework.constants import APIConstants, LoggingConstants


class ErrorCategory(Enum):
    """Categories of errors we might encounter with the flaky API"""
    NETWORK_ERROR = "network_error"
    FLAKY_API_BEHAVIOR = "flaky_api_behavior"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMITING = "rate_limiting"
    SERVER_ERROR = "server_error"
    EXPECTED_ERROR = "expected_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorAnalysis:
    """Result of error analysis"""
    category: ErrorCategory
    is_retryable: bool
    confidence: float  # 0.0 to 1.0
    description: str
    suggested_action: str
    retry_delay: Optional[float] = None


class ErrorAnalyzer:
    """
    Analyzes errors from the deliberately flaky/unreliable Pet Store API
    Helps distinguish between expected errors and API flakiness
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_patterns = self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize patterns for different error categories"""
        return {
            ErrorCategory.NETWORK_ERROR: [
                "connection.*timeout", "connection.*refused", "network.*unreachable",
                "dns.*resolution", "socket.*error", "connection.*reset"
            ],
            ErrorCategory.FLAKY_API_BEHAVIOR: [
                "internal.*server.*error", "service.*unavailable", "bad.*gateway",
                "gateway.*timeout", "temporary.*unavailable", "502", "503", "504"
            ],
            ErrorCategory.RATE_LIMITING: [
                "rate.*limit", "too.*many.*requests", "429", "quota.*exceeded"
            ],
            ErrorCategory.AUTHENTICATION_ERROR: [
                "unauthorized", "forbidden", "invalid.*api.*key", "401", "403"
            ],
            ErrorCategory.VALIDATION_ERROR: [
                "bad.*request", "invalid.*input", "validation.*failed", "400"
            ]
        }

    def analyze_response_error(self, response: APIResponse, context: str = "") -> ErrorAnalysis:
        """
        Analyze an error response from the API

        Args:
            response: The failed API response
            context: Additional context about what operation failed

        Returns:
            ErrorAnalysis with categorization and recommendations
        """
        self.logger.debug("Analyzing error response", extra={
            "analysis_type": "response_error",
            "status_code": response.status_code,
            "context": context
        })

        # Quick categorization based on status code
        if response.status_code == APIConstants.HTTP_NOT_FOUND:
            return self._analyze_not_found_error(response, context)
        elif response.status_code == APIConstants.HTTP_BAD_REQUEST:
            return self._analyze_bad_request_error(response, context)
        elif response.status_code >= 500:
            return self._analyze_server_error(response, context)
        elif response.status_code == 429:
            return self._analyze_rate_limit_error(response, context)
        elif response.status_code in [401, 403]:
            return self._analyze_auth_error(response, context)
        else:
            return self._analyze_unknown_error(response, context)

    def analyze_exception(self, exception: Exception, context: str = "") -> ErrorAnalysis:
        """
        Analyze an exception that occurred during API operations

        Args:
            exception: The exception that was raised
            context: Additional context about what operation failed

        Returns:
            ErrorAnalysis with categorization and recommendations
        """
        self.logger.debug("Analyzing exception", extra={
            "analysis_type": "exception",
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context
        })

        exception_str = str(exception).lower()
        exception_type = type(exception).__name__

        # Network-related exceptions
        if any(keyword in exception_type.lower() for keyword in ['connection', 'timeout', 'network']):
            return ErrorAnalysis(
                category=ErrorCategory.NETWORK_ERROR,
                is_retryable=True,
                confidence=0.9,
                description=f"Network error: {exception_type}",
                suggested_action="Retry with exponential backoff",
                retry_delay=2.0
            )

        # Check exception message against patterns
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, exception_str, re.IGNORECASE):
                    return self._create_analysis_for_category(category, str(exception))

        # Unknown exception
        return ErrorAnalysis(
            category=ErrorCategory.UNKNOWN_ERROR,
            is_retryable=False,
            confidence=0.5,
            description=f"Unknown exception: {exception_type}: {str(exception)}",
            suggested_action="Investigate manually - unexpected error type"
        )

    def _analyze_not_found_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze 404 Not Found errors"""
        # For the flaky API, 404 might be legitimate or due to auto-cleanup
        if "get" in context.lower():
            description = "Pet not found - might be legitimate or auto-cleaned by flaky API"
            is_retryable = True  # Might retry in case of timing issues
            suggested_action = "Check if pet was auto-deleted by flaky API, minimal retry"
        else:
            description = "Resource not found"
            is_retryable = False
            suggested_action = "Verify resource exists before operation"

        self.logger.info("Analyzed 404 error", extra={
            "analysis_type": "not_found_error",
            "status": LoggingConstants.STATUS_WARNING,
            "is_retryable": is_retryable,
            "context": context
        })

        return ErrorAnalysis(
            category=ErrorCategory.EXPECTED_ERROR,
            is_retryable=is_retryable,
            confidence=0.8,
            description=description,
            suggested_action=suggested_action,
            retry_delay=1.0 if is_retryable else None
        )

    def _analyze_bad_request_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze 400 Bad Request errors"""
        try:
            error_details = response.json()
            error_message = error_details.get('message', 'No details provided')
        except:
            error_message = response.text

        return ErrorAnalysis(
            category=ErrorCategory.VALIDATION_ERROR,
            is_retryable=False,
            confidence=0.9,
            description=f"Validation error: {error_message}",
            suggested_action="Fix request data format/content"
        )

    def _analyze_server_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze 5xx server errors"""
        # For the flaky API, server errors are common and should be retried
        self.logger.warning("Server error detected - typical flaky API behavior", extra={
            "analysis_type": "server_error",
            "status": LoggingConstants.STATUS_WARNING,
            "status_code": response.status_code,
            "context": context,
            "is_expected": True
        })

        return ErrorAnalysis(
            category=ErrorCategory.FLAKY_API_BEHAVIOR,
            is_retryable=True,
            confidence=0.95,
            description=f"Server error {response.status_code} - typical flaky API behavior",
            suggested_action="Retry with exponential backoff - this is expected from flaky API",
            retry_delay=1.5
        )

    def _analyze_rate_limit_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze rate limiting errors"""
        # Extract retry-after header if present
        retry_after = response.headers.get('retry-after', '60')
        try:
            retry_delay = float(retry_after)
        except:
            retry_delay = 60.0

        return ErrorAnalysis(
            category=ErrorCategory.RATE_LIMITING,
            is_retryable=True,
            confidence=1.0,
            description="Rate limit exceeded",
            suggested_action=f"Wait {retry_delay} seconds before retry",
            retry_delay=retry_delay
        )

    def _analyze_auth_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze authentication/authorization errors"""
        return ErrorAnalysis(
            category=ErrorCategory.AUTHENTICATION_ERROR,
            is_retryable=False,
            confidence=0.95,
            description=f"Authentication error {response.status_code}",
            suggested_action="Check API key configuration"
        )

    def _analyze_unknown_error(self, response: APIResponse, context: str) -> ErrorAnalysis:
        """Analyze unknown/unexpected errors"""
        return ErrorAnalysis(
            category=ErrorCategory.UNKNOWN_ERROR,
            is_retryable=True,  # For flaky API, try once more
            confidence=0.3,
            description=f"Unknown error with status {response.status_code}",
            suggested_action="Log details and retry once - might be flaky API",
            retry_delay=2.0
        )

    def _create_analysis_for_category(self, category: ErrorCategory, description: str) -> ErrorAnalysis:
        """Create ErrorAnalysis for a specific category"""
        category_configs = {
            ErrorCategory.NETWORK_ERROR: {
                "is_retryable": True,
                "confidence": 0.9,
                "suggested_action": "Retry with exponential backoff",
                "retry_delay": 2.0
            },
            ErrorCategory.FLAKY_API_BEHAVIOR: {
                "is_retryable": True,
                "confidence": 0.95,
                "suggested_action": "Retry - expected flaky API behavior",
                "retry_delay": 1.5
            },
            ErrorCategory.RATE_LIMITING: {
                "is_retryable": True,
                "confidence": 1.0,
                "suggested_action": "Wait before retry",
                "retry_delay": 60.0
            },
            ErrorCategory.AUTHENTICATION_ERROR: {
                "is_retryable": False,
                "confidence": 0.9,
                "suggested_action": "Fix authentication",
                "retry_delay": None
            },
            ErrorCategory.VALIDATION_ERROR: {
                "is_retryable": False,
                "confidence": 0.9,
                "suggested_action": "Fix request data",
                "retry_delay": None
            }
        }

        config = category_configs.get(category, {
            "is_retryable": False,
            "confidence": 0.5,
            "suggested_action": "Manual investigation required",
            "retry_delay": None
        })

        return ErrorAnalysis(
            category=category,
            description=description,
            **config
        )

    def should_retry_operation(self, analysis: ErrorAnalysis, attempt_number: int, max_attempts: int) -> Tuple[bool, float]:
        """
        Determine if operation should be retried based on error analysis

        Returns:
            (should_retry, delay_seconds)
        """
        if attempt_number >= max_attempts:
            return False, 0.0

        if not analysis.is_retryable:
            return False, 0.0

        # For flaky API behavior, be more aggressive with retries
        if analysis.category == ErrorCategory.FLAKY_API_BEHAVIOR:
            delay = min(analysis.retry_delay or 1.0, 5.0)  # Cap at 5 seconds
            return True, delay

        # For network errors, use exponential backoff
        if analysis.category == ErrorCategory.NETWORK_ERROR:
            delay = min((analysis.retry_delay or 2.0) * (2 ** (attempt_number - 1)), 30.0)
            return True, delay

        # For rate limiting, respect the suggested delay
        if analysis.category == ErrorCategory.RATE_LIMITING:
            return True, analysis.retry_delay or 60.0

        # Default case
        return analysis.is_retryable, analysis.retry_delay or 1.0

    def get_error_summary(self, error_analyses: List[ErrorAnalysis]) -> Dict[str, Any]:
        """
        Generate summary statistics from multiple error analyses
        Useful for understanding patterns in flaky API behavior
        """
        if not error_analyses:
            return {"total_errors": 0}

        category_counts = {}
        retryable_count = 0
        total_confidence = 0.0

        for analysis in error_analyses:
            category = analysis.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            if analysis.is_retryable:
                retryable_count += 1
            total_confidence += analysis.confidence

        return {
            "total_errors": len(error_analyses),
            "category_breakdown": category_counts,
            "retryable_errors": retryable_count,
            "retry_rate": (retryable_count / len(error_analyses)) * 100,
            "average_confidence": total_confidence / len(error_analyses),
            "most_common_category": max(category_counts, key=category_counts.get) if category_counts else None
        }