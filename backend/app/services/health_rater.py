from typing import Dict, List, Any
import re

class HealthRater:
    def __init__(self):
        self.unhealthy_ingredients = {
            'sugar': -2, 'syrup': -2, 'candy': -3, 'soda': -3,
            'butter': -1, 'cream': -1.5, 'mayo': -1.5, 'mayonnaise': -1.5,
            'bacon': -2, 'sausage': -2, 'processed': -2,
            'fried': -2, 'deep-fried': -3, 'crispy': -1,
            'salt': -0.5, 'sodium': -1
        }
        
        self.healthy_ingredients = {
            'vegetable': 2, 'fruit': 2, 'whole grain': 2, 'whole wheat': 2,
            'quinoa': 2, 'oats': 2, 'brown rice': 1.5,
            'spinach': 2, 'kale': 2, 'broccoli': 2, 'carrot': 1.5,
            'tomato': 1.5, 'cucumber': 1.5, 'lettuce': 1.5,
            'chicken breast': 1, 'fish': 1.5, 'salmon': 2, 'tuna': 1.5,
            'beans': 1.5, 'lentils': 1.5, 'chickpeas': 1.5,
            'nuts': 1.5, 'seeds': 1.5, 'avocado': 1.5,
            'olive oil': 1, 'herbs': 1, 'spices': 1
        }
        
        self.cooking_methods = {
            'baked': 1, 'grilled': 1, 'steamed': 2, 'boiled': 1,
            'raw': 2, 'fresh': 2, 'roasted': 1,
            'fried': -2, 'deep-fried': -3, 'pan-fried': -1
        }
    
    def rate_health(self, recipe_data: Dict[str, Any]) -> float:
        score = 5.0
        
        ingredients = recipe_data.get('ingredients', [])
        instructions = recipe_data.get('instructions', [])
        nutrition = recipe_data.get('nutrition_data', {})
        
        score += self._rate_ingredients(ingredients)
        score += self._rate_cooking_method(instructions)
        score += self._rate_nutrition(nutrition)
        score += self._rate_portion_control(ingredients, recipe_data.get('servings', 4))
        
        return max(1.0, min(10.0, score))
    
    def _rate_ingredients(self, ingredients: List[Dict[str, Any]]) -> float:
        score = 0
        oil_count = 0
        sugar_count = 0
        vegetable_count = 0
        
        for ingredient in ingredients:
            name = ingredient.get('name', '').lower()
            
            for unhealthy, penalty in self.unhealthy_ingredients.items():
                if unhealthy in name:
                    score += penalty
                    if 'sugar' in unhealthy or 'syrup' in unhealthy:
                        sugar_count += 1
            
            for healthy, bonus in self.healthy_ingredients.items():
                if healthy in name:
                    score += bonus
                    if any(veg in healthy for veg in ['vegetable', 'spinach', 'kale', 'broccoli', 'carrot', 'tomato']):
                        vegetable_count += 1
            
            if any(oil in name for oil in ['oil', 'butter', 'margarine']):
                oil_count += 1
        
        if oil_count > 2:
            score -= (oil_count - 2) * 0.5
        
        if sugar_count > 1:
            score -= (sugar_count - 1)
        
        if vegetable_count < 2:
            score -= (2 - vegetable_count) * 0.5
        
        return score
    
    def _rate_cooking_method(self, instructions: List[str]) -> float:
        score = 0
        all_text = ' '.join(instructions).lower()
        
        for method, rating in self.cooking_methods.items():
            if method in all_text:
                score += rating
        
        if 'deep fry' in all_text or 'deep-fry' in all_text:
            score -= 2
        
        return score
    
    def _rate_nutrition(self, nutrition: Dict[str, Any]) -> float:
        if not nutrition or 'per_serving' not in nutrition:
            return 0
        
        score = 0
        per_serving = nutrition['per_serving']
        
        calories = per_serving.get('calories', 0)
        if calories > 0:
            if calories < 300:
                score += 1
            elif calories > 800:
                score -= 2
            elif calories > 600:
                score -= 1
        
        sodium = per_serving.get('sodium', 0)
        if sodium > 0:
            if sodium > 1000:
                score -= 2
            elif sodium > 600:
                score -= 1
        
        sugar = per_serving.get('sugar', 0)
        if sugar > 0:
            if sugar > 25:
                score -= 2
            elif sugar > 15:
                score -= 1
        
        fiber = per_serving.get('fiber', 0)
        if fiber > 5:
            score += 1
        
        protein = per_serving.get('protein', 0)
        if protein > 20:
            score += 0.5
        
        return score
    
    def _rate_portion_control(self, ingredients: List[Dict[str, Any]], servings: int) -> float:
        score = 0
        
        heavy_ingredients = ['cheese', 'cream', 'butter', 'oil', 'meat', 'beef', 'pork']
        heavy_count = sum(1 for ing in ingredients 
                         if any(heavy in ing.get('name', '').lower() for heavy in heavy_ingredients))
        
        if heavy_count > 0:
            ratio = heavy_count / len(ingredients)
            if ratio > 0.5:
                score -= 1
            elif ratio > 0.3:
                score -= 0.5
        
        if servings >= 6:
            score += 0.5
        elif servings <= 2:
            score -= 0.5
        
        return score