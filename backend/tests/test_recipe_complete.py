"""
Comprehensive tests for recipe creation, including text, URL, and image uploads
"""
import json
import base64
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image
from fastapi import UploadFile


class TestRecipeCreation:
    """Test recipe creation from various sources"""
    
    def test_create_recipe_from_text(self, client, auth_headers, mocker):
        """Test creating a recipe from plain text"""
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Pasta Carbonara",
            ingredients=[
                {"name": "spaghetti", "quantity": "400", "unit": "g"},
                {"name": "eggs", "quantity": "4", "unit": ""},
                {"name": "parmesan cheese", "quantity": "100", "unit": "g"},
                {"name": "bacon", "quantity": "200", "unit": "g"}
            ],
            instructions=[
                "Cook spaghetti according to package directions",
                "Fry bacon until crispy",
                "Mix eggs and cheese",
                "Combine all ingredients"
            ],
            servings=4,
            cuisine_type="Italian",
            dietary_tags=[]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 450, "protein": 20, "carbs": 50, "fat": 18},
            "total": {"calories": 1800, "protein": 80, "carbs": 200, "fat": 72},
            "servings": 4,
            "detailed_breakdown": []
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {
            "score": 6.5,
            "breakdown": "Moderate health rating due to high fat content"
        }
        
        # Mock ChromaDB
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        recipe_data = {
            "title": "Pasta Carbonara",
            "raw_text": """
            Pasta Carbonara
            - 400g spaghetti
            - 4 eggs
            - 100g parmesan cheese
            - 200g bacon
            Cook spaghetti, fry bacon, mix eggs and cheese, combine all
            """,
            "cuisine_type": "Italian",
            "servings": 4
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Pasta Carbonara"
        assert len(data["ingredients"]) == 4
        assert data["calories"] == 450
        assert data["health_rating"] == 6.5
        assert data["servings"] == 4
    
    def test_create_recipe_with_preserve_original(self, client, auth_headers, mocker):
        """Test creating a recipe with preserve_original flag"""
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Simple Salad",
            ingredients=[
                {"name": "lettuce", "quantity": "1", "unit": "head"},
                {"name": "tomatoes", "quantity": "2", "unit": ""},
                {"name": "olive oil", "quantity": "2", "unit": "tbsp"}
            ],
            instructions=[
                "Chop up the lettuce real good",  # Original wording preserved
                "Slice them tomatoes",
                "Drizzle that oil on top"
            ],
            servings=2,
            cuisine_type="Mediterranean",
            dietary_tags=["Vegan", "Gluten-Free"]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 120, "protein": 2, "carbs": 8, "fat": 10},
            "total": {"calories": 240, "protein": 4, "carbs": 16, "fat": 20},
            "servings": 2
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 8.5, "breakdown": "Very healthy"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        recipe_data = {
            "title": "Simple Salad",
            "raw_text": """
            Chop up the lettuce real good
            Slice them tomatoes
            Drizzle that oil on top
            """,
            "preserve_original": True  # This flag should preserve original instructions
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that instructions are preserved in original form
        assert "Chop up the lettuce real good" in data["instructions"][0]
        assert "Slice them tomatoes" in data["instructions"][1]
    
    def test_create_recipe_from_url(self, client, auth_headers, mocker):
        """Test creating a recipe from a URL"""
        # Mock URL scraper
        mock_scraper = mocker.patch('app.services.url_scraper.URLRecipeScraper.scrape_recipe')
        mock_scraper.return_value = {
            'text': """
            Chocolate Chip Cookies
            Ingredients: 2 cups flour, 1 cup butter, 1 cup sugar, 2 eggs, 1 cup chocolate chips
            Instructions: Mix ingredients, form cookies, bake at 350F for 12 minutes
            """,
            'structured_data': {
                'title': 'Best Chocolate Chip Cookies',
                'servings': 24
            },
            'image_url': 'https://example.com/cookie.jpg'
        }
        
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Chocolate Chip Cookies",
            ingredients=[
                {"name": "flour", "quantity": "2", "unit": "cups"},
                {"name": "butter", "quantity": "1", "unit": "cup"},
                {"name": "sugar", "quantity": "1", "unit": "cup"},
                {"name": "eggs", "quantity": "2", "unit": ""},
                {"name": "chocolate chips", "quantity": "1", "unit": "cup"}
            ],
            instructions=["Mix ingredients", "Form cookies", "Bake at 350F for 12 minutes"],
            servings=24,
            cuisine_type="American",
            dietary_tags=[]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 150, "protein": 2, "carbs": 20, "fat": 8},
            "total": {"calories": 3600, "protein": 48, "carbs": 480, "fat": 192},
            "servings": 24
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 4.0, "breakdown": "High in sugar and fat"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        recipe_data = {
            "title": "",
            "raw_text": "https://example.com/chocolate-chip-cookies"
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Best Chocolate Chip Cookies"  # Uses title from URL
        assert data["image_url"] == "https://example.com/cookie.jpg"
        assert data["servings"] == 24
        assert len(data["ingredients"]) == 5
    
    def test_create_recipe_from_url_failure(self, client, auth_headers, mocker):
        """Test handling URL scraping failure"""
        mock_scraper = mocker.patch('app.services.url_scraper.URLRecipeScraper.scrape_recipe')
        mock_scraper.side_effect = ValueError("Failed to fetch recipe")
        
        recipe_data = {
            "title": "",
            "raw_text": "https://invalid-url.com/recipe"
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Failed to fetch recipe from URL" in response.json()["detail"]


class TestRecipeImageUpload:
    """Test recipe creation from image uploads"""
    
    def test_upload_recipe_image(self, client, auth_headers, mocker):
        """Test uploading a recipe image"""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Mock OCR service
        mock_ocr = mocker.patch('app.services.ocr_service.OCRService.extract_text_from_image')
        mock_ocr.return_value = """
        Tomato Soup Recipe
        Ingredients:
        - 4 tomatoes
        - 1 onion
        - 2 cups vegetable broth
        
        Instructions:
        1. Chop tomatoes and onion
        2. Sauté onion until soft
        3. Add tomatoes and broth
        4. Simmer for 20 minutes
        5. Blend until smooth
        """
        
        mock_validate = mocker.patch('app.services.ocr_service.OCRService.validate_image')
        mock_validate.return_value = (True, "Image is valid")
        
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Tomato Soup",
            ingredients=[
                {"name": "tomatoes", "quantity": "4", "unit": ""},
                {"name": "onion", "quantity": "1", "unit": ""},
                {"name": "vegetable broth", "quantity": "2", "unit": "cups"}
            ],
            instructions=[
                "Chop tomatoes and onion",
                "Sauté onion until soft",
                "Add tomatoes and broth",
                "Simmer for 20 minutes",
                "Blend until smooth"
            ],
            servings=4,
            cuisine_type="American",
            dietary_tags=["Vegan", "Gluten-Free"]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 45, "protein": 2, "carbs": 10, "fat": 0.5},
            "total": {"calories": 180, "protein": 8, "carbs": 40, "fat": 2},
            "servings": 4
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 9.0, "breakdown": "Very healthy, low calorie"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        # Prepare form data
        files = {"file": ("recipe.png", img_bytes, "image/png")}
        data = {
            "preserve_original": "false",
            "title": "My Tomato Soup",
            "cuisine_type": "American"
        }
        
        response = client.post(
            "/api/recipes/upload-image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "My Tomato Soup"
        assert len(result["ingredients"]) == 3
        assert result["cuisine_type"] == "American"
        assert "[Extracted from image]" in result["raw_text"]
    
    def test_upload_image_with_preserve_original(self, client, auth_headers, mocker):
        """Test image upload with preserve_original flag"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Mock OCR to return text with colloquial language
        mock_ocr = mocker.patch('app.services.ocr_service.OCRService.extract_text_from_image')
        mock_ocr.return_value = "Put 2 rice cookers of quinoa in a strainer"
        
        mock_validate = mocker.patch('app.services.ocr_service.OCRService.validate_image')
        mock_validate.return_value = (True, "Image is valid")
        
        # Mock parser to preserve original
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Quinoa Recipe",
            ingredients=[
                {"name": "quinoa", "quantity": "2", "unit": "cups"}  # Converted for nutrition
            ],
            instructions=[
                "Put 2 rice cookers of quinoa in a strainer"  # Original preserved
            ],
            servings=4,
            cuisine_type=None,
            dietary_tags=[]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 278, "protein": 12, "carbs": 48, "fat": 3.6},
            "total": {"calories": 1112, "protein": 48, "carbs": 192, "fat": 14.4},
            "servings": 4
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 7.5, "breakdown": "Healthy grain"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        files = {"file": ("recipe.png", img_bytes, "image/png")}
        data = {"preserve_original": "true"}
        
        response = client.post(
            "/api/recipes/upload-image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Check that original wording is preserved
        assert "Put 2 rice cookers of quinoa in a strainer" in result["instructions"][0]
        # But nutrition should still be calculated
        assert result["calories"] == 278
    
    def test_upload_invalid_image(self, client, auth_headers, mocker):
        """Test uploading an invalid image"""
        # Create invalid image data
        invalid_data = b"This is not an image"
        
        files = {"file": ("recipe.txt", invalid_data, "text/plain")}
        data = {"preserve_original": "false"}
        
        response = client.post(
            "/api/recipes/upload-image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]
    
    def test_upload_image_ocr_failure(self, client, auth_headers, mocker):
        """Test handling OCR extraction failure"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_validate = mocker.patch('app.services.ocr_service.OCRService.validate_image')
        mock_validate.return_value = (True, "Image is valid")
        
        mock_ocr = mocker.patch('app.services.ocr_service.OCRService.extract_text_from_image')
        mock_ocr.return_value = ""  # Empty text extraction
        
        files = {"file": ("recipe.png", img_bytes, "image/png")}
        data = {"preserve_original": "false"}
        
        response = client.post(
            "/api/recipes/upload-image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Could not extract any text" in response.json()["detail"]