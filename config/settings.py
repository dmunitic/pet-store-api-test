"""
Configuration settings for Pet Store API Test Framework
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    BASE_URL: str = "https://petstore.swagger.io/v2"
    API_KEY: str = "test_api_key"
    TIMEOUT: int = 30

    # Test Configuration
    TEST_DATA_PATH: str = "tests/test_data"
    REPORTS_PATH: str = "reports"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "test_execution.log"

    # Environment
    ENVIRONMENT: str = "test"

    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()


class APIEndpoints:
    """API endpoint paths"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    @property
    def pets(self) -> str:
        return f"{self.base_url}/pet"

    def pet_by_id(self, pet_id: int) -> str:
        return f"{self.base_url}/pet/{pet_id}"


# Global endpoints instance
endpoints = APIEndpoints(settings.BASE_URL)