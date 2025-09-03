"""
Tests for AI services (parser, nutrition calculator, health analyzer)
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.recipe_parser_ai import AIRecipeParser
from app.services.nutrition_ai import AINutritionCalculator
from app.services.health_analyzer_ai import AIHealthAnalyzer


class TestAIRecipeParser:
    """Test AI recipe parsing service"""
    
    @patch('app.services.recipe_parser_ai.OpenAI')
    def test_parse_recipe_success(self, mock_openai_class):
        """Test successful recipe parsing"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Pasta Carbonara",
            "ingredients": [
                {"name": "spaghetti", "quantity": "400", "unit": "g"},
                {"name": "eggs", "quantity": "4", "unit": ""},
                {"name": "bacon", "quantity": "200", "unit": "g"}
            ],
            "instructions": [
                "Cook pasta",
                "Fry bacon",
                "Mix eggs and cheese",
                "Combine all ingredients"
            ],
            "servings": 4,
            "cuisine_type": "Italian",
            "dietary_tags": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        parser = AIRecipeParser()
        recipe_text = """
        Pasta Carbonara
        Ingredients: 400g spaghetti, 4 eggs, 200g bacon
        Instructions: Cook pasta, fry bacon, mix eggs, combine
        """
        
        result = parser.parse_recipe_text(recipe_text)
        
        assert result.title == "Pasta Carbonara"
        assert len(result.ingredients) == 3
        assert result.ingredients[0]["name"] == "spaghetti"
        assert len(result.instructions) == 4
        assert result.servings == 4
        assert result.cuisine_type == "Italian"
    
    @patch('app.services.recipe_parser_ai.OpenAI')
    def test_parse_recipe_with_markdown_response(self, mock_openai_class):
        """Test parsing when AI returns markdown-wrapped JSON"""
        mock_client = Mock()
        mock_response = Mock()
        # Response wrapped in markdown code blocks
        mock_response.choices[0].message.content = """```json
        {
            "title": "Simple Recipe",
            "ingredients": [{"name": "water", "quantity": "1", "unit": "cup"}],
            "instructions": ["Boil water"],
            "servings": 2,
            "cuisine_type": null,
            "dietary_tags": []
        }
        ```"""
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        parser = AIRecipeParser()
        result = parser.parse_recipe_text("Simple recipe: boil water")
        
        assert result.title == "Simple Recipe"
        assert len(result.ingredients) == 1
    
    @patch('app.services.recipe_parser_ai.OpenAI')
    def test_parse_recipe_invalid_json(self, mock_openai_class):
        """Test handling of invalid JSON response"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        parser = AIRecipeParser()
        
        with pytest.raises(ValueError, match="Failed to parse recipe"):
            parser.parse_recipe_text("Test recipe")
    
    def test_parse_recipe_no_api_key(self):
        """Test parser initialization without API key"""
        with patch('app.core.config.settings.OPENAI_API_KEY', None):
            parser = AIRecipeParser()
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                parser.parse_recipe_text("Test recipe")


class TestAINutritionCalculator:
    """Test AI nutrition calculation service"""
    
    @patch('app.services.nutrition_ai.OpenAI')
    def test_calculate_nutrition_success(self, mock_openai_class):
        """Test successful nutrition calculation"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "total": {
                "calories": 800,
                "protein": 40,
                "carbs": 100,
                "fat": 30,
                "fiber": 10,
                "sugar": 5,
                "sodium": 1000
            },
            "per_serving": {
                "calories": 200,
                "protein": 10,
                "carbs": 25,
                "fat": 7.5,
                "fiber": 2.5,
                "sugar": 1.25,
                "sodium": 250
            },
            "servings": 4,
            "detailed_breakdown": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        calculator = AINutritionCalculator()
        ingredients = [
            {"name": "flour", "quantity": "2", "unit": "cups"},
            {"name": "water", "quantity": "1", "unit": "cup"}
        ]
        
        result = calculator.calculate_nutrition(ingredients, 4)
        
        assert result["per_serving"]["calories"] == 200
        assert result["total"]["calories"] == 800
        assert result["servings"] == 4
    
    @patch('app.services.nutrition_ai.OpenAI')
    def test_calculate_nutrition_with_json_parsing_retry(self, mock_openai_class):
        """Test JSON parsing with retry logic"""
        mock_client = Mock()
        mock_response = Mock()
        # Malformed JSON with trailing comma
        mock_response.choices[0].message.content = """{
            "total": {"calories": 500,},
            "per_serving": {"calories": 125},
            "servings": 4
        }"""
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        calculator = AINutritionCalculator()
        ingredients = [{"name": "test", "quantity": "1", "unit": "cup"}]
        
        # Should handle the trailing comma and parse successfully
        result = calculator.calculate_nutrition(ingredients, 4)
        assert result["per_serving"]["calories"] == 125


class TestAIHealthAnalyzer:
    """Test AI health analysis service"""
    
    @patch('app.services.health_analyzer_ai.OpenAI')
    def test_analyze_health_success(self, mock_openai_class):
        """Test successful health analysis"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "score": 7.5,
            "summary": "Healthy balanced meal",
            "healthy_aspects": [
                {
                    "title": "High Protein",
                    "description": "Good protein content"
                }
            ],
            "watch_points": [
                {
                    "ingredient": "Oil",
                    "concern": "High in calories"
                }
            ],
            "nutritional_highlights": {
                "vitamins": ["Vitamin C: 20% DV"],
                "minerals": ["Iron: 15% DV"],
                "macros": {
                    "protein_quality": "Good",
                    "carb_quality": "Complex carbs",
                    "fat_quality": "Healthy fats"
                },
                "special_compounds": ["Antioxidants"]
            },
            "dietary_considerations": {
                "suitable_for": ["Vegetarian"],
                "may_not_suit": ["Keto"],
                "modifications_for_conditions": {
                    "diabetes": "Reduce sugar"
                }
            },
            "improvement_tips": ["Add more vegetables"],
            "meal_pairing_suggestions": ["Serve with salad"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        analyzer = AIHealthAnalyzer()
        recipe_data = {
            "ingredients": [{"name": "test"}],
            "instructions": ["Cook"],
            "nutrition_data": {
                "per_serving": {"calories": 200}
            }
        }
        
        result = analyzer.analyze_health(recipe_data)
        
        assert result["score"] == 7.5
        assert "Health Score: 7.5/10" in result["breakdown"]
        assert len(result["healthy_points"]) == 1
        assert len(result["watch_points"]) == 1
    
    @patch('app.services.health_analyzer_ai.OpenAI')
    def test_format_health_breakdown(self, mock_openai_class):
        """Test health breakdown formatting"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "score": 8,
            "summary": "Very healthy",
            "healthy_aspects": [],
            "watch_points": [],
            "improvement_tips": ["Tip 1", "Tip 2"],
            "meal_pairing_suggestions": ["Pairing 1"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        analyzer = AIHealthAnalyzer()
        recipe_data = {"ingredients": [], "instructions": []}
        
        result = analyzer.analyze_health(recipe_data)
        breakdown = result["breakdown"]
        
        assert "**Health Score: 8/10**" in breakdown
        assert "Tips to Make It Healthier" in breakdown
        assert "• Tip 1" in breakdown
        assert "• Tip 2" in breakdown
        assert "Suggested Pairings" in breakdown
        assert "• Pairing 1" in breakdown
    
    def test_extract_text_from_item(self):
        """Test text extraction from various item formats"""
        analyzer = AIHealthAnalyzer()
        
        # Test string
        assert analyzer._extract_text_from_item("Simple text", ["tip"]) == "Simple text"
        
        # Test dictionary
        dict_item = {"tip": "Dictionary tip"}
        assert analyzer._extract_text_from_item(dict_item, ["tip"]) == "Dictionary tip"
        
        # Test string representation of dictionary
        str_dict = "{'tip': 'String dict tip'}"
        result = analyzer._extract_text_from_item(str_dict, ["tip"])
        assert result == "String dict tip"
        
        # Test with alternative keys
        dict_item = {"description": "Description text"}
        assert analyzer._extract_text_from_item(dict_item, ["tip", "description"]) == "Description text"


class TestAIServicesIntegration:
    """Test integration between AI services"""
    
    @patch('app.services.recipe_parser_ai.OpenAI')
    @patch('app.services.nutrition_ai.OpenAI')
    @patch('app.services.health_analyzer_ai.OpenAI')
    def test_full_recipe_processing_pipeline(
        self,
        mock_health_openai,
        mock_nutrition_openai,
        mock_parser_openai
    ):
        """Test complete recipe processing pipeline"""
        # Setup parser mock
        parser_response = Mock()
        parser_response.choices[0].message.content = json.dumps({
            "title": "Test Recipe",
            "ingredients": [
                {"name": "ingredient1", "quantity": "1", "unit": "cup"}
            ],
            "instructions": ["Step 1"],
            "servings": 2,
            "cuisine_type": "Test",
            "dietary_tags": []
        })
        mock_parser_openai.return_value.chat.completions.create.return_value = parser_response
        
        # Setup nutrition mock
        nutrition_response = Mock()
        nutrition_response.choices[0].message.content = json.dumps({
            "total": {"calories": 400},
            "per_serving": {"calories": 200},
            "servings": 2
        })
        mock_nutrition_openai.return_value.chat.completions.create.return_value = nutrition_response
        
        # Setup health mock
        health_response = Mock()
        health_response.choices[0].message.content = json.dumps({
            "score": 7,
            "summary": "Healthy",
            "healthy_aspects": [],
            "watch_points": []
        })
        mock_health_openai.return_value.chat.completions.create.return_value = health_response
        
        # Process recipe through all services
        parser = AIRecipeParser()
        parsed = parser.parse_recipe_text("Test recipe text")
        
        calculator = AINutritionCalculator()
        nutrition = calculator.calculate_nutrition(parsed.ingredients, parsed.servings)
        
        analyzer = AIHealthAnalyzer()
        health = analyzer.analyze_health({
            "ingredients": parsed.ingredients,
            "instructions": parsed.instructions,
            "nutrition_data": nutrition
        })
        
        # Verify pipeline results
        assert parsed.title == "Test Recipe"
        assert nutrition["per_serving"]["calories"] == 200
        assert health["score"] == 7