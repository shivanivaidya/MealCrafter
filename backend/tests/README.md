# MealCrafter Backend Tests

This directory contains the test suite for the MealCrafter backend API.

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_auth.py` - Authentication endpoint tests
- `test_recipes.py` - Recipe CRUD operation tests
- `test_url_scraper.py` - URL recipe scraping tests
- `test_ai_services.py` - AI service tests (parser, nutrition, health)

## Running Tests

### Basic Test Run
```bash
# From the backend directory
pytest tests/
```

### With Coverage Report
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Verbose Output
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_auth.py
```

### Run Specific Test Class or Method
```bash
pytest tests/test_auth.py::TestAuthentication
pytest tests/test_auth.py::TestAuthentication::test_register_success
```

### Using the Test Runner Script
```bash
./run_tests.sh           # Run all tests
./run_tests.sh coverage  # With coverage report
./run_tests.sh verbose   # Verbose mode
./run_tests.sh unit      # Unit tests only
```

## Test Coverage

Current test coverage: ~39%

Key areas covered:
- ✅ User registration and authentication
- ✅ Recipe creation, reading, updating, deletion
- ✅ Recipe ownership validation
- ✅ URL recipe scraping
- ✅ AI service mocking and integration
- ✅ Input validation
- ✅ Error handling

## Writing New Tests

### Test Fixtures

Common fixtures available in `conftest.py`:
- `client` - FastAPI test client
- `db` - Test database session
- `test_user` - Pre-created test user
- `auth_token` - Authentication token for test user
- `auth_headers` - Authorization headers with token
- `sample_recipe` - Pre-created recipe
- `sample_recipe_data` - Sample recipe creation data

### Example Test
```python
def test_create_recipe(client, auth_headers, sample_recipe_data):
    response = client.post(
        "/api/recipes/",
        json=sample_recipe_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == sample_recipe_data["title"]
```

## Continuous Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request

See `.github/workflows/test.yml` for CI configuration.

## Environment Variables

Tests require these environment variables:
- `SECRET_KEY` - JWT secret key
- `DATABASE_URL` - Database connection (uses SQLite in-memory for tests)
- `OPENAI_API_KEY` - OpenAI API key (can be mocked)
- `GPT_MODEL` - GPT model to use