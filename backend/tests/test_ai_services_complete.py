"""
Comprehensive tests for AI services including nutrition, health analysis, and recipe parsing
"""
import json
from unittest.mock import Mock, patch
import pytest
from app.services.recipe_parser_ai import AIRecipeParser, ParsedRecipe
from app.services.nutrition_ai import AINutritionCalculator
from app.services.health_analyzer_ai import AIHealthAnalyzer


class TestNutritionCalculator:
    """Test nutrition calculation service"""
    
    def test_calculate_nutrition_basic(self, mocker):
        """Test basic nutrition calculation"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "total": {
                "calories": 1112,
                "protein": 48,
                "carbs": 192,
                "fat": 14.4,
                "fiber": 24,
                "sugar": 0,
                "sodium": 40
            },
            "per_serving": {
                "calories": 278,
                "protein": 12,
                "carbs": 48,
                "fat": 3.6,
                "fiber": 6,
                "sugar": 0,
                "sodium": 10
            },
            "servings": 4,
            "detailed_breakdown": [
                {
                    "ingredient": "2 cups quinoa",
                    "calories": 1112,
                    "protein": 48,
                    "carbs": 192,
                    "fat": 14.4
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.nutrition_ai.OpenAI', return_value=mock_client):
            calculator = AINutritionCalculator()
            ingredients = [
                {"name": "quinoa", "quantity": "2", "unit": "cups"}
            ]
            
            result = calculator.calculate_nutrition(ingredients, 4)
            
            assert result["per_serving"]["calories"] == 278
            assert result["total"]["calories"] == 1112
            assert result["servings"] == 4
            assert len(result["detailed_breakdown"]) == 1
    
    def test_calculate_nutrition_with_vague_quantities(self, mocker):
        """Test nutrition calculation with non-standard quantities"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # Should handle "to taste" and estimate reasonable amounts
        mock_response.choices[0].message.content = json.dumps({
            "total": {
                "calories": 150,
                "protein": 10,
                "carbs": 5,
                "fat": 12,
                "fiber": 0,
                "sugar": 0,
                "sodium": 500
            },
            "per_serving": {
                "calories": 75,
                "protein": 5,
                "carbs": 2.5,
                "fat": 6,
                "fiber": 0,
                "sugar": 0,
                "sodium": 250
            },
            "servings": 2,
            "detailed_breakdown": [
                {"ingredient": "salt (1/4 tsp estimated)", "calories": 0, "sodium": 500},
                {"ingredient": "olive oil (1 tbsp)", "calories": 120, "fat": 14}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.nutrition_ai.OpenAI', return_value=mock_client):
            calculator = AINutritionCalculator()
            ingredients = [
                {"name": "salt", "quantity": "to taste", "unit": None},
                {"name": "olive oil", "quantity": "a drizzle", "unit": None}
            ]
            
            result = calculator.calculate_nutrition(ingredients, 2)
            
            assert result["per_serving"]["calories"] == 75
            assert result["per_serving"]["sodium"] == 250
    
    def test_calculate_nutrition_zero_result_handling(self, mocker):
        """Test handling when nutrition calculator returns zeros"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "total": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0},
            "per_serving": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0},
            "servings": 4,
            "detailed_breakdown": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.nutrition_ai.OpenAI', return_value=mock_client):
            calculator = AINutritionCalculator()
            ingredients = [
                {"name": "water", "quantity": "as needed", "unit": None}
            ]
            
            result = calculator.calculate_nutrition(ingredients, 4)
            
            # Should return the zero values without error
            assert result["per_serving"]["calories"] == 0
            assert result["total"]["calories"] == 0


class TestHealthAnalyzer:
    """Test health analysis service"""
    
    def test_analyze_health_healthy_recipe(self, mocker):
        """Test health analysis for a healthy recipe"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 8.5,
            "summary": "Healthy vegetable-based dish",
            "healthy_aspects": [
                {"title": "High Fiber", "description": "Rich in fiber from vegetables"},
                {"title": "Low Fat", "description": "Low in saturated fat"},
                {"title": "Vitamins", "description": "Good source of vitamins"}
            ],
            "watch_points": [
                {"ingredient": "Salt", "concern": "Slightly high in sodium"}
            ],
            "improvement_tips": [
                "Reduce salt by half for lower sodium"
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.health_analyzer_ai.OpenAI', return_value=mock_client):
            analyzer = AIHealthAnalyzer()
            recipe_data = {
                "ingredients": [
                    {"name": "spinach", "quantity": "2", "unit": "cups"},
                    {"name": "tomatoes", "quantity": "3", "unit": ""}
                ],
                "nutrition_data": {
                    "per_serving": {"calories": 50, "protein": 3, "carbs": 10, "fat": 1}
                }
            }
            
            result = analyzer.analyze_health(recipe_data)
            
            assert result["score"] == 8.5
            assert "Health Score: 8.5/10" in result["breakdown"]
            assert "What Makes It Healthy" in result["breakdown"]
            assert len(result["healthy_points"]) == 3
    
    def test_analyze_health_unhealthy_recipe(self, mocker):
        """Test health analysis for an unhealthy recipe"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 3.5,
            "summary": "High calorie dish needing improvements",
            "healthy_aspects": [
                {"title": "Protein", "description": "Contains some protein"}
            ],
            "watch_points": [
                {"ingredient": "Fat", "concern": "Very high in saturated fat"},
                {"ingredient": "Calories", "concern": "Excessive calories per serving"},
                {"ingredient": "Sugar", "concern": "High in sugar"}
            ],
            "improvement_tips": [
                "Use lean meat instead",
                "Reduce portion size",
                "Add vegetables for balance"
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.health_analyzer_ai.OpenAI', return_value=mock_client):
            analyzer = AIHealthAnalyzer()
            recipe_data = {
                "ingredients": [
                    {"name": "bacon", "quantity": "1", "unit": "pound"},
                    {"name": "cheese", "quantity": "2", "unit": "cups"}
                ],
                "nutrition_data": {
                    "per_serving": {"calories": 800, "protein": 30, "carbs": 5, "fat": 70}
                }
            }
            
            result = analyzer.analyze_health(recipe_data)
            
            assert result["score"] == 3.5
            assert "Health Score: 3.5/10" in result["breakdown"]
            assert len(result["watch_points"]) > len(result["healthy_points"])


class TestRecipeParser:
    """Test recipe parsing service"""
    
    def test_parse_recipe_standard(self, mocker):
        """Test standard recipe parsing"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Vegetable Stir Fry",
            "ingredients": [
                {"name": "broccoli", "quantity": "2", "unit": "cups"},
                {"name": "carrots", "quantity": "1", "unit": "cup"},
                {"name": "soy sauce", "quantity": "3", "unit": "tbsp"}
            ],
            "instructions": [
                "Cut vegetables into bite-sized pieces",
                "Heat oil in a wok",
                "Stir-fry vegetables for 5 minutes",
                "Add soy sauce and serve"
            ],
            "servings": 4,
            "cuisine_type": "Asian",
            "dietary_tags": ["Vegan", "Gluten-Free"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.recipe_parser_ai.OpenAI', return_value=mock_client):
            parser = AIRecipeParser()
            text = """
            Vegetable Stir Fry
            - 2 cups broccoli
            - 1 cup carrots
            - 3 tbsp soy sauce
            
            Cut vegetables, heat oil, stir-fry for 5 minutes, add soy sauce
            """
            
            result = parser.parse_recipe_text(text)
            
            assert result.title == "Vegetable Stir Fry"
            assert len(result.ingredients) == 3
            assert len(result.instructions) == 4
            assert result.cuisine_type == "Asian"
            assert "Vegan" in result.dietary_tags
    
    def test_parse_recipe_with_preserve_original(self, mocker):
        """Test recipe parsing with preserve_original flag"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Grandma's Soup",
            "ingredients": [
                {"name": "chicken", "quantity": "1", "unit": "whole"},
                {"name": "water", "quantity": "8", "unit": "cups"}
            ],
            "instructions": [
                "Throw the chicken in the pot",  # Original wording preserved
                "Let 'er simmer real good for an hour or so"
            ],
            "servings": 6,
            "cuisine_type": "American",
            "dietary_tags": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.recipe_parser_ai.OpenAI', return_value=mock_client):
            parser = AIRecipeParser()
            text = """
            Grandma's Soup
            Throw the chicken in the pot
            Let 'er simmer real good for an hour or so
            """
            
            result = parser.parse_recipe_text(text, preserve_original=True)
            
            assert "Throw the chicken in the pot" in result.instructions[0]
            assert "Let 'er simmer real good" in result.instructions[1]
            # But ingredients should still be properly extracted
            assert result.ingredients[0]["name"] == "chicken"
            assert result.ingredients[0]["quantity"] == "1"
    
    def test_parse_recipe_ocr_text(self, mocker):
        """Test parsing OCR text with potential errors"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Apple Pie",
            "ingredients": [
                {"name": "apples", "quantity": "6", "unit": ""},
                {"name": "sugar", "quantity": "1", "unit": "cup"},
                {"name": "flour", "quantity": "2", "unit": "cups"}
            ],
            "instructions": [
                "Peel and slice apples",
                "Mix with sugar",
                "Make pie crust with flour",
                "Bake at 350F for 45 minutes"
            ],
            "servings": 8,
            "cuisine_type": "American",
            "dietary_tags": ["Vegetarian"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.recipe_parser_ai.OpenAI', return_value=mock_client):
            parser = AIRecipeParser()
            # OCR text with typical errors (0 instead of O, l instead of 1)
            text = """
            App1e Pie
            6 app1es
            l cup sugar
            2 cups f1our
            
            Pee1 and s1ice app1es
            Mix with sugar
            Make pie crust
            Bake at 35O°F for 45 minutes
            """
            
            result = parser.parse_recipe_text(text, is_ocr_text=True)
            
            # Parser should correct OCR errors
            assert result.title == "Apple Pie"
            assert result.ingredients[0]["name"] == "apples"
            assert result.ingredients[1]["quantity"] == "1"  # Corrected from "l"
    
    def test_parse_recipe_with_indian_ingredients(self, mocker):
        """Test parsing recipes with Indian ingredients"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Bhindi Masala",
            "ingredients": [
                {"name": "bhindi (okra)", "quantity": "500", "unit": "g"},
                {"name": "hing (asafoetida)", "quantity": "1", "unit": "pinch"},
                {"name": "jeera (cumin seeds)", "quantity": "1", "unit": "tsp"},
                {"name": "haldi (turmeric powder)", "quantity": "1/2", "unit": "tsp"}
            ],
            "instructions": [
                "Wash and dry bhindi completely",
                "Cut into pieces",
                "Heat oil and add jeera",
                "Add hing and then bhindi",
                "Add haldi and cook until done"
            ],
            "servings": 4,
            "cuisine_type": "Indian",
            "dietary_tags": ["Vegan", "Gluten-Free"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.recipe_parser_ai.OpenAI', return_value=mock_client):
            parser = AIRecipeParser()
            text = """
            Bhindi Masala
            - 500g bhindi
            - pinch of hing
            - 1 tsp jeera
            - 1/2 tsp haldi
            
            Wash and dry bhindi, cut into pieces, heat oil, add jeera,
            add hing and bhindi, add haldi and cook
            """
            
            result = parser.parse_recipe_text(text)
            
            # Should have English translations
            assert "okra" in result.ingredients[0]["name"]
            assert "asafoetida" in result.ingredients[1]["name"]
            assert "cumin seeds" in result.ingredients[2]["name"]
            assert "turmeric powder" in result.ingredients[3]["name"]
            assert result.cuisine_type == "Indian"