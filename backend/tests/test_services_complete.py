"""
Comprehensive tests for OCR, URL scraping, and search services
"""
import base64
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
from PIL import Image
from app.services.ocr_service import OCRService
from app.services.url_scraper import URLRecipeScraper


class TestOCRService:
    """Test OCR service for text extraction from images"""
    
    def test_extract_text_basic(self, mocker):
        """Test basic text extraction from image"""
        # Mock pytesseract
        mock_tesseract = mocker.patch('app.services.ocr_service.pytesseract.image_to_string')
        mock_tesseract.return_value = "Recipe: Tomato Soup\nIngredients: tomatoes, onion"
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        Recipe: Tomato Soup
        Ingredients:
        - 4 tomatoes
        - 1 onion
        Instructions:
        1. Chop vegetables
        2. Simmer for 20 minutes
        """
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.ocr_service.OpenAI', return_value=mock_client):
            service = OCRService()
            
            # Create test image
            img = Image.new('RGB', (100, 100), color='white')
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            result = service.extract_text_from_image(img_data)
            
            assert "Recipe: Tomato Soup" in result
            assert "4 tomatoes" in result
            assert "Simmer for 20 minutes" in result
    
    def test_extract_text_with_preserve_original(self, mocker):
        """Test text extraction with preserve_original flag"""
        mock_tesseract = mocker.patch('app.services.ocr_service.pytesseract.image_to_string')
        mock_tesseract.return_value = "Put 2 rice cookers of quinoa"
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # With preserve_original, should keep original wording
        mock_response.choices[0].message.content = "Put 2 rice cookers of quinoa in a strainer"
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.ocr_service.OpenAI', return_value=mock_client):
            service = OCRService()
            
            img = Image.new('RGB', (100, 100), color='white')
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            result = service.extract_text_from_image(img_data, preserve_original=True)
            
            # Should preserve original wording
            assert "Put 2 rice cookers of quinoa" in result
            # Should not reformat to standard units in the text
            assert "2 cups" not in result
    
    def test_preprocess_image(self, mocker):
        """Test image preprocessing for better OCR"""
        mock_tesseract = mocker.patch('app.services.ocr_service.pytesseract.image_to_string')
        # Different results for different preprocessing approaches
        mock_tesseract.side_effect = [
            "blurry text",  # First attempt
            "clear text from adaptive threshold",  # Second attempt (best)
            "okay text"  # Third attempt
        ]
        
        service = OCRService()
        service.client = None  # No OpenAI for this test
        
        img = Image.new('RGB', (100, 100), color='gray')
        processed = service._preprocess_image(img)
        
        # Should return the image that produced the best OCR result
        assert processed is not None
    
    def test_validate_image(self):
        """Test image validation"""
        service = OCRService()
        
        # Test valid image
        img = Image.new('RGB', (500, 500), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        is_valid, message = service.validate_image(img_data)
        assert is_valid
        assert message == "Image is valid"
        
        # Test image too small
        small_img = Image.new('RGB', (100, 100), color='white')
        small_bytes = BytesIO()
        small_img.save(small_bytes, format='PNG')
        small_data = small_bytes.getvalue()
        
        is_valid, message = service.validate_image(small_data)
        assert not is_valid
        assert "too small" in message
        
        # Test image too large
        large_img = Image.new('RGB', (5000, 5000), color='white')
        large_bytes = BytesIO()
        large_img.save(large_bytes, format='PNG', optimize=True, quality=10)
        large_data = large_bytes.getvalue()
        
        is_valid, message = service.validate_image(large_data)
        assert not is_valid
        assert "too large" in message
    
    def test_ocr_fallback_when_ai_fails(self, mocker):
        """Test fallback to basic cleaning when AI enhancement fails"""
        mock_tesseract = mocker.patch('app.services.ocr_service.pytesseract.image_to_string')
        mock_tesseract.return_value = """
        Ingredients:
        - flour
        - water
        Instructions:
        1. Mix
        2. Bake
        """
        
        # Mock OpenAI to fail
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        with patch('app.services.ocr_service.OpenAI', return_value=mock_client):
            service = OCRService()
            
            img = Image.new('RGB', (100, 100), color='white')
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            result = service.extract_text_from_image(img_data)
            
            # Should fall back to basic cleaning
            assert "Ingredients:" in result
            assert "- flour" in result
            assert "Instructions:" in result


class TestURLScraper:
    """Test URL recipe scraping service"""
    
    def test_scrape_recipe_with_json_ld(self, mocker):
        """Test scraping recipe with JSON-LD structured data"""
        mock_response = Mock()
        html_content = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Recipe",
                "name": "Chocolate Cake",
                "recipeIngredient": ["2 cups flour", "1 cup sugar", "3 eggs"],
                "recipeInstructions": "Mix and bake at 350F",
                "recipeYield": "8 servings",
                "image": "https://example.com/cake.jpg"
            }
            </script>
        </head>
        <body>Recipe content here</body>
        </html>
        """
        mock_response.text = html_content
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            scraper = URLRecipeScraper()
            result = scraper.scrape_recipe("https://example.com/recipe")
            
            assert result['structured_data']['title'] == "Chocolate Cake"
            assert len(result['structured_data']['ingredients']) == 3
            assert result['image_url'] == "https://example.com/cake.jpg"
            assert "Mix and bake" in result['text']
    
    def test_scrape_recipe_without_structured_data(self, mocker):
        """Test scraping recipe without structured data"""
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <h1>Simple Pasta</h1>
            <div class="ingredients">
                <ul>
                    <li>200g pasta</li>
                    <li>Tomato sauce</li>
                </ul>
            </div>
            <div class="instructions">
                <p>Cook pasta according to package.</p>
                <p>Add sauce and serve.</p>
            </div>
            <img src="https://example.com/pasta.jpg" alt="Pasta dish">
        </body>
        </html>
        """
        mock_response.content = mock_response.text.encode('utf-8')
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            scraper = URLRecipeScraper()
            result = scraper.scrape_recipe("https://example.com/pasta")
            
            assert "Simple Pasta" in result['text']
            assert "200g pasta" in result['text']
            assert "Cook pasta" in result['text']
            # Should extract image from img tag
            assert result['image_url'] == "https://example.com/pasta.jpg"
    
    def test_scrape_recipe_with_microdata(self, mocker):
        """Test scraping recipe with microdata format"""
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <div itemscope itemtype="http://schema.org/Recipe">
                <h1 itemprop="name">Veggie Burger</h1>
                <img itemprop="image" src="https://example.com/burger.jpg">
                <span itemprop="recipeYield">4 servings</span>
                <div itemprop="recipeIngredient">Black beans</div>
                <div itemprop="recipeIngredient">Breadcrumbs</div>
                <div itemprop="recipeInstructions">Mash beans, mix, form patties, cook</div>
            </div>
        </body>
        </html>
        """
        mock_response.content = mock_response.text.encode('utf-8')
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            scraper = URLRecipeScraper()
            result = scraper.scrape_recipe("https://example.com/burger")
            
            assert "Veggie Burger" in result['text']
            assert "Black beans" in result['text']
            assert result['image_url'] == "https://example.com/burger.jpg"
    
    def test_scrape_recipe_network_error(self, mocker):
        """Test handling network errors during scraping"""
        import requests
        with patch('requests.get', side_effect=requests.RequestException("Network error")):
            scraper = URLRecipeScraper()
            
            with pytest.raises(ValueError) as exc_info:
                scraper.scrape_recipe("https://example.com/recipe")
            
            assert "Failed to fetch" in str(exc_info.value)
    
    def test_extract_image_from_meta_tags(self, mocker):
        """Test extracting image from meta tags"""
        mock_response = Mock()
        mock_response.text = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/meta-image.jpg">
            <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
        </head>
        <body>Recipe content</body>
        </html>
        """
        mock_response.content = mock_response.text.encode('utf-8')
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            scraper = URLRecipeScraper()
            result = scraper.scrape_recipe("https://example.com/recipe")
            
            # Should prioritize og:image
            assert result['image_url'] == "https://example.com/meta-image.jpg"


class TestRecipeSearch:
    """Test recipe search and recommendations"""
    
    @pytest.mark.skip(reason="/api/recipes/search endpoint not implemented yet")
    def test_search_recipes(self, client, auth_headers, sample_recipe, mocker):
        """Test searching recipes"""
        # Mock ChromaDB collection
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['recipe_1']],
            'distances': [[0.5]],
            'metadatas': [[{
                'recipe_id': sample_recipe.id,
                'user_id': sample_recipe.user_id,
                'calories': 200,
                'health_rating': 7.5
            }]]
        }
        mocker.patch('app.database.get_chroma_collection', return_value=mock_collection)
        
        response = client.post(
            "/api/recipes/search",
            json={"query": "pasta"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        assert results[0]["id"] == sample_recipe.id
    
    @pytest.mark.skip(reason="/api/recipes/{id}/recommendations endpoint not implemented yet")
    def test_get_recommendations(self, client, auth_headers, sample_recipe, mocker):
        """Test getting recipe recommendations"""
        # Mock ChromaDB collection
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['recipe_1', 'recipe_2']],
            'distances': [[0.3, 0.5]],
            'metadatas': [[
                {
                    'recipe_id': sample_recipe.id,
                    'user_id': sample_recipe.user_id,
                    'calories': 200,
                    'health_rating': 7.5
                },
                {
                    'recipe_id': 2,
                    'user_id': sample_recipe.user_id,
                    'calories': 250,
                    'health_rating': 8.0
                }
            ]]
        }
        mocker.patch('app.database.get_chroma_collection', return_value=mock_collection)
        
        # Mock health analyzer
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 8.0, "breakdown": "Healthy"}
        
        response = client.get(
            f"/api/recipes/{sample_recipe.id}/recommendations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        recommendations = response.json()
        assert len(recommendations) > 0
    
    @pytest.mark.skip(reason="/api/recipes/search endpoint not implemented yet")
    def test_filter_recipes_by_criteria(self, client, auth_headers, db, test_user, mocker):
        """Test filtering recipes by various criteria"""
        # Create multiple recipes with different properties
        recipe1 = Recipe(
            user_id=test_user.id,
            title="Healthy Salad",
            raw_text="Salad recipe",
            ingredients=[{"name": "lettuce", "quantity": "1", "unit": "head"}],
            instructions=["Mix ingredients"],
            calories=100,
            health_rating=9.0,
            cuisine_type="Mediterranean",
            dietary_tags=["Vegan", "Gluten-Free"],
            servings=2
        )
        recipe2 = Recipe(
            user_id=test_user.id,
            title="Pasta Carbonara",
            raw_text="Pasta recipe",
            ingredients=[{"name": "pasta", "quantity": "200", "unit": "g"}],
            instructions=["Cook pasta"],
            calories=450,
            health_rating=6.0,
            cuisine_type="Italian",
            dietary_tags=[],
            servings=4
        )
        db.add_all([recipe1, recipe2])
        db.commit()
        
        # Mock ChromaDB
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['recipe_1']],
            'metadatas': [[{'recipe_id': recipe1.id}]]
        }
        mocker.patch('app.database.get_chroma_collection', return_value=mock_collection)
        
        # Test filtering by max calories
        response = client.post(
            "/api/recipes/search",
            json={"max_calories": 200},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test filtering by dietary tags
        response = client.post(
            "/api/recipes/search",
            json={"dietary_tags": ["Vegan"]},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test filtering by cuisine type
        response = client.post(
            "/api/recipes/search",
            json={"cuisine_type": "Italian"},
            headers=auth_headers
        )
        assert response.status_code == 200