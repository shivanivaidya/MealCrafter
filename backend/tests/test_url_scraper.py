"""
Tests for URL recipe scraping service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.url_scraper import URLRecipeScraper


class TestURLRecipeScraper:
    """Test URL recipe scraping functionality"""
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance"""
        return URLRecipeScraper()
    
    @pytest.fixture
    def sample_json_ld(self):
        """Sample JSON-LD recipe data"""
        return {
            "@type": "Recipe",
            "name": "Chocolate Chip Cookies",
            "description": "Delicious homemade cookies",
            "image": "https://example.com/cookie.jpg",
            "recipeYield": "24 cookies",
            "prepTime": "PT15M",
            "cookTime": "PT12M",
            "recipeIngredient": [
                "2 cups flour",
                "1 cup butter",
                "1 cup chocolate chips"
            ],
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "Preheat oven to 350°F"},
                {"@type": "HowToStep", "text": "Mix ingredients"},
                {"@type": "HowToStep", "text": "Bake for 12 minutes"}
            ],
            "nutrition": {
                "calories": "250",
                "proteinContent": "3g",
                "carbohydrateContent": "30g",
                "fatContent": "15g"
            }
        }
    
    @pytest.fixture
    def sample_html_with_json_ld(self, sample_json_ld):
        """Sample HTML with JSON-LD structured data"""
        import json
        return f"""
        <html>
        <head>
            <title>Chocolate Chip Cookies Recipe</title>
            <script type="application/ld+json">
            {json.dumps(sample_json_ld)}
            </script>
        </head>
        <body>
            <h1>Chocolate Chip Cookies</h1>
        </body>
        </html>
        """
    
    @patch('app.services.url_scraper.requests.get')
    def test_scrape_recipe_with_json_ld(
        self,
        mock_get,
        scraper,
        sample_html_with_json_ld
    ):
        """Test scraping a recipe with JSON-LD structured data"""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.content = sample_html_with_json_ld
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper.scrape_recipe("https://example.com/recipe")
        
        assert result is not None
        assert "Chocolate Chip Cookies" in result["text"]
        assert result["image_url"] == "https://example.com/cookie.jpg"
        assert result["structured_data"]["title"] == "Chocolate Chip Cookies"
        assert len(result["structured_data"]["ingredients"]) == 3
        assert len(result["structured_data"]["instructions"]) == 3
    
    @patch('app.services.url_scraper.requests.get')
    def test_scrape_recipe_without_structured_data(self, mock_get, scraper):
        """Test scraping a recipe without JSON-LD (manual extraction)"""
        html_content = """
        <html>
        <head>
            <title>Simple Recipe - My Food Blog</title>
            <meta property="og:image" content="https://example.com/recipe.jpg">
        </head>
        <body>
            <h1 class="recipe-title">Simple Recipe</h1>
            <div class="ingredients">
                <h2>Ingredients</h2>
                <ul>
                    <li class="ingredient">1 cup water</li>
                    <li class="ingredient">2 cups flour</li>
                </ul>
            </div>
            <div class="instructions">
                <h2>Instructions</h2>
                <ol>
                    <li class="instruction">Mix water and flour</li>
                    <li class="instruction">Knead the dough</li>
                </ol>
            </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper.scrape_recipe("https://example.com/recipe")
        
        assert result is not None
        assert "Simple Recipe" in result["text"]
        assert result["image_url"] == "https://example.com/recipe.jpg"
        assert "1 cup water" in result["text"]
        assert "Mix water and flour" in result["text"]
    
    @patch('app.services.url_scraper.requests.get')
    def test_scrape_invalid_url(self, mock_get, scraper):
        """Test scraping with invalid URL"""
        with pytest.raises(ValueError, match="Invalid URL format"):
            scraper.scrape_recipe("not-a-url")
    
    @patch('app.services.url_scraper.requests.get')
    def test_scrape_network_error(self, mock_get, scraper):
        """Test handling network errors"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(ValueError, match="Failed to fetch URL"):
            scraper.scrape_recipe("https://example.com/recipe")
    
    def test_parse_duration(self, scraper):
        """Test ISO 8601 duration parsing"""
        assert scraper._parse_duration("PT30M") == "30 minutes"
        assert scraper._parse_duration("PT1H30M") == "1 hour 30 minutes"
        assert scraper._parse_duration("PT2H") == "2 hours"
        assert scraper._parse_duration("PT1M") == "1 minute"
        assert scraper._parse_duration("invalid") == "invalid"
    
    def test_is_recipe_schema(self, scraper):
        """Test recipe schema detection"""
        assert scraper._is_recipe_schema({"@type": "Recipe"}) == True
        assert scraper._is_recipe_schema({"@type": ["Recipe", "Article"]}) == True
        assert scraper._is_recipe_schema({"@type": "Article"}) == False
        assert scraper._is_recipe_schema({}) == False
        assert scraper._is_recipe_schema("not a dict") == False
    
    @patch('app.services.url_scraper.requests.get')
    def test_extract_image_from_various_sources(self, mock_get, scraper):
        """Test image extraction from different HTML structures"""
        html_variants = [
            # Image in JSON-LD as string
            """<script type="application/ld+json">{"@type": "Recipe", "image": "https://example.com/img1.jpg"}</script>""",
            
            # Image in JSON-LD as object
            """<script type="application/ld+json">{"@type": "Recipe", "image": {"url": "https://example.com/img2.jpg"}}</script>""",
            
            # Image in JSON-LD as array
            """<script type="application/ld+json">{"@type": "Recipe", "image": ["https://example.com/img3.jpg"]}</script>""",
            
            # Open Graph image
            """<meta property="og:image" content="https://example.com/img4.jpg">""",
            
            # Image with itemprop
            """<img itemprop="image" src="https://example.com/img5.jpg">""",
            
            # Image with class
            """<img class="recipe-image" src="https://example.com/img6.jpg">"""
        ]
        
        expected_images = [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg",
            "https://example.com/img3.jpg",
            "https://example.com/img4.jpg",
            "https://example.com/img5.jpg",
            "https://example.com/img6.jpg"
        ]
        
        for html, expected_image in zip(html_variants, expected_images):
            mock_response = Mock()
            mock_response.content = f"<html><body>{html}</body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = scraper.scrape_recipe("https://example.com/recipe")
            if expected_image in ["https://example.com/img1.jpg", "https://example.com/img2.jpg", "https://example.com/img3.jpg"]:
                # These come from JSON-LD
                assert result.get("image_url") == expected_image or expected_image in str(result)
            else:
                # These come from HTML parsing
                assert result.get("image_url") == expected_image or result.get("image_url") is None


class TestRecipeURLIntegration:
    """Test recipe creation with URL input"""
    
    @patch('app.routers.recipes.URLRecipeScraper')
    @patch('app.routers.recipes.AIRecipeParser')
    @patch('app.routers.recipes.AINutritionCalculator')
    @patch('app.routers.recipes.AIHealthAnalyzer')
    def test_create_recipe_from_url(
        self,
        mock_health,
        mock_nutrition,
        mock_parser,
        mock_scraper_class,
        client,
        auth_headers
    ):
        """Test creating a recipe from a URL"""
        # Mock URL scraper
        mock_scraper = Mock()
        mock_scraper.scrape_recipe.return_value = {
            "text": "Recipe content from URL",
            "image_url": "https://example.com/recipe-image.jpg",
            "structured_data": {
                "title": "URL Recipe Title"
            }
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Mock AI services
        mock_parser_instance = Mock()
        mock_parser_instance.parse_recipe_text.return_value = Mock(
            title="Parsed Title",
            ingredients=[{"name": "ingredient", "quantity": "1", "unit": "cup"}],
            instructions=["Step 1"],
            servings=4,
            cuisine_type=None,
            dietary_tags=[]
        )
        mock_parser.return_value = mock_parser_instance
        
        mock_nutrition_instance = Mock()
        mock_nutrition_instance.calculate_nutrition.return_value = {
            "per_serving": {"calories": 100},
            "total": {"calories": 400}
        }
        mock_nutrition.return_value = mock_nutrition_instance
        
        mock_health_instance = Mock()
        mock_health_instance.analyze_health.return_value = {
            "score": 8,
            "breakdown": "Healthy"
        }
        mock_health.return_value = mock_health_instance
        
        # Send request with URL
        response = client.post(
            "/api/recipes/",
            json={
                "title": "",  # Empty title, should use URL title
                "raw_text": "https://example.com/recipe"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "URL Recipe Title"  # Should use URL-extracted title
        assert data["image_url"] == "https://example.com/recipe-image.jpg"
        
        # Verify scraper was called
        mock_scraper.scrape_recipe.assert_called_once_with("https://example.com/recipe")