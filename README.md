# Pet Store API Test Automation Framework

> **Assignment Objective**: Design and implement a Test Automation Framework (TAF) to validate key API endpoints of the "Pet Online Store" Back-End application.

## Assignment Requirements

This framework tests the three required API endpoints:
- **POST /pet** - Add a new pet
- **GET /pet/{petId}** - Retrieve pet details by ID  
- **PUT /pet** - Update an existing pet

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run all core assignment tests
python run_tests.py full

# Run specific test types
python run_tests.py positive    # Happy path scenarios
python run_tests.py negative    # Error handling
python run_tests.py stability   # API reliability analysis
```

## Project Structure

```
pet-store-api-test/
├── framework/
│   ├── api_client.py      # HTTP client with retry logic
│   └── base_test.py       # Test base class with utilities
├── config/
│   └── settings.py        # Configuration management
├── tests/
│   ├── test_pet_api.py                    
│   ├── test_api_connection.py             # Framework validation
│   └── conftest.py                        # Test configuration
├── reports/               # Test summary reports
├── run_tests.py          # Enhanced test runner
├── pytest.ini           # Test configuration
└── requirements.txt      # Dependencies
```

## Core Tests (Assignment Requirements)

**File**: `tests/test_pet_api.py`

These tests fulfill the assignment requirements:
- Complete pet lifecycle workflow (POST → GET → PUT → GET)
- Individual endpoint testing
- Basic positive and negative scenarios
- Retry logic for demo API reliability
- API key authentication
- Proper error handling

```bash
# Run just the core assignment tests
python run_tests.py single tests/test_pet_api.py
```

## Key Framework Features

### **Retry Logic**
Handles the unreliable demo API with intelligent retry mechanisms:
- Configurable retry attempts
- Exponential backoff
- Stability metrics and reporting

### **Professional Logging**
- Timestamped log files with all HTTP details
- Human-readable summary reports
- Request/response body logging
- Stability analysis

### **Test Organization**
- pytest markers for test categorization
- Positive/negative test separation
- Comprehensive fixture management
- Automatic test data cleanup

## Reports

After running tests, check:
- **Detailed logs**: `tests/logs/test_run_YYYYMMDD_HHMMSS.log`
- **Summary reports**: `reports/test_summary_YYYYMMDD_HHMMSS.txt`

## Framework Architecture

### **API Client** (`framework/api_client.py`)
- HTTP session management with retry strategies
- API key authentication
- Response wrapper with utilities
- Comprehensive request/response logging

### **Base Test Class** (`framework/base_test.py`)
- Retry logic with stability tracking
- Test data cleanup management
- Advanced assertion methods
- Statistics collection and reporting

### **Configuration** (`config/settings.py`)
- Environment-based configuration
- Secure API key management
- Endpoint URL management

## Assignment Compliance

This framework meets all assignment requirements:
- **Scalable TAF architecture**
- **All three required endpoints tested**
- **Independent test case design** (no manual QA dependency)
- **Git version control ready**
- **Swagger Petstore API integration**
- **API key authentication** (test_api_key header)
- **Python 3.12+ and pytest**
- **Best practices in test automation**

## Bonus Achievements

Going beyond requirements:
- **Intelligent retry logic** for unreliable APIs
- **Stability metrics** and analysis
- **Comprehensive edge case coverage**
- **Security testing capabilities**
- **Professional reporting**
- **Multiple execution modes**

---

**Tech Stack**: Python 3.12+, pytest, requests, pydantic  
**API Documentation**: [Swagger Petstore](https://petstore.swagger.io/)