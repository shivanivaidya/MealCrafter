import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI
from app.core.config import settings

@dataclass
class ParsedRecipe:
    title: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    servings: int = 4
    cuisine_type: Optional[str] = None
    dietary_tags: Optional[List[str]] = None

class AIRecipeParser:
    def __init__(self):
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            
    def parse_recipe_text(self, text: str) -> ParsedRecipe:
        """Parse recipe using OpenAI API"""
        
        if not self.client:
            raise ValueError("OpenAI API key is required for recipe parsing")
        
        return self._parse_with_ai(text)
    
    def _parse_with_ai(self, text: str) -> ParsedRecipe:
        """Use OpenAI to intelligently parse the recipe"""
        
        prompt = """You are a recipe parser. Extract the recipe information from the following text.
        
        The recipe might have ingredients and instructions mixed together (like "Add 2 cups flour") 
        or separated into sections. Handle both formats.
        
        Return ONLY valid JSON without any markdown formatting, code blocks, or explanations.
        Do not use markdown code blocks (no ```json or ```).
        Return a JSON object with this exact structure:
        {
            "title": "Recipe title",
            "ingredients": [
                {"name": "ingredient name", "quantity": "2", "unit": "cups"},
                {"name": "salt", "quantity": "to taste", "unit": null}
            ],
            "instructions": [
                "Step 1 instruction",
                "Step 2 instruction"
            ],
            "servings": 4,
            "cuisine_type": "Italian",
            "dietary_tags": ["Vegetarian", "Gluten-Free"]
        }
        
        Important:
        - Extract ALL ingredients mentioned, even if mixed within instructions
        - Combine duplicate ingredients (e.g., if oil is mentioned twice, sum the quantities)
        - Default servings to 4 if not specified
        - For ingredients like "salt to taste", use quantity: "to taste" and unit: null
        - Clean ingredient names (remove preparation notes like "chopped", "diced")
        
        CRITICAL - Indian Ingredient Translation and Formatting:
        - For Indian/regional ingredients, ALWAYS include English translation in parentheses
        - Use lowercase for ingredient names (except proper nouns) for consistency
        - Common translations (ALWAYS apply these):
          * "bhindi" → "bhindi (okra)"
          * "hing" → "hing (asafoetida)"
          * "kadi patta" or "curry patta" → "curry leaves"
          * "urad dal" or "udit dal" or "urad daal" → "urad dal (split black gram)"
          * "khadi mirchi" or "red mirchi" or "lal mirchi" → "red chili peppers (dried)"
          * "hari mirchi" or "green mirchi" → "green chili peppers"
          * "jeera" → "jeera (cumin seeds)"
          * "haldi" → "haldi (turmeric powder)"
          * "dhania" → "dhania (coriander)"
          * "methi" → "methi (fenugreek)"
          * "garam masala" → "garam masala (Indian spice blend)"
          * "chana dal" → "chana dal (split chickpeas)"
          * "moong dal" → "moong dal (split mung beans)"
        - If the ingredient is already in English, don't add translation
        - Keep the original name first, then English in parentheses
        - Use proper capitalization: lowercase for common ingredients
        
        INSTRUCTIONS - Improve Clarity:
        - Rephrase instructions to be clear, professional cooking steps
        - Keep the same meaning but improve grammar and flow
        - Use standard cooking terminology
        - Number each step clearly
        - Make instructions concise but complete
        - Example: "Add and mix 1 tbsp oil with Bhindi" → "Toss the okra with 1 tablespoon of oil until well coated"
        - Example: "Fry until golden brown" → "Sauté until the onions turn golden brown"
        
        CUISINE DETECTION:
        - Identify the cuisine type based on ingredients, cooking methods, and dish name
        - Choose ONE from: Italian, Chinese, Indian, Mexican, Japanese, Thai, French, Mediterranean, American, Korean, Vietnamese, Greek, Spanish, Middle Eastern, African
        - If uncertain or fusion, choose the most dominant influence
        - Examples:
          * Pasta, tomato sauce, basil, parmesan → Italian
          * Curry leaves, turmeric, dal, chapati → Indian
          * Soy sauce, ginger, stir-fry, rice → Chinese
          * Tortillas, salsa, beans, cilantro → Mexican
        
        DIETARY TAG DETECTION:
        - Analyze ingredients to automatically detect ALL applicable dietary tags:
        - Vegetarian: No meat, poultry, or fish (eggs and dairy OK)
        - Vegan: No animal products at all (no meat, dairy, eggs, honey)
        - Gluten-Free: No wheat, barley, rye, or their derivatives
        - Dairy-Free: No milk, cheese, butter, yogurt, cream
        - Keto: Very low carb (no grains, sugar, most fruits), high fat
        - Paleo: No grains, legumes, dairy, refined sugar
        - Low-Carb: Limited bread, pasta, rice, sugar
        - High-Protein: Emphasizes meat, eggs, legumes, protein sources
        - Nut-Free: No tree nuts or peanuts
        - Egg-Free: No eggs or egg products
        - Sugar-Free: No added sugars or sweeteners
        - Low-Sodium: Minimal salt, no high-sodium ingredients
        - Pescatarian: Vegetarian plus fish/seafood
        
        Be thorough - include ALL tags that apply. For example:
        - A salad with just vegetables → ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free", "Egg-Free", "Low-Carb"]
        - Grilled chicken with vegetables → ["Gluten-Free", "Dairy-Free", "Low-Carb", "High-Protein"]
        
        CRITICAL: Return ONLY valid JSON, no additional text or explanations outside the JSON structure.
        
        Recipe text:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful recipe parser that extracts structured data from recipe text."},
                    {"role": "user", "content": prompt + text}
                ],
                temperature=0.3,
                max_tokens=3000  # Increased for GPT-4's more detailed responses
            )
            
            # Extract JSON from response
            result_text = response.choices[0].message.content
            
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
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to fix common issues
                    json_str = json_str.replace('\\n', ' ')
                    json_str = re.sub(r'//.*', '', json_str)  # Remove comments
                    result = json.loads(json_str)
            else:
                result = json.loads(result_text)
            
            # Validate and clean the result
            ingredients = result.get('ingredients', [])
            instructions = result.get('instructions', [])
            
            # Ensure proper structure for ingredients
            cleaned_ingredients = []
            for ing in ingredients:
                if isinstance(ing, dict):
                    cleaned_ingredients.append({
                        "name": ing.get('name', ''),
                        "quantity": ing.get('quantity'),
                        "unit": ing.get('unit')
                    })
            
            return ParsedRecipe(
                title=result.get('title', 'Untitled Recipe'),
                ingredients=cleaned_ingredients,
                instructions=instructions,
                servings=result.get('servings', 4),
                cuisine_type=result.get('cuisine_type'),
                dietary_tags=result.get('dietary_tags', [])
            )
            
        except Exception as e:
            print(f"Error parsing with AI: {e}")
            raise
    
    def _parse_basic(self, text: str) -> ParsedRecipe:
        """Basic fallback parser for when AI is not available"""
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        # Extract title (first non-bullet line)
        title = "Untitled Recipe"
        for line in lines:
            if not line.startswith('-') and not line.startswith('•') and not line.startswith('⁃'):
                title = line
                break
        
        # Simple extraction of ingredients and instructions
        all_ingredients = {}
        instructions = []
        
        # Common ingredient patterns
        ingredient_pattern = re.compile(
            r'(\d+(?:\.\d+)?(?:/\d+)?)\s*'
            r'(cups?|tbsps?|tsps?|lbs?|oz|g|kg|ml|l|tablespoons?|teaspoons?|pounds?|ounces?)?\s*'
            r'([a-zA-Z][^,\.\n]+)',
            re.IGNORECASE
        )
        
        for line in lines:
            # Clean line
            clean_line = re.sub(r'^[-•⁃*]\s*', '', line).strip()
            
            # Look for ingredients
            found_ingredient = False
            for match in ingredient_pattern.finditer(clean_line):
                quantity = match.group(1)
                unit = match.group(2) if match.group(2) else None
                name = match.group(3).strip()
                
                # Clean name
                name = re.sub(r'\b(chopped|diced|sliced|minced|crushed|ground)\b', '', name, re.IGNORECASE).strip()
                
                if len(name) > 2 and len(name.split()) <= 5:
                    key = name.lower()
                    if key not in all_ingredients:
                        all_ingredients[key] = {
                            "name": name,
                            "quantity": quantity,
                            "unit": unit
                        }
                    found_ingredient = True
            
            # Check for "to taste" ingredients
            taste_match = re.search(r'([a-zA-Z][a-zA-Z\s]+)\s+to\s+taste', clean_line, re.IGNORECASE)
            if taste_match:
                name = taste_match.group(1).strip()
                key = name.lower()
                if key not in all_ingredients:
                    all_ingredients[key] = {
                        "name": name,
                        "quantity": "to taste",
                        "unit": None
                    }
                found_ingredient = True
            
            # Add as instruction if it contains action words or if we found ingredients
            if clean_line and clean_line != title:
                instructions.append(clean_line)
        
        ingredients_list = list(all_ingredients.values())
        
        if not ingredients_list:
            raise ValueError("Could not extract ingredients. Please ensure recipe includes quantities and ingredient names.")
        
        return ParsedRecipe(
            title=title,
            ingredients=ingredients_list,
            instructions=instructions,
            servings=4
        )