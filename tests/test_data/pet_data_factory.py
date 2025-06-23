"""
Test data factory for generating pet data for tests.
Centralizes all test data generation logic.

NOTE: No __init__.py in tests/test_data/ to avoid pytest conflicts.
Import directly: from tests.test_data.pet_data_factory import PetDataFactory
"""
import random
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


class PetDataFactory:
    """Factory for generating pet test data"""

    # Constants for test data
    VALID_STATUSES = ["available", "pending", "sold"]
    INVALID_STATUSES = ["invalid_status", "unknown", "deleted"]

    SAMPLE_CATEGORIES = [
        {"id": 1, "name": "Dogs"},
        {"id": 2, "name": "Cats"},
        {"id": 3, "name": "Birds"},
        {"id": 4, "name": "Fish"},
        {"id": 5, "name": "Reptiles"}
    ]

    SAMPLE_TAGS = [
        {"id": 1, "name": "friendly"},
        {"id": 2, "name": "energetic"},
        {"id": 3, "name": "calm"},
        {"id": 4, "name": "trained"},
        {"id": 5, "name": "young"},
        {"id": 6, "name": "adult"},
        {"id": 7, "name": "senior"}
    ]

    @classmethod
    def generate_pet_id(cls) -> int:
        """Generate a unique pet ID for testing"""
        return random.randint(1000000, 9999999)

    @classmethod
    def create_basic_pet(cls, pet_id: int = None, name: str = None, status: str = "available") -> Dict[str, Any]:
        """Create basic pet data with minimal required fields"""
        return {
            "id": pet_id or cls.generate_pet_id(),
            "name": name or fake.first_name(),
            "photoUrls": [fake.image_url()],
            "status": status
        }

    @classmethod
    def create_complete_pet(cls, pet_id: int = None, **overrides) -> Dict[str, Any]:
        """Create complete pet data with all fields"""
        category = random.choice(cls.SAMPLE_CATEGORIES)
        tags = random.sample(cls.SAMPLE_TAGS, k=random.randint(1, 3))

        pet_data = {
            "id": pet_id or cls.generate_pet_id(),
            "name": fake.first_name(),
            "category": category,
            "photoUrls": [fake.image_url() for _ in range(random.randint(1, 3))],
            "tags": tags,
            "status": random.choice(cls.VALID_STATUSES)
        }

        # Apply any overrides
        pet_data.update(overrides)
        return pet_data

    @classmethod
    def create_updated_pet(cls, original_pet: Dict[str, Any]) -> Dict[str, Any]:
        """Create updated version of existing pet"""
        updated = original_pet.copy()
        updated.update({
            "name": f"Updated {original_pet.get('name', 'Pet')}",
            "status": "sold" if original_pet.get("status") == "available" else "available",
            "photoUrls": original_pet.get("photoUrls", []) + [fake.image_url()]
        })

        # Add an additional tag if tags exist
        if "tags" in updated:
            new_tag = {"id": 99, "name": "updated"}
            if new_tag not in updated["tags"]:
                updated["tags"].append(new_tag)

        return updated

    @classmethod
    def create_invalid_pets(cls) -> List[Dict[str, Any]]:
        """Create various invalid pet data for negative testing"""
        return [
            # Missing required fields
            {"name": "Pet Missing ID", "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "name": "Pet Missing PhotoUrls", "status": "available"},
            {"id": cls.generate_pet_id(), "name": "Pet Missing Status", "photoUrls": []},

            # Invalid data types
            {"id": "not_a_number", "name": "Invalid ID Type", "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "name": 12345, "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "name": "Invalid PhotoUrls", "photoUrls": "not_array", "status": "available"},
            {"id": cls.generate_pet_id(), "name": "Invalid Status Type", "photoUrls": [], "status": 123},

            # Boundary values
            {"id": cls.generate_pet_id(), "name": "", "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "name": "x" * 1000, "photoUrls": [], "status": "available"},
            {"id": cls.generate_pet_id(), "name": "Invalid Status", "photoUrls": [], "status": "invalid_status"},

            # Edge cases
            {"id": -1, "name": "Negative ID", "photoUrls": [], "status": "available"},
            {"id": 0, "name": "Zero ID", "photoUrls": [], "status": "available"},
            {"id": None, "name": "Null ID", "photoUrls": [], "status": "available"},
        ]

    @classmethod
    def create_boundary_test_data(cls) -> Dict[str, Dict[str, Any]]:
        """Create boundary test cases"""
        base_id = cls.generate_pet_id()
        return {
            "empty_name": cls.create_basic_pet(base_id + 1, name=""),
            "long_name": cls.create_basic_pet(base_id + 2, name="x" * 1000),
            "special_chars_name": cls.create_basic_pet(base_id + 3, name="Pet!@#$%^&*()"),
            "unicode_name": cls.create_basic_pet(base_id + 4, name="Питомец 🐕"),
            "invalid_status": cls.create_basic_pet(base_id + 5, status="invalid_status"),
            "empty_photo_urls": cls.create_complete_pet(base_id + 6, photoUrls=[]),
            "many_photo_urls": cls.create_complete_pet(base_id + 7, photoUrls=[fake.image_url() for _ in range(50)]),
        }


class SecurityTestData:
    """Test data for security-related tests"""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "';DROP TABLE pets;--"
    ]

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE pets; --",
        "1' OR '1'='1",
        "admin'--",
        "admin'/*"
    ]

    @classmethod
    def create_security_test_pets(cls) -> List[Dict[str, Any]]:
        """Create pets with security test payloads"""
        pets = []
        base_id = PetDataFactory.generate_pet_id()

        for i, payload in enumerate(cls.XSS_PAYLOADS + cls.SQL_INJECTION_PAYLOADS):
            pets.append({
                "id": base_id + i,
                "name": payload,
                "photoUrls": [f"https://evil.com/{payload}"],
                "status": "available"
            })

        return pets


class PerformanceTestData:
    """Test data for performance testing"""

    @classmethod
    def create_large_pet(cls) -> Dict[str, Any]:
        """Create pet with large data payload"""
        return {
            "id": PetDataFactory.generate_pet_id(),
            "name": "Large Pet Data Test",
            "photoUrls": [fake.image_url() for _ in range(100)],
            "status": "available",
            "category": {"id": 1, "name": "Performance Test Category"},
            "tags": [{"id": i, "name": f"tag_{i}"} for i in range(50)]
        }

    @classmethod
    def create_batch_pets(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Create batch of pets for performance testing"""
        return [PetDataFactory.create_complete_pet() for _ in range(count)]