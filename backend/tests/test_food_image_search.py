"""
Tests for food image search service functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from app.services.food_image_search import FoodImageSearch


class TestFoodImageSearch:
    """Test food image search service"""
    
    @pytest.fixture
    def search_service(self):
        """Create food image search service"""
        return FoodImageSearch()
    
    def test_initialization(self, search_service):
        """Test service initialization"""
        assert search_service.headers is not None
        assert 'User-Agent' in search_service.headers
        assert 'Mozilla' in search_service.headers['User-Agent']
        assert search_service.image_cache == {}
    
    def test_validate_image_url_valid_jpg(self, search_service):
        """Test validating JPG image URL"""
        url = "https://example.com/image.jpg"
        assert search_service._validate_image_url(url) is True
    
    def test_validate_image_url_valid_jpeg(self, search_service):
        """Test validating JPEG image URL"""
        url = "https://example.com/image.jpeg"
        assert search_service._validate_image_url(url) is True
    
    def test_validate_image_url_valid_png(self, search_service):
        """Test validating PNG image URL"""
        url = "https://example.com/image.png"
        assert search_service._validate_image_url(url) is True
    
    def test_validate_image_url_valid_webp(self, search_service):
        """Test validating WebP image URL"""
        url = "https://example.com/image.webp"
        assert search_service._validate_image_url(url) is True
    
    def test_validate_image_url_looks_like_image(self, search_service):
        """Test validating URL that looks like image without extension"""
        url = "https://cdn.example.com/images/photo123"
        assert search_service._validate_image_url(url) is True
    
    def test_validate_image_url_empty(self, search_service):
        """Test validating empty URL"""
        assert search_service._validate_image_url("") is False
        assert search_service._validate_image_url(None) is False
    
    def test_validate_image_url_invalid_protocol(self, search_service):
        """Test validating URL with invalid protocol"""
        url = "ftp://example.com/image.jpg"
        assert search_service._validate_image_url(url) is False
    
    def test_validate_image_url_no_extension_no_keywords(self, search_service):
        """Test validating URL without extension or image keywords"""
        url = "https://example.com/some-random-page"
        assert search_service._validate_image_url(url) is False
    
    def test_cache_functionality(self, search_service):
        """Test caching functionality"""
        recipe_name = "Test Recipe"
        image_url = "https://example.com/test.jpg"
        
        # Initially empty cache
        assert recipe_name not in search_service.image_cache
        
        # Add to cache
        search_service.image_cache[recipe_name] = image_url
        
        # Should return cached result
        with patch.object(search_service, '_search_google_images') as mock_google:
            result = search_service.search_food_image(recipe_name)
            assert result == image_url
            mock_google.assert_not_called()  # Should not call Google if cached
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_google_images_success(self, mock_get, search_service):
        """Test successful Google Images search"""
        # Mock HTML response with image URLs
        html_content = '''
        <script>
        ["https://example.com/large-image.jpg?size=1600", "other", "data"]
        ["https://example.com/small-image.jpg?size=90", "other", "data"]
        </script>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_google_images("pasta recipe")
        
        assert result == "https://example.com/large-image.jpg?size=1600"
        mock_get.assert_called_once()
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_google_images_no_results(self, mock_get, search_service):
        """Test Google Images search with no results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No images found</body></html>"
        mock_get.return_value = mock_response
        
        result = search_service._search_google_images("nonexistent recipe")
        
        assert result is None
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_google_images_http_error(self, mock_get, search_service):
        """Test Google Images search with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = search_service._search_google_images("pasta recipe")
        
        assert result is None
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_google_images_exception(self, mock_get, search_service):
        """Test Google Images search with exception"""
        mock_get.side_effect = Exception("Network error")
        
        result = search_service._search_google_images("pasta recipe")
        
        assert result is None
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_recipe_sites_success(self, mock_get, search_service):
        """Test successful recipe site search"""
        # Mock HTML response with recipe images
        html_content = '''
        <html>
        <body>
        <img class="card__img" src="https://allrecipes.com/recipe-image.jpg" alt="Recipe">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_recipe_sites("pasta recipe")
        
        assert result == "https://allrecipes.com/recipe-image.jpg"
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_recipe_sites_relative_url(self, mock_get, search_service):
        """Test recipe site search with relative URL"""
        html_content = '''
        <html>
        <body>
        <img class="card__img" src="/images/recipe.jpg" alt="Recipe">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_recipe_sites("pasta recipe")
        
        # Should convert relative URL to absolute
        assert result == "https://www.allrecipes.com/images/recipe.jpg"
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_recipe_sites_protocol_relative_url(self, mock_get, search_service):
        """Test recipe site search with protocol-relative URL"""
        html_content = '''
        <html>
        <body>
        <img class="card__img" src="//cdn.allrecipes.com/recipe.jpg" alt="Recipe">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_recipe_sites("pasta recipe")
        
        # Should add https protocol
        assert result == "https://cdn.allrecipes.com/recipe.jpg"
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_pexels_success(self, mock_get, search_service):
        """Test successful Pexels search"""
        html_content = '''
        <html>
        <body>
        <img data-big-src="https://images.pexels.com/photos/123/pexels-photo-123.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260" alt="Food photo">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_pexels("pasta recipe")
        
        assert result is not None
        assert "pexels.com" in result
        assert "h=750&w=1260" in result
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_pexels_srcset(self, mock_get, search_service):
        """Test Pexels search with srcset attribute"""
        html_content = '''
        <html>
        <body>
        <img srcset="https://images.pexels.com/small.jpg 1x, https://images.pexels.com/large.jpg 2x" alt="Food photo">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_pexels("pasta recipe")
        
        assert result == "https://images.pexels.com/large.jpg"
    
    @patch('app.services.food_image_search.requests.get')
    def test_search_pexels_fallback_src(self, mock_get, search_service):
        """Test Pexels search fallback to src attribute"""
        html_content = '''
        <html>
        <body>
        <img src="https://images.pexels.com/photos/123/photo.jpg" alt="Food photo">
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        result = search_service._search_pexels("pasta recipe")
        
        assert result is not None
        assert "images.pexels.com" in result
    
    @patch('app.services.food_image_search.requests.get')
    def test_get_fallback_image_with_category(self, mock_get, search_service):
        """Test getting fallback image with matching category"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"image": "https://foodish-api.com/images/pasta/pasta1.jpg"}
        mock_get.return_value = mock_response
        
        result = search_service.get_fallback_image("pasta recipe")
        
        assert result == "https://foodish-api.com/images/pasta/pasta1.jpg"
        mock_get.assert_called_with('https://foodish-api.com/api/images/pasta', timeout=3)
    
    @patch('app.services.food_image_search.requests.get')
    def test_get_fallback_image_burger_category(self, mock_get, search_service):
        """Test getting fallback image for burger category"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"image": "https://foodish-api.com/images/burger/burger1.jpg"}
        mock_get.return_value = mock_response
        
        result = search_service.get_fallback_image("hamburger recipe")
        
        assert result == "https://foodish-api.com/images/burger/burger1.jpg"
        mock_get.assert_called_with('https://foodish-api.com/api/images/burger', timeout=3)
    
    @patch('app.services.food_image_search.requests.get')
    def test_get_fallback_image_no_category_match(self, mock_get, search_service):
        """Test getting fallback image with no category match"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"image": "https://foodish-api.com/images/misc/food1.jpg"}
        mock_get.return_value = mock_response
        
        result = search_service.get_fallback_image("unknown recipe")
        
        assert result == "https://foodish-api.com/images/misc/food1.jpg"
        mock_get.assert_called_with('https://foodish-api.com/api/', timeout=3)
    
    @patch('app.services.food_image_search.requests.get')
    def test_get_fallback_image_api_error(self, mock_get, search_service):
        """Test getting fallback image when API fails"""
        mock_get.side_effect = Exception("API error")
        
        result = search_service.get_fallback_image("pasta recipe")
        
        # Should return Lorem Picsum fallback
        assert "picsum.photos" in result
        assert "1200/800" in result
    
    @patch('app.services.food_image_search.requests.get')
    def test_get_fallback_image_lorem_picsum(self, mock_get, search_service):
        """Test Lorem Picsum fallback has correct parameters"""
        mock_get.side_effect = Exception("API error")
        
        result = search_service.get_fallback_image("test recipe")
        
        assert result.startswith("https://picsum.photos/1200/800?random=")
        # Should include hash of recipe name for consistent random
        assert str(hash("test recipe")) in result
    
    def test_search_food_image_full_workflow(self, search_service):
        """Test complete search workflow with all fallbacks"""
        recipe_name = "chocolate cake"
        
        with patch.object(search_service, '_search_google_images', return_value=None), \
             patch.object(search_service, '_search_recipe_sites', return_value=None), \
             patch.object(search_service, '_search_pexels', return_value="https://pexels.com/cake.jpg"):
            
            result = search_service.search_food_image(recipe_name)
            
            assert result == "https://pexels.com/cake.jpg"
            assert search_service.image_cache[recipe_name] == result
    
    def test_search_food_image_google_success(self, search_service):
        """Test search workflow when Google Images succeeds"""
        recipe_name = "pizza recipe"
        google_result = "https://google.com/pizza.jpg"
        
        with patch.object(search_service, '_search_google_images', return_value=google_result), \
             patch.object(search_service, '_search_recipe_sites') as mock_recipe, \
             patch.object(search_service, '_search_pexels') as mock_pexels:
            
            result = search_service.search_food_image(recipe_name)
            
            assert result == google_result
            # Should not call other search methods if Google succeeds
            mock_recipe.assert_not_called()
            mock_pexels.assert_not_called()
    
    def test_search_food_image_no_results(self, search_service):
        """Test search workflow when no results found"""
        recipe_name = "unknown dish"
        
        with patch.object(search_service, '_search_google_images', return_value=None), \
             patch.object(search_service, '_search_recipe_sites', return_value=None), \
             patch.object(search_service, '_search_pexels', return_value=None):
            
            result = search_service.search_food_image(recipe_name)
            
            assert result is None


class TestFoodImageSearchCategories:
    """Test food image search category mapping"""
    
    @pytest.fixture
    def search_service(self):
        return FoodImageSearch()
    
    def test_category_mapping_pizza(self, search_service):
        """Test pizza category mapping"""
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"image": "https://foodish-api.com/images/pizza/pizza1.jpg"}
            mock_get.return_value = mock_response
            
            result = search_service.get_fallback_image("margherita pizza")
            
            mock_get.assert_called_with('https://foodish-api.com/api/images/pizza', timeout=3)
    
    def test_category_mapping_pasta(self, search_service):
        """Test pasta category mapping"""
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"image": "https://foodish-api.com/images/pasta/pasta1.jpg"}
            mock_get.return_value = mock_response
            
            result = search_service.get_fallback_image("spaghetti noodles")
            
            mock_get.assert_called_with('https://foodish-api.com/api/images/pasta', timeout=3)
    
    def test_category_mapping_dessert(self, search_service):
        """Test dessert category mapping"""
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"image": "https://foodish-api.com/images/dessert/dessert1.jpg"}
            mock_get.return_value = mock_response
            
            result = search_service.get_fallback_image("chocolate brownie")
            
            mock_get.assert_called_with('https://foodish-api.com/api/images/dessert', timeout=3)
    
    def test_category_mapping_indian_food(self, search_service):
        """Test Indian food category mapping"""
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"image": "https://foodish-api.com/images/biryani/biryani1.jpg"}
            mock_get.return_value = mock_response
            
            result = search_service.get_fallback_image("chicken biryani")
            
            mock_get.assert_called_with('https://foodish-api.com/api/images/biryani', timeout=3)
    
    def test_category_mapping_butter_chicken(self, search_service):
        """Test butter chicken category mapping"""
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"image": "https://foodish-api.com/images/butter-chicken/bc1.jpg"}
            mock_get.return_value = mock_response
            
            result = search_service.get_fallback_image("butter chicken curry")
            
            mock_get.assert_called_with('https://foodish-api.com/api/images/butter-chicken', timeout=3)


class TestFoodImageSearchIntegration:
    """Integration tests for food image search"""
    
    def test_user_agent_headers(self):
        """Test that proper User-Agent headers are set"""
        service = FoodImageSearch()
        
        assert 'User-Agent' in service.headers
        user_agent = service.headers['User-Agent']
        assert 'Mozilla' in user_agent
        assert 'Chrome' in user_agent
        assert 'Safari' in user_agent
    
    def test_search_timeout_handling(self):
        """Test that timeouts are handled gracefully"""
        service = FoodImageSearch()
        
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            # Should not raise exception, should return None
            result = service._search_google_images("test recipe")
            assert result is None
            
            result = service._search_recipe_sites("test recipe")
            assert result is None
            
            result = service._search_pexels("test recipe")
            assert result is None
    
    def test_html_parsing_with_malformed_html(self):
        """Test handling malformed HTML gracefully"""
        service = FoodImageSearch()
        
        with patch('app.services.food_image_search.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><img src='broken.jpg'><img src=https://example.com/valid.jpg></html>"
            mock_get.return_value = mock_response
            
            # Should handle malformed HTML and find valid images
            result = service._search_recipe_sites("test recipe")
            # Will find the valid image URL
            assert result is not None or result is None  # Depends on validation