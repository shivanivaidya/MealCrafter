from typing import Dict, List, Any
from openai import OpenAI
from app.core.config import settings
import json
import re

class AINutritionCalculator:
    def __init__(self):
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
    
    def calculate_nutrition(self, ingredients: List[Dict[str, Any]], servings: int = 4) -> Dict[str, Any]:
        """
        Calculate nutrition using OpenAI
        """
        if not self.client:
            raise ValueError("OpenAI API key is required for nutrition calculation")
        
        return self._calculate_with_ai(ingredients, servings)
    
    def _calculate_with_ai(self, ingredients: List[Dict[str, Any]], servings: int) -> Dict[str, Any]:
        """Use OpenAI to calculate detailed nutrition"""
        
        ingredients_text = "\n".join([
            f"- {ing.get('quantity', '1')} {ing.get('unit', '')} {ing['name']}"
            for ing in ingredients
        ])
        
        prompt = f"""You are a professional nutritionist. Calculate the detailed nutritional information for this recipe.

Ingredients:
{ingredients_text}

Servings: {servings}

Return ONLY valid JSON without any markdown formatting, code blocks, or explanations.
Do not use markdown code blocks (no ```json or ```).
Provide nutritional analysis in this EXACT JSON format:
{{
    "total": {{
        "calories": 850,
        "protein": 45,
        "carbs": 95,
        "fat": 35,
        "fiber": 18,
        "sugar": 12,
        "sodium": 1200
    }},
    "per_serving": {{
        "calories": 213,
        "protein": 11.3,
        "carbs": 23.8,
        "fat": 8.8,
        "fiber": 4.5,
        "sugar": 3,
        "sodium": 300
    }},
    "servings": {servings},
    "detailed_breakdown": [
        {{
            "ingredient": "2 lbs bhindi (okra)",
            "calories": 60,
            "protein": 4,
            "carbs": 14,
            "fat": 0.4,
            "fiber": 6,
            "notes": "Rich in vitamins C, K, and folate"
        }},
        {{
            "ingredient": "3 tbsp oil",
            "calories": 360,
            "protein": 0,
            "carbs": 0,
            "fat": 42,
            "fiber": 0,
            "notes": "High in calories but provides essential fatty acids"
        }}
    ]
}}

Important Calculation Guidelines:

CALORIE CALCULATION METHOD:
- Use USDA FoodData Central and Indian Food Composition Tables as reference
- Calculate based on: Calories = (Protein × 4) + (Carbs × 4) + (Fat × 9) + (Alcohol × 7)
- Account for cooking losses: Oil absorption in frying (~10-25%), water loss in roasting (~20-30%)

REFERENCE VALUES (per 100g or as specified):
Common Vegetables:
- Okra/Bhindi: 33 cal, 1.9g protein, 7.5g carbs, 0.2g fat, 3.2g fiber
- Onion: 40 cal, 1.1g protein, 9.3g carbs, 0.1g fat
- Tomato: 18 cal, 0.9g protein, 3.9g carbs, 0.2g fat
- Spinach: 23 cal, 2.9g protein, 3.6g carbs, 0.4g fat

Oils & Fats (per tablespoon/15ml):
- Vegetable oil: 120 cal, 0g protein, 0g carbs, 14g fat
- Ghee: 112 cal, 0g protein, 0g carbs, 12.7g fat
- Butter: 102 cal, 0.1g protein, 0g carbs, 11.5g fat

Nuts & Seeds (per ounce/28g):
- Peanuts: 161 cal, 7.3g protein, 4.6g carbs, 14g fat
- Cashews: 157 cal, 5.2g protein, 8.6g carbs, 12.4g fat
- Almonds: 164 cal, 6g protein, 6.1g carbs, 14.2g fat

Grains & Legumes (per 100g cooked):
- Rice (white): 130 cal, 2.7g protein, 28.2g carbs, 0.3g fat
- Wheat flour: 364 cal, 10.3g protein, 76.3g carbs, 1g fat
- Lentils (cooked): 116 cal, 9g protein, 20.1g carbs, 0.4g fat

INDIAN INGREDIENT CONVERSIONS:
- Bhindi = Okra
- Hing = Asafoetida (negligible calories in typical amounts)
- Haldi = Turmeric (9 cal per tsp)
- Jeera = Cumin (8 cal per tsp)
- Dhania = Coriander (5 cal per tsp)
- Rai/Sarson = Mustard seeds (20 cal per tsp)

COOKING METHOD ADJUSTMENTS:
- Deep frying: Add 5-10% of oil weight absorbed
- Shallow frying: Add 3-5% of oil used
- Air frying: Add only oil directly used (minimal absorption)
- Roasting: Reduce weight by 20-30% for water loss

For each ingredient in detailed_breakdown, show:
1. The calculation basis (e.g., "Based on USDA data for raw okra")
2. Actual quantities used in calculation
3. Any adjustments made for cooking method

CRITICAL: Return ONLY valid JSON, no additional text or explanations outside the JSON structure
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional nutritionist with expertise in calculating accurate nutritional values for recipes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent calculations
                max_tokens=2500  # Increased for GPT-4's more detailed responses
            )
            
            # Extract JSON from response
            result_text = response.choices[0].message.content
            
            # Log the raw response for debugging
            print(f"GPT-4 Raw Response: {result_text[:500]}...")  # First 500 chars for debugging
            
            # Clean up the text to help with JSON parsing
            result_text = result_text.strip()
            
            # If response starts with markdown code block, extract it
            if result_text.startswith('```json'):
                result_text = result_text[7:]  # Remove ```json
                if '```' in result_text:
                    result_text = result_text[:result_text.index('```')]
            elif result_text.startswith('```'):
                result_text = result_text[3:]  # Remove ```
                if '```' in result_text:
                    result_text = result_text[:result_text.index('```')]
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # Clean up common JSON issues
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                json_str = re.sub(r'"\s*:\s*"([^"]*)"([^,}\]]*)"', r'": "\1\2"', json_str)  # Fix broken strings
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {e}")
                    print(f"Problematic JSON: {json_str[:200]}...")
                    # Try to fix common issues
                    json_str = json_str.replace('\\n', ' ')
                    json_str = re.sub(r'//.*?(?=[\n,}])', '', json_str)  # Remove comments
                    json_str = re.sub(r'\s+', ' ', json_str)  # Normalize whitespace
                    json_str = re.sub(r'"\s*}', '"}', json_str)  # Fix spacing issues
                    json_str = re.sub(r'"\s*]', '"]', json_str)  # Fix spacing issues
                    result = json.loads(json_str)
            else:
                result = json.loads(result_text)
            
            # Ensure all required fields are present
            if 'total' not in result or 'per_serving' not in result:
                raise ValueError("Invalid nutrition data format")
            
            # Round values for cleaner display
            for category in ['total', 'per_serving']:
                if category in result:
                    for key, value in result[category].items():
                        if isinstance(value, (int, float)):
                            result[category][key] = round(value, 1)
            
            return result
            
        except Exception as e:
            print(f"Error in AI nutrition calculation: {e}")
            # Return a basic estimation if AI fails
            raise ValueError(f"Failed to calculate nutrition: {str(e)}")