"""
Tests for video recipe extraction functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.video_extractor import VideoRecipeExtractor


class TestVideoRecipeExtractor:
    """Test video recipe extraction service"""
    
    def test_detect_platform_youtube(self):
        """Test detecting YouTube URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://www.youtube.com/watch?v=abc123") == "youtube"
        assert extractor._detect_platform("https://youtu.be/abc123") == "youtube"
        assert extractor._detect_platform("https://m.youtube.com/watch?v=abc123") == "youtube"
    
    def test_detect_platform_instagram(self):
        """Test detecting Instagram URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://www.instagram.com/reel/123") == "instagram"
        assert extractor._detect_platform("https://instagram.com/p/123") == "instagram"
    
    def test_detect_platform_tiktok(self):
        """Test detecting TikTok URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"
        assert extractor._detect_platform("https://tiktok.com/@user/video/123") == "tiktok"
    
    def test_detect_platform_facebook(self):
        """Test detecting Facebook URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://www.facebook.com/watch/?v=123") == "facebook"
        assert extractor._detect_platform("https://fb.watch/123") == "facebook"
    
    def test_detect_platform_vimeo(self):
        """Test detecting Vimeo URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://vimeo.com/123456") == "vimeo"
        assert extractor._detect_platform("https://www.vimeo.com/123456") == "vimeo"
    
    def test_detect_platform_unknown(self):
        """Test detecting unknown platform URLs"""
        extractor = VideoRecipeExtractor()
        
        assert extractor._detect_platform("https://example.com/video") == "unknown"
    
    def test_get_youtube_video_id(self):
        """Test extracting YouTube video ID from various URL formats"""
        extractor = VideoRecipeExtractor()
        
        # Standard watch URL
        assert extractor._get_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        
        # Short URL
        assert extractor._get_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        
        # Embed URL
        assert extractor._get_youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        
        # Mobile URL
        assert extractor._get_youtube_video_id("https://m.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        
        # URL with additional parameters
        assert extractor._get_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s") == "dQw4w9WgXcQ"
        
        # Invalid URL
        assert extractor._get_youtube_video_id("https://example.com/video") is None
    
    @patch('app.services.video_extractor.yt_dlp.YoutubeDL')
    @patch('app.services.video_extractor.YouTubeTranscriptApi')
    def test_extract_youtube_with_transcript(self, mock_transcript_api, mock_yt_dlp):
        """Test extracting YouTube video with transcript"""
        # Mock yt-dlp metadata
        mock_ydl = MagicMock()
        mock_info = {
            'title': 'Amazing Pasta Recipe',
            'uploader': 'Chef John',
            'thumbnail': 'https://example.com/thumb.jpg',
            'duration': 300,
            'description': 'Learn how to make pasta\n\nIngredients:\n- 200g pasta\n- Salt\n\nInstructions:\n1. Boil water\n2. Cook pasta'
        }
        mock_ydl.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        
        # Mock transcript API correctly - it calls api.fetch(video_id) directly
        mock_api_instance = Mock()
        mock_transcript_entry1 = Mock()
        mock_transcript_entry1.text = 'Today we are making pasta'
        mock_transcript_entry2 = Mock()
        mock_transcript_entry2.text = 'First, boil water'
        
        mock_api_instance.fetch.return_value = [mock_transcript_entry1, mock_transcript_entry2]
        mock_transcript_api.return_value = mock_api_instance
        
        extractor = VideoRecipeExtractor()
        result = extractor.extract_from_url("https://www.youtube.com/watch?v=abc123")
        
        assert result['platform'] == 'youtube'
        assert result['title'] == 'Amazing Pasta Recipe'
        assert result['author'] == 'Chef John'
        assert result['thumbnail'] == 'https://example.com/thumb.jpg'
        assert 'Ingredients:' in result['description']
        assert result['transcript'] is not None
        assert 'Today we are making pasta' in result['transcript']
        assert '200g pasta' in result['recipe_text']
    
    @patch('app.services.video_extractor.yt_dlp.YoutubeDL')
    @patch('app.services.video_extractor.YouTubeTranscriptApi')
    def test_extract_youtube_no_transcript(self, mock_transcript_api, mock_yt_dlp):
        """Test extracting YouTube video without transcript"""
        # Mock yt-dlp metadata
        mock_ydl = MagicMock()
        mock_info = {
            'title': 'Quick Recipe',
            'uploader': 'Home Cook',
            'thumbnail': 'https://example.com/thumb.jpg',
            'duration': 120,
            'description': 'Simple recipe in description'
        }
        mock_ydl.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        
        # Mock no transcript available
        mock_transcript_api.list_transcripts.side_effect = Exception("No transcript available")
        
        extractor = VideoRecipeExtractor()
        result = extractor.extract_from_url("https://www.youtube.com/watch?v=xyz789")
        
        assert result['platform'] == 'youtube'
        assert result['title'] == 'Quick Recipe'
        assert result['transcript'] is None
        assert 'Simple recipe in description' in result['full_text']
    
    @patch('app.services.video_extractor.yt_dlp.YoutubeDL')
    def test_extract_instagram(self, mock_yt_dlp):
        """Test extracting Instagram video/reel"""
        mock_ydl = MagicMock()
        mock_info = {
            'title': 'Instagram Recipe',
            'uploader': 'foodie_chef',
            'thumbnail': 'https://example.com/ig_thumb.jpg',
            'description': '🍝 Amazing pasta recipe! #cooking #recipe\n\nIngredients in comments 👇'
        }
        mock_ydl.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        
        extractor = VideoRecipeExtractor()
        result = extractor.extract_from_url("https://www.instagram.com/reel/abc123")
        
        assert result['platform'] == 'instagram'
        assert result['title'] == 'Instagram Recipe'
        assert result['author'] == 'foodie_chef'
        assert 'Amazing pasta recipe' in result['description']
    
    @patch('app.services.video_extractor.yt_dlp.YoutubeDL')
    def test_extract_tiktok(self, mock_yt_dlp):
        """Test extracting TikTok video"""
        mock_ydl = MagicMock()
        mock_info = {
            'title': 'TikTok Recipe',
            'creator': 'quick_recipes',
            'uploader': 'quick_recipes',
            'thumbnail': 'https://example.com/tiktok_thumb.jpg',
            'description': '30 second pasta hack! #foodhack #quickrecipe'
        }
        mock_ydl.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        
        extractor = VideoRecipeExtractor()
        result = extractor.extract_from_url("https://www.tiktok.com/@user/video/123")
        
        assert result['platform'] == 'tiktok'
        assert result['title'] == 'TikTok Recipe'
        assert result['author'] == 'quick_recipes'
        assert '30 second pasta hack' in result['description']
    
    @patch('app.services.video_extractor.yt_dlp.YoutubeDL')
    def test_extract_generic_video(self, mock_yt_dlp):
        """Test extracting from generic video platform"""
        mock_ydl = MagicMock()
        mock_info = {
            'title': 'Generic Video Recipe',
            'uploader': 'Unknown Chef',
            'thumbnail': 'https://example.com/generic_thumb.jpg',
            'description': 'Recipe video from unknown platform'
        }
        mock_ydl.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        
        extractor = VideoRecipeExtractor()
        result = extractor.extract_from_url("https://randomvideo.com/watch/123")
        
        assert result['platform'] == 'other'
        assert result['title'] == 'Generic Video Recipe'
        assert result['author'] == 'Unknown Chef'
    
    def test_extract_recipe_from_text(self):
        """Test extracting structured recipe from text"""
        extractor = VideoRecipeExtractor()
        
        text = """
        Welcome to my cooking channel!
        
        Ingredients:
        - 2 cups flour
        - 1 cup sugar
        - 3 eggs
        
        Instructions:
        1. Mix dry ingredients
        2. Add eggs
        3. Bake at 350F
        
        Enjoy!
        """
        
        result = extractor._extract_recipe_from_text(text)
        
        assert result is not None
        assert "## Ingredients:" in result
        assert "- 2 cups flour" in result
        assert "## Instructions:" in result
        # Check that we have some instructions content
        assert "Add eggs" in result or "Bake at 350F" in result
    
    def test_extract_recipe_from_text_no_structure(self):
        """Test extracting recipe from unstructured text"""
        extractor = VideoRecipeExtractor()
        
        text = "Just a random video description without any recipe structure"
        
        result = extractor._extract_recipe_from_text(text)
        
        assert result is None
    
    def test_extract_timestamps(self):
        """Test extracting timestamps from video description"""
        extractor = VideoRecipeExtractor()
        
        text = """
        Recipe timestamps:
        0:00 - Introduction
        1:30 - Preparing ingredients
        3:45 - Mixing the dough
        5:20 - Baking
        7:00 - Final result
        """
        
        timestamps = extractor._extract_timestamps(text)
        
        assert len(timestamps) == 5
        assert timestamps[0]['time'] == '0:00'
        assert timestamps[0]['description'] == 'Introduction'
        assert timestamps[2]['time'] == '3:45'
        assert timestamps[2]['description'] == 'Mixing the dough'
    
    @patch('app.services.video_extractor.YouTubeTranscriptApi')
    def test_extract_video_error_handling(self, mock_transcript_api):
        """Test error handling when video extraction fails"""
        with patch('app.services.video_extractor.yt_dlp.YoutubeDL') as mock_yt_dlp:
            # Make extract_info fail
            mock_yt_dlp.return_value.__enter__.return_value.extract_info.side_effect = Exception("Video not available")
            # Also mock transcript to avoid secondary errors
            mock_transcript_api.list_transcripts.side_effect = Exception("No transcript")
            
            extractor = VideoRecipeExtractor()
            
            # Since _extract_youtube returns empty metadata dict on failure,
            # the result won't raise an error but will have minimal content
            result = extractor.extract_from_url("https://www.youtube.com/watch?v=invalid")
            
            # The extraction should succeed but with default/empty values
            assert result['platform'] == 'youtube'
            assert result['title'] == ''  # Empty title when metadata fails


class TestVideoRecipeIntegration:
    """Test video extraction integration with recipe creation"""
    
    def test_create_recipe_from_youtube_url(self, client, auth_headers, mocker):
        """Test creating recipe from YouTube video URL"""
        # Mock video extractor
        mock_extractor = mocker.patch('app.routers.recipes.VideoRecipeExtractor')
        mock_instance = mock_extractor.return_value
        mock_instance.extract_from_url.return_value = {
            'title': 'Perfect Pasta Recipe',
            'thumbnail': 'https://example.com/pasta_thumb.jpg',
            'platform': 'youtube',
            'author': 'Chef Mario',
            'full_text': 'Pasta recipe with ingredients and instructions',
            'recipe_text': 'Ingredients: pasta, sauce. Instructions: Cook and mix.'
        }
        
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Perfect Pasta",
            ingredients=[
                {"name": "pasta", "quantity": "200", "unit": "g"},
                {"name": "tomato sauce", "quantity": "1", "unit": "cup"}
            ],
            instructions=["Cook pasta", "Add sauce"],
            servings=2,
            cuisine_type="Italian",
            dietary_tags=[]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 350, "protein": 12, "carbs": 65, "fat": 5},
            "total": {"calories": 700, "protein": 24, "carbs": 130, "fat": 10},
            "servings": 2
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 7.0, "breakdown": "Balanced meal"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        recipe_data = {
            "title": "",
            "raw_text": "https://www.youtube.com/watch?v=abc123"
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Perfect Pasta"  # Uses AI-parsed title (cleaned version)
        assert data["image_url"] == "https://example.com/pasta_thumb.jpg"
        # Check that raw_text contains the YouTube URL
        assert "https://www.youtube.com/watch?v=abc123" in data["raw_text"]
    
    def test_create_recipe_from_instagram_url(self, client, auth_headers, mocker):
        """Test creating recipe from Instagram reel URL"""
        mock_extractor = mocker.patch('app.routers.recipes.VideoRecipeExtractor')
        mock_instance = mock_extractor.return_value
        mock_instance.extract_from_url.return_value = {
            'title': 'Quick Salad',
            'thumbnail': 'https://example.com/salad_thumb.jpg',
            'platform': 'instagram',
            'author': 'healthy_eats',
            'full_text': 'Quick salad recipe',
            'recipe_text': 'Mix lettuce, tomatoes, dressing'
        }
        
        # Mock AI services
        mock_parse = mocker.patch('app.services.recipe_parser_ai.AIRecipeParser.parse_recipe_text')
        mock_parse.return_value = Mock(
            title="Quick Salad",
            ingredients=[
                {"name": "lettuce", "quantity": "1", "unit": "head"},
                {"name": "tomatoes", "quantity": "2", "unit": ""}
            ],
            instructions=["Chop vegetables", "Mix with dressing"],
            servings=1,
            cuisine_type="Mediterranean",
            dietary_tags=["Vegan"]
        )
        
        mock_nutrition = mocker.patch('app.services.nutrition_ai.AINutritionCalculator.calculate_nutrition')
        mock_nutrition.return_value = {
            "per_serving": {"calories": 120, "protein": 3, "carbs": 15, "fat": 6},
            "total": {"calories": 120, "protein": 3, "carbs": 15, "fat": 6},
            "servings": 1
        }
        
        mock_health = mocker.patch('app.services.health_analyzer_ai.AIHealthAnalyzer.analyze_health')
        mock_health.return_value = {"score": 9.0, "breakdown": "Very healthy"}
        
        mocker.patch('app.database.get_chroma_collection', return_value=Mock(add=Mock()))
        
        recipe_data = {
            "title": "",
            "raw_text": "https://www.instagram.com/reel/xyz789"
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Quick Salad"
        assert data["image_url"] == "https://example.com/salad_thumb.jpg"
        # Check that raw_text contains the Instagram URL
        assert "https://www.instagram.com/reel/xyz789" in data["raw_text"]
    
    def test_create_recipe_from_video_url_failure(self, client, auth_headers, mocker):
        """Test handling video extraction failure"""
        mock_extractor = mocker.patch('app.routers.recipes.VideoRecipeExtractor')
        mock_instance = mock_extractor.return_value
        mock_instance.extract_from_url.side_effect = Exception("Video unavailable")
        
        recipe_data = {
            "title": "",
            "raw_text": "https://www.youtube.com/watch?v=invalid"
        }
        
        response = client.post("/api/recipes/", json=recipe_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Failed to extract recipe from video" in response.json()["detail"]