import requests
from typing import Dict, List, Any, Optional
import re
from app.core.config import settings

class NutritionCalculator:
    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        self.base_url = "https://api.spoonacular.com"
        
    def calculate_nutrition(self, ingredients: List[Dict[str, Any]], servings: int = 4) -> Dict[str, Any]:
        if not self.api_key:
            return self._estimate_nutrition_fallback(ingredients, servings)
        
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0
        }
        
        for ingredient in ingredients:
            nutrition = self._get_ingredient_nutrition(ingredient)
            if nutrition:
                for key in total_nutrition:
                    total_nutrition[key] += nutrition.get(key, 0)
        
        per_serving = {
            key: round(value / servings, 1) 
            for key, value in total_nutrition.items()
        }
        
        return {
            "total": total_nutrition,
            "per_serving": per_serving,
            "servings": servings
        }
    
    def _get_ingredient_nutrition(self, ingredient: Dict[str, Any]) -> Optional[Dict[str, float]]:
        try:
            # Extract the English name if there's a translation in parentheses
            ingredient_name = ingredient['name']
            if '(' in ingredient_name and ')' in ingredient_name:
                # Use the English translation for API lookup
                # e.g., "bhindi (okra)" -> use "okra"
                english_name = ingredient_name[ingredient_name.index('(')+1:ingredient_name.index(')')].strip()
                query = f"{ingredient.get('quantity', '1')} {ingredient.get('unit', '')} {english_name}"
            else:
                query = f"{ingredient.get('quantity', '1')} {ingredient.get('unit', '')} {ingredient_name}"
            
            url = f"{self.base_url}/recipes/parseIngredients"
            params = {
                "apiKey": self.api_key,
                "ingredientList": query,
                "servings": 1,
                "includeNutrition": True
            }
            
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    nutrition_data = data[0].get("nutrition", {})
                    nutrients = nutrition_data.get("nutrients", [])
                    
                    result = {}
                    nutrient_map = {
                        "Calories": "calories",
                        "Protein": "protein",
                        "Carbohydrates": "carbs",
                        "Fat": "fat",
                        "Fiber": "fiber",
                        "Sugar": "sugar",
                        "Sodium": "sodium"
                    }
                    
                    for nutrient in nutrients:
                        name = nutrient.get("name")
                        if name in nutrient_map:
                            result[nutrient_map[name]] = nutrient.get("amount", 0)
                    
                    return result
        except Exception as e:
            print(f"Error getting nutrition for {ingredient['name']}: {e}")
        
        return self._estimate_single_ingredient(ingredient)
    
    def _estimate_nutrition_fallback(self, ingredients: List[Dict[str, Any]], servings: int) -> Dict[str, Any]:
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0
        }
        
        for ingredient in ingredients:
            estimated = self._estimate_single_ingredient(ingredient)
            if estimated:
                for key in total_nutrition:
                    total_nutrition[key] += estimated.get(key, 0)
        
        per_serving = {
            key: round(value / servings, 1) 
            for key, value in total_nutrition.items()
        }
        
        return {
            "total": total_nutrition,
            "per_serving": per_serving,
            "servings": servings,
            "estimated": True
        }
    
    def _estimate_single_ingredient(self, ingredient: Dict[str, Any]) -> Dict[str, float]:
        # Use English name if available for better estimation
        ingredient_name = ingredient['name']
        if '(' in ingredient_name and ')' in ingredient_name:
            # Use the English translation for estimation
            name_lower = ingredient_name[ingredient_name.index('(')+1:ingredient_name.index(')')].strip().lower()
        else:
            name_lower = ingredient_name.lower()
        
        quantity = self._parse_quantity(ingredient.get('quantity', '1'))
        unit = (ingredient.get('unit', '') or '').lower()
        
        calorie_estimates = {
            'oil': 120, 'butter': 100, 'sugar': 50, 'flour': 55,
            'rice': 200, 'pasta': 200, 'chicken': 165, 'beef': 250,
            'pork': 240, 'fish': 120, 'egg': 70, 'milk': 150,
            'cheese': 110, 'yogurt': 100, 'bread': 80, 'potato': 160,
            'onion': 40, 'garlic': 5, 'tomato': 20, 'carrot': 25,
            'broccoli': 30, 'spinach': 7, 'lettuce': 5, 'pepper': 20,
            'salt': 0, 'pepper': 0, 'spice': 5, 'herb': 2,
            # Indian ingredients
            'okra': 33, 'bhindi': 33, 'dal': 120, 'lentil': 120,
            'peanut': 160, 'cashew': 155, 'almond': 160,
            'curry': 5, 'asafoetida': 2, 'hing': 2,
            'turmeric': 8, 'haldi': 8, 'cumin': 8, 'jeera': 8,
            'coriander': 5, 'dhania': 5, 'chili': 10, 'mirchi': 10,
            'ginger': 10, 'fenugreek': 12, 'methi': 12,
            'mustard': 10, 'coconut': 180, 'paneer': 265
        }
        
        multipliers = {
            'cup': 1, 'cups': 1, 'tablespoon': 0.0625, 'tbsp': 0.0625,
            'teaspoon': 0.02, 'tsp': 0.02, 'ounce': 0.125, 'oz': 0.125,
            'pound': 2, 'lb': 2, 'gram': 0.004, 'g': 0.004,
            'kilogram': 4, 'kg': 4, 'piece': 1, 'clove': 0.02
        }
        
        base_calories = 50
        for key, cal in calorie_estimates.items():
            if key in name_lower:
                base_calories = cal
                break
        
        multiplier = multipliers.get(unit, 1)
        estimated_calories = base_calories * quantity * multiplier
        
        # Estimate other nutrients based on ingredient type
        nutrients = {"calories": round(estimated_calories)}
        
        # Protein-rich foods
        if any(protein in name_lower for protein in ['chicken', 'beef', 'pork', 'fish', 'egg', 'dal', 'lentil', 'beans', 'paneer']):
            nutrients["protein"] = round(estimated_calories * 0.25)  # ~25% from protein
            nutrients["fat"] = round(estimated_calories * 0.15)
            nutrients["carbs"] = round(estimated_calories * 0.1)
        # Nuts and seeds
        elif any(nut in name_lower for nut in ['peanut', 'cashew', 'almond', 'nut', 'seed']):
            nutrients["protein"] = round(estimated_calories * 0.15)
            nutrients["fat"] = round(estimated_calories * 0.5)  # High fat
            nutrients["carbs"] = round(estimated_calories * 0.2)
            nutrients["fiber"] = round(estimated_calories * 0.05)
        # Vegetables
        elif any(veg in name_lower for veg in ['okra', 'bhindi', 'onion', 'tomato', 'carrot', 'broccoli', 'spinach', 'pepper', 'cucumber']):
            nutrients["protein"] = round(estimated_calories * 0.1)
            nutrients["carbs"] = round(estimated_calories * 0.7)
            nutrients["fiber"] = round(estimated_calories * 0.15)
            nutrients["sugar"] = round(estimated_calories * 0.2)
        # Grains and carbs
        elif any(grain in name_lower for grain in ['rice', 'flour', 'bread', 'pasta', 'potato']):
            nutrients["carbs"] = round(estimated_calories * 0.8)
            nutrients["protein"] = round(estimated_calories * 0.1)
            nutrients["fiber"] = round(estimated_calories * 0.05)
        # Oils and fats
        elif any(fat in name_lower for fat in ['oil', 'butter', 'ghee', 'cream']):
            nutrients["fat"] = round(estimated_calories * 0.95)
        # Dairy
        elif any(dairy in name_lower for dairy in ['milk', 'yogurt', 'cheese']):
            nutrients["protein"] = round(estimated_calories * 0.2)
            nutrients["fat"] = round(estimated_calories * 0.3)
            nutrients["carbs"] = round(estimated_calories * 0.3)
            nutrients["sugar"] = round(estimated_calories * 0.2)
        # Spices generally have minimal macros
        else:
            nutrients["carbs"] = round(estimated_calories * 0.5)
            nutrients["protein"] = round(estimated_calories * 0.1)
        
        # Add some sodium for savory ingredients
        if not any(sweet in name_lower for sweet in ['sugar', 'honey', 'syrup']):
            nutrients["sodium"] = round(quantity * multiplier * 50)  # mg
        
        # Ensure we have all keys
        for key in ["protein", "carbs", "fat", "fiber", "sugar", "sodium"]:
            if key not in nutrients:
                nutrients[key] = 0
                
        return nutrients
    
    def _parse_quantity(self, quantity_str: str) -> float:
        if not quantity_str:
            return 1
        
        quantity_str = str(quantity_str).strip()
        
        if '/' in quantity_str:
            parts = quantity_str.split('/')
            try:
                return float(parts[0]) / float(parts[1])
            except:
                return 1
        
        if '-' in quantity_str:
            parts = quantity_str.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except:
                pass
        
        try:
            return float(quantity_str)
        except:
            return 1