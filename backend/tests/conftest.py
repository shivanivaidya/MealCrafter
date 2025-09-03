"""
Pytest configuration and fixtures for testing
"""
import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from main import app
from app.models.user import User
from app.models.recipe import Recipe
from app.core.security import get_password_hash, create_access_token


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create an authentication token for the test user."""
    access_token = create_access_token(data={"sub": test_user.username})
    return access_token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with the test user's token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_recipe_data() -> dict:
    """Sample recipe data for testing."""
    return {
        "title": "Test Recipe",
        "raw_text": """
        Test Recipe
        
        Ingredients:
        - 2 cups flour
        - 1 cup water
        - 1 tsp salt
        
        Instructions:
        1. Mix all ingredients
        2. Knead the dough
        3. Let it rest for 30 minutes
        4. Cook as desired
        """,
        "cuisine_type": "Italian",
        "dietary_tags": ["Vegan", "Low-Fat"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 4
    }


@pytest.fixture
def sample_recipe(db: Session, test_user: User) -> Recipe:
    """Create a sample recipe in the database."""
    recipe = Recipe(
        user_id=test_user.id,
        title="Sample Recipe",
        raw_text="Sample recipe text",
        ingredients=[
            {"name": "flour", "quantity": "2", "unit": "cups"},
            {"name": "water", "quantity": "1", "unit": "cup"}
        ],
        instructions=["Mix ingredients", "Cook"],
        calories=200,
        health_rating=7.5,
        health_breakdown="Healthy recipe",
        servings=4,
        nutrition_data={
            "per_serving": {
                "calories": 200,
                "protein": 10,
                "carbs": 30,
                "fat": 5
            },
            "total": {
                "calories": 800,
                "protein": 40,
                "carbs": 120,
                "fat": 20
            }
        }
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@pytest.fixture
def mock_openai_response(mocker):
    """Mock OpenAI API responses for testing."""
    def _mock_response(content: str):
        mock = mocker.Mock()
        mock.choices = [mocker.Mock()]
        mock.choices[0].message.content = content
        return mock
    return _mock_response


# Environment variable fixtures
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["GPT_MODEL"] = "gpt-3.5-turbo"
    yield
    # Cleanup after test if needed