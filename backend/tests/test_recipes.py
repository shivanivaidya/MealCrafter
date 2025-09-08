"""
Tests for recipe CRUD operations
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.recipe import Recipe
from app.models.user import User


class TestRecipeCreate:
    """Test recipe creation endpoint"""
    
    @patch('app.routers.recipes.AIRecipeParser')
    @patch('app.routers.recipes.AINutritionCalculator')
    @patch('app.routers.recipes.AIHealthAnalyzer')
    def test_create_recipe_success(
        self,
        mock_health,
        mock_nutrition,
        mock_parser,
        client: TestClient,
        auth_headers: dict,
        sample_recipe_data: dict
    ):
        """Test successful recipe creation"""
        # Mock AI services
        mock_parser_instance = Mock()
        mock_parser_instance.parse_recipe_text.return_value = Mock(
            title="Test Recipe",
            ingredients=[
                {"name": "flour", "quantity": "2", "unit": "cups"},
                {"name": "water", "quantity": "1", "unit": "cup"},
                {"name": "salt", "quantity": "1", "unit": "tsp"}
            ],
            instructions=["Mix ingredients", "Knead dough", "Rest", "Cook"],
            servings=4,
            cuisine_type="Italian",
            dietary_tags=["Vegan"]
        )
        mock_parser.return_value = mock_parser_instance
        
        mock_nutrition_instance = Mock()
        mock_nutrition_instance.calculate_nutrition.return_value = {
            "per_serving": {"calories": 200, "protein": 5, "carbs": 40, "fat": 2},
            "total": {"calories": 800, "protein": 20, "carbs": 160, "fat": 8},
            "servings": 4
        }
        mock_nutrition.return_value = mock_nutrition_instance
        
        mock_health_instance = Mock()
        mock_health_instance.analyze_health.return_value = {
            "score": 7.5,
            "breakdown": "Healthy recipe with good nutritional balance"
        }
        mock_health.return_value = mock_health_instance
        
        response = client.post(
            "/api/recipes/",
            json=sample_recipe_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Recipe"
        assert len(data["ingredients"]) == 3
        assert len(data["instructions"]) == 4
        assert data["calories"] == 200
        assert data["health_rating"] == 7.5
        assert "id" in data
    
    def test_create_recipe_unauthorized(self, client: TestClient, sample_recipe_data: dict):
        """Test recipe creation without authentication"""
        response = client.post("/api/recipes/", json=sample_recipe_data)
        assert response.status_code == 401
    
    @patch('app.routers.recipes.AIRecipeParser')
    def test_create_recipe_invalid_text(
        self,
        mock_parser,
        client: TestClient,
        auth_headers: dict
    ):
        """Test recipe creation with invalid text"""
        mock_parser_instance = Mock()
        mock_parser_instance.parse_recipe_text.side_effect = ValueError("Invalid recipe text")
        mock_parser.return_value = mock_parser_instance
        
        response = client.post(
            "/api/recipes/",
            json={"title": "Bad Recipe", "raw_text": "invalid"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Pydantic validation error


class TestRecipeRead:
    """Test recipe reading endpoints"""
    
    def test_get_recipe_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_recipe: Recipe
    ):
        """Test getting a recipe by ID"""
        response = client.get(
            f"/api/recipes/{sample_recipe.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_recipe.id
        assert data["title"] == sample_recipe.title
    
    def test_get_recipe_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent recipe"""
        response = client.get("/api/recipes/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_recipe_unauthorized(
        self,
        client: TestClient,
        sample_recipe: Recipe
    ):
        """Test getting recipe without authentication"""
        response = client.get(f"/api/recipes/{sample_recipe.id}")
        assert response.status_code == 401
    
    def test_list_recipes(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_recipe: Recipe,
        db: Session,
        test_user: User
    ):
        """Test listing user's recipes"""
        # Create another recipe
        recipe2 = Recipe(
            user_id=test_user.id,
            title="Another Recipe",
            raw_text="Another recipe text",
            ingredients=[{"name": "sugar", "quantity": "1", "unit": "cup"}],
            instructions=["Mix", "Bake"],
            calories=300,
            servings=2
        )
        db.add(recipe2)
        db.commit()
        
        response = client.get("/api/recipes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = [r["title"] for r in data]
        assert "Sample Recipe" in titles
        assert "Another Recipe" in titles
    
    def test_list_recipes_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User
    ):
        """Test recipe listing with pagination"""
        # Create multiple recipes
        for i in range(25):
            recipe = Recipe(
                user_id=test_user.id,
                title=f"Recipe {i}",
                raw_text=f"Recipe {i} text",
                ingredients=[],
                instructions=[],
                servings=1
            )
            db.add(recipe)
        db.commit()
        
        # Test default pagination (20 items)
        response = client.get("/api/recipes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 20
        
        # Test with skip and limit
        response = client.get("/api/recipes/?skip=20&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Only 5 recipes left


class TestRecipeUpdate:
    """Test recipe update operations"""
    
    def test_update_recipe_rating(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_recipe: Recipe
    ):
        """Test updating recipe taste rating"""
        response = client.patch(
            f"/api/recipes/{sample_recipe.id}/rating",
            json={"taste_rating": 4.5},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["taste_rating"] == 4.5
    
    def test_update_recipe_rating_invalid(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_recipe: Recipe
    ):
        """Test updating recipe with invalid rating"""
        response = client.patch(
            f"/api/recipes/{sample_recipe.id}/rating",
            json={"taste_rating": 6},  # Rating must be 1-5
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_update_recipe_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test updating non-existent recipe"""
        response = client.patch(
            "/api/recipes/99999/rating",
            json={"taste_rating": 3},
            headers=auth_headers
        )
        assert response.status_code == 404


class TestRecipeDelete:
    """Test recipe deletion"""
    
    def test_delete_recipe(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_recipe: Recipe,
        db: Session
    ):
        """Test deleting a recipe"""
        recipe_id = sample_recipe.id
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Recipe deleted successfully"
        
        # Verify recipe was deleted
        deleted_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert deleted_recipe is None
    
    def test_delete_recipe_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent recipe"""
        response = client.delete("/api/recipes/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_recipe_unauthorized(
        self,
        client: TestClient,
        sample_recipe: Recipe
    ):
        """Test deleting recipe without authentication"""
        response = client.delete(f"/api/recipes/{sample_recipe.id}")
        assert response.status_code == 401


class TestRecipeOwnership:
    """Test that users can only access their own recipes"""
    
    def test_cannot_access_other_user_recipe(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session
    ):
        """Test that user cannot access another user's recipe"""
        # Create another user and their recipe
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed"
        )
        db.add(other_user)
        db.commit()
        
        other_recipe = Recipe(
            user_id=other_user.id,
            title="Other's Recipe",
            raw_text="Other recipe",
            ingredients=[],
            instructions=[],
            servings=1
        )
        db.add(other_recipe)
        db.commit()
        
        # Try to access with first user's token
        response = client.get(
            f"/api/recipes/{other_recipe.id}",
            headers=auth_headers
        )
        assert response.status_code == 404  # Should not find the recipe
    
    def test_cannot_delete_other_user_recipe(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session
    ):
        """Test that user cannot delete another user's recipe"""
        # Create another user and their recipe
        other_user = User(
            username="otheruser2",
            email="other2@example.com",
            hashed_password="hashed"
        )
        db.add(other_user)
        db.commit()
        
        other_recipe = Recipe(
            user_id=other_user.id,
            title="Other's Recipe",
            raw_text="Other recipe",
            ingredients=[],
            instructions=[],
            servings=1
        )
        db.add(other_recipe)
        db.commit()
        
        # Try to delete with first user's token
        response = client.delete(
            f"/api/recipes/{other_recipe.id}",
            headers=auth_headers
        )
        assert response.status_code == 404  # Should not find the recipe
        
        # Verify recipe still exists
        recipe = db.query(Recipe).filter(Recipe.id == other_recipe.id).first()
        assert recipe is not None