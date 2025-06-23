"""
API Client for Pet Store API Test Framework
"""
import json
import logging
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings, endpoints
from framework.constants import APIConstants, ErrorMessages
from framework.exceptions import (
    APIConnectionError, InvalidPetIdError, PetNotFoundError,
    PetCreationError, PetUpdateError, validate_pet_id, validate_pet_data
)


class APIResponse:
    """Wrapper for HTTP response with additional utilities"""

    def __init__(self, response: requests.Response):
        self._response = response
        self.status_code = response.status_code
        self.text = response.text
        self.headers = response.headers
        self.url = response.url

    def json(self):
        """Parse response as JSON"""
        return self._response.json()

    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status code)"""
        return 200 <= self.status_code < 300

    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error (4xx status code)"""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error (5xx status code)"""
        return 500 <= self.status_code < 600

    def get_json_value(self, key: str, default: Any = None) -> Any:
        """Safely get value from JSON response"""
        if hasattr(self, '_json_data') and self._json_data and isinstance(self._json_data, dict):
            return self._json_data.get(key, default)
        return default


class PetStoreAPIClient:
    """
    HTTP client for Pet Store API with built-in retry, logging, and validation
    """

    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = None):
        self.base_url = base_url or settings.BASE_URL
        self.api_key = api_key or settings.API_KEY
        self.timeout = timeout or APIConstants.DEFAULT_TIMEOUT

        # Setup standard Python logger
        self.logger = logging.getLogger('framework.api_client')

        # Setup session with retry strategy
        self.session = self._create_session()

        # Default headers
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "api_key": self.api_key
        }

        self.logger.info(f"Initialized API client for {self.base_url}")

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=APIConstants.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _log_request(self, method: str, url: str, **kwargs):
        """Log request details"""
        self.logger.info(f"Making {method} request to {url}")
        if 'json' in kwargs:
            self.logger.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")

    def _log_response(self, response: APIResponse):
        """Log response details"""
        self.logger.info(f"Response: {response.status_code} from {response.url}")
        if response.status_code == APIConstants.HTTP_OK:
            try:
                json_data = response.json()
                if json_data:
                    self.logger.debug(f"Response body: {json.dumps(json_data, indent=2)}")
            except (ValueError, requests.exceptions.JSONDecodeError):
                self.logger.debug(f"Response text: {response.text}")
        elif response.text:
            self.logger.debug(f"Response text: {response.text}")

    def _make_request(
            self,
            method: str,
            url: str,
            headers: Dict[str, str] = None,
            **kwargs
    ) -> APIResponse:
        """Make HTTP request with logging and error handling"""

        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        # Log request
        self._log_request(method, url, **kwargs)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                timeout=self.timeout,
                **kwargs
            )

            api_response = APIResponse(response)
            self._log_response(api_response)

            return api_response

        except requests.exceptions.ConnectionError as e:
            # Specific exception handling
            error_msg = ErrorMessages.API_CONNECTION_FAILED
            self.logger.error(error_msg)
            raise APIConnectionError(url, e)

        except requests.exceptions.Timeout as e:
            # Specific exception handling
            self.logger.error(f"Request timeout after {self.timeout}s")
            raise APIConnectionError(url, e)

        except requests.exceptions.RequestException as e:
            # More specific than broad Exception
            self.logger.error(f"Request failed: {str(e)}")
            raise APIConnectionError(url, e)

    # Pet API Methods with validation and proper error handling

    def create_pet(self, pet_data: Dict[str, Any]) -> APIResponse:
        """
        Create a new pet
        """
        # Input validation using custom validator
        try:
            validate_pet_data(pet_data)
        except Exception as e:
            raise PetCreationError(pet_data, 0, f"Validation failed: {str(e)}")

        try:
            response = self._make_request(
                method="POST",
                url=endpoints.pets,
                json=pet_data
            )

            # Check for creation errors
            if response.status_code >= APIConstants.HTTP_BAD_REQUEST:
                raise PetCreationError(
                    pet_data,
                    response.status_code,
                    response.text
                )

            return response

        except APIConnectionError:
            # Re-raise connection errors as-is
            raise
        except Exception as e:
            # Convert other errors to PetCreationError
            raise PetCreationError(pet_data, 0, str(e))

    def get_pet_by_id(self, pet_id: Union[int, str]) -> APIResponse:
        """
        Get pet by ID
        """
        # Input validation using custom validator
        try:
            validated_id = validate_pet_id(pet_id)
        except InvalidPetIdError:
            # Re-raise validation errors as-is
            raise

        try:
            response = self._make_request(
                method="GET",
                url=endpoints.pet_by_id(validated_id)
            )

            # Handle specific error cases
            if response.status_code == APIConstants.HTTP_NOT_FOUND:
                raise PetNotFoundError(validated_id)

            return response

        except APIConnectionError:
            # Re-raise connection errors as-is
            raise
        except PetNotFoundError:
            # Re-raise pet not found errors as-is
            raise

    def update_pet(self, pet_data: Dict[str, Any]) -> APIResponse:
        """
        Update an existing pet
        """
        # Input validation
        try:
            validate_pet_data(pet_data)
        except Exception as e:
            pet_id = pet_data.get('id', 'unknown')
            raise PetUpdateError(pet_id, pet_data, status_code=0)

        pet_id = pet_data['id']  # Safe because validate_pet_data checks this

        try:
            response = self._make_request(
                method="PUT",
                url=endpoints.pets,
                json=pet_data
            )

            # Check for update errors
            if response.status_code == APIConstants.HTTP_NOT_FOUND:
                raise PetNotFoundError(pet_id, f"Cannot update non-existent pet {pet_id}")
            elif response.status_code >= APIConstants.HTTP_BAD_REQUEST:
                raise PetUpdateError(
                    pet_id,
                    pet_data,
                    status_code=response.status_code
                )

            return response

        except (APIConnectionError, PetNotFoundError):
            # Re-raise specific errors as-is
            raise
        except Exception as e:
            # Convert other errors to PetUpdateError
            raise PetUpdateError(pet_id, pet_data, status_code=0)

    def delete_pet(self, pet_id: Union[int, str]) -> APIResponse:
        """
        Delete a pet by ID
        """
        # Input validation
        try:
            validated_id = validate_pet_id(pet_id)
        except InvalidPetIdError:
            # Re-raise validation errors as-is
            raise

        try:
            response = self._make_request(
                method="DELETE",
                url=endpoints.pet_by_id(validated_id)
            )

            # Handle specific error cases
            if response.status_code == APIConstants.HTTP_NOT_FOUND:
                raise PetNotFoundError(validated_id)

            return response

        except (APIConnectionError, PetNotFoundError):
            # Re-raise specific errors as-is
            raise

    # Utility methods

    def health_check(self) -> bool:
        """
        Simple health check by making a basic request
        """
        try:
            # Use a constant for the test pet ID
            response = self.get_pet_by_id(1)
            return True  # Any response (even 404) means API is reachable
        except PetNotFoundError:
            # 404 is actually a successful connection
            return True
        except APIConnectionError as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Health check failed with unexpected error: {str(e)}")
            return False

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
            self.logger.info("API client session closed")
