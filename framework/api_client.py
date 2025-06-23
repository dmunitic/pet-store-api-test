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
    """HTTP client for Pet Store API with built-in retry, logging, and validation"""

    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = None):
        self.base_url = base_url or settings.BASE_URL
        self.api_key = api_key or settings.API_KEY
        self.timeout = timeout or settings.TIMEOUT

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
            total=3,
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
        if response.status_code == 200:
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

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    # Pet API Methods

    def create_pet(self, pet_data: Dict[str, Any]) -> APIResponse:
        """Create a new pet"""
        return self._make_request(
            method="POST",
            url=endpoints.pets,
            json=pet_data
        )

    def get_pet_by_id(self, pet_id: int) -> APIResponse:
        """Get pet by ID"""
        return self._make_request(
            method="GET",
            url=endpoints.pet_by_id(pet_id)
        )

    def update_pet(self, pet_data: Dict[str, Any]) -> APIResponse:
        """Update an existing pet"""
        return self._make_request(
            method="PUT",
            url=endpoints.pets,
            json=pet_data
        )

    def delete_pet(self, pet_id: int) -> APIResponse:
        """Delete a pet by ID"""
        return self._make_request(
            method="DELETE",
            url=endpoints.pet_by_id(pet_id)
        )

    # Utility methods

    def health_check(self) -> bool:
        """Simple health check by making a basic request"""
        try:
            response = self.get_pet_by_id(1)  # Try to get any pet
            return True  # Any response (even 404) means API is reachable
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
            self.logger.info("API client session closed")