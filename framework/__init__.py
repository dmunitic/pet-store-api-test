"""
Pet Store API Test Framework

A comprehensive test automation framework for the Pet Store API.
Provides API client, base test classes, and testing utilities.
"""

from .api_client import PetStoreAPIClient, APIResponse
from .base_test import BaseTest, EnhancedAPITestSuite

__version__ = "1.0.0"
__all__ = [
    'PetStoreAPIClient',
    'APIResponse',
    'BaseTest',
    'EnhancedAPITestSuite'
]