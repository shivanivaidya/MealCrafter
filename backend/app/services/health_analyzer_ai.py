from typing import Dict, List, Any
from openai import OpenAI
from app.core.config import settings
import json
import re
import ast

class AIHealthAnalyzer:
    def __init__(self):
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
    
    def analyze_health(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze recipe health using OpenAI
        """
        if not self.client:
            raise ValueError("OpenAI API key is required for health analysis")
        
        return self._analyze_with_ai(recipe_data)
    
    def _analyze_with_ai(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to provide intelligent health analysis"""
        
        # Prepare recipe information for analysis
        ingredients_text = "\n".join([
            f"- {ing.get('quantity', '')} {ing.get('unit', '')} {ing['name']}"
            for ing in recipe_data.get('ingredients', [])
        ])
        
        instructions_text = "\n".join([
            f"{i+1}. {inst}"
            for i, inst in enumerate(recipe_data.get('instructions', []))
        ])
        
        nutrition = recipe_data.get('nutrition_data', {}).get('per_serving', {})
        nutrition_text = f"""
        Per serving nutrition:
        - Calories: {nutrition.get('calories', 'unknown')}
        - Protein: {nutrition.get('protein', 'unknown')}g
        - Carbs: {nutrition.get('carbs', 'unknown')}g
        - Fat: {nutrition.get('fat', 'unknown')}g
        - Fiber: {nutrition.get('fiber', 'unknown')}g
        - Sodium: {nutrition.get('sodium', 'unknown')}mg
        """
        
        prompt = f"""You are a professional nutritionist analyzing a recipe. Provide a detailed health analysis.

Recipe Ingredients:
{ingredients_text}

Cooking Instructions:
{instructions_text}

{nutrition_text}

Return ONLY valid JSON without any markdown formatting, code blocks, or explanations.
Do not use markdown code blocks (no ```json or ```).
Provide a health analysis with this EXACT JSON structure:
{{
    "score": 7.5,  // Score from 1-10 (can be decimal like 7.5 or 8.5)
    "summary": "Comprehensive 2-3 sentence summary of overall healthiness, nutritional balance, and suitability for common dietary goals",
    "healthy_aspects": [
        {{
            "title": "Bhindi (Okra)",
            "description": "Low in calories (33 cal/100g), high in fiber (3.2g/100g), vitamin C (23mg/100g), and folate. Contains mucilage that helps stabilize blood sugar and improve digestion. Rich in antioxidants including polyphenols and flavonoids"
        }},
        {{
            "title": "Air Frying Method",
            "description": "Reduces oil absorption by 70-80% compared to deep frying while maintaining crispy texture. Preserves heat-sensitive vitamins better than traditional frying"
        }}
    ],
    "watch_points": [
        {{
            "ingredient": "Oil (2 tbsp)",
            "concern": "Adds ~240 calories and 28g fat. While healthy fats are important, this represents 43% of daily fat intake for a 2000-calorie diet"
        }},
        {{
            "ingredient": "Roasted nuts",
            "concern": "Peanuts (160 cal/oz) and cashews (157 cal/oz) are nutrient-dense but calorie-heavy. Combined ~300+ calories could be significant for weight management"
        }}
    ],
    "nutritional_highlights": {{
        "vitamins": ["Vitamin C: 38% DV", "Vitamin K: 45% DV", "Folate: 22% DV", "Vitamin A: 15% DV"],
        "minerals": ["Potassium: 12% DV", "Magnesium: 18% DV", "Calcium: 8% DV", "Iron: 10% DV"],
        "macros": {{
            "protein_quality": "Moderate - contains plant proteins from nuts and legumes. Combine with grains for complete protein",
            "carb_quality": "Good - primarily complex carbs with 7.8g fiber per serving. Low glycemic index",
            "fat_quality": "Good - mix of monounsaturated (from oil) and polyunsaturated fats (from nuts). Omega-6 to Omega-3 ratio could be better"
        }},
        "special_compounds": [
            "Curcumin from turmeric - anti-inflammatory, may reduce arthritis symptoms",
            "Capsaicin from chili - boosts metabolism, may aid weight loss",
            "Quercetin from okra - antioxidant, may reduce inflammation"
        ]
    }},
    "dietary_considerations": {{
        "suitable_for": ["Vegetarian", "Vegan", "Gluten-Free", "Low-Carb", "Anti-Inflammatory"],
        "may_not_suit": ["Nut Allergies", "Low-Fat Diets", "FODMAP-sensitive individuals (due to okra)"],
        "modifications_for_conditions": {{
            "diabetes": "Excellent choice - okra helps regulate blood sugar. Consider reducing oil slightly",
            "heart_disease": "Good option - use heart-healthy oil like olive oil. Nuts provide beneficial fats",
            "weight_loss": "Reduce oil to 1 tbsp and nuts by half to cut 200+ calories",
            "high_cholesterol": "Beneficial - okra's soluble fiber helps lower LDL cholesterol"
        }}
    }},
    "improvement_tips": [
        "Reduce oil to 1 tablespoon to cut 120 calories while maintaining flavor",
        "Add 1 cup cooked quinoa or brown rice for complete protein and sustained energy",
        "Include a cucumber-tomato salad with lemon for vitamin C and hydration",
        "Sprinkle ground flaxseed (1 tbsp) for omega-3 fatty acids",
        "Consider adding chickpeas or tofu for extra protein (especially for athletes)"
    ],
    "meal_pairing_suggestions": [
        "Pair with whole wheat roti (2) for a balanced meal with 15g protein",
        "Serve with dal (lentil curry) for complementary proteins",
        "Add a glass of buttermilk for probiotics and calcium"
    ]
}}

Important guidelines:
- Consider Indian ingredients and their health benefits (turmeric = anti-inflammatory, hing = digestive)
- Account for cooking methods (air frying > deep frying)
- Be specific about calorie counts when mentioning oil or nuts
- Recognize healthy spices and their benefits
- Score should reflect: vegetable content, oil usage, cooking method, nutritional balance
- Scores: 8-10 = very healthy, 6-8 = healthy with minor concerns, 4-6 = moderate, below 4 = needs improvement
- Format all sections with bullet points for consistency
- For Indian recipes, appreciate the use of spices and traditional healthy ingredients
- CRITICAL: improvement_tips MUST be an array of plain strings, NOT objects. Each tip should be a simple string like "Reduce oil to 1 tablespoon"
- CRITICAL: meal_pairing_suggestions MUST be an array of plain strings, NOT objects. Each suggestion should be a simple string like "Pair with whole wheat roti"
- CRITICAL: Return ONLY valid JSON, no additional text or explanations outside the JSON structure
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional nutritionist who understands both Western and Indian cuisine health benefits."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500  # Increased for GPT-4's more detailed responses
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
            
            # Format the breakdown text
            breakdown = self._format_ai_breakdown(result)
            
            return {
                "score": result.get('score', 7),
                "breakdown": breakdown,
                "healthy_points": [f"{asp['title']}: {asp['description']}" 
                                 for asp in result.get('healthy_aspects', [])],
                "watch_points": [f"{wp['ingredient']}: {wp['concern']}" 
                                for wp in result.get('watch_points', [])]
            }
            
        except Exception as e:
            print(f"Error in AI health analysis: {e}")
            raise
    
    def _format_ai_breakdown(self, analysis: Dict[str, Any]) -> str:
        """Format the AI analysis into readable markdown"""
        
        score = analysis.get('score', 7)
        summary = analysis.get('summary', '')
        
        breakdown = f"**Health Score: {score}/10**\n\n"
        
        if summary:
            breakdown += f"📊 **Overview**: {summary}\n\n"
        
        # Nutritional highlights
        nutritional = analysis.get('nutritional_highlights', {})
        if nutritional:
            breakdown += "### 🏆 Nutritional Highlights\n\n"
            
            # Vitamins and minerals
            vitamins = nutritional.get('vitamins', [])
            minerals = nutritional.get('minerals', [])
            if vitamins or minerals:
                breakdown += "**Key Vitamins & Minerals:**\n"
                for v in vitamins[:4]:  # Top 4 vitamins
                    breakdown += f"• {v}\n"
                for m in minerals[:4]:  # Top 4 minerals
                    breakdown += f"• {m}\n"
                breakdown += "\n"
            
            # Macronutrient quality
            macros = nutritional.get('macros', {})
            if macros:
                breakdown += "**Macronutrient Analysis:**\n"
                if macros.get('protein_quality'):
                    breakdown += f"• **Protein**: {macros['protein_quality']}\n"
                if macros.get('carb_quality'):
                    breakdown += f"• **Carbs**: {macros['carb_quality']}\n"
                if macros.get('fat_quality'):
                    breakdown += f"• **Fats**: {macros['fat_quality']}\n"
                breakdown += "\n"
            
            # Special compounds
            compounds = nutritional.get('special_compounds', [])
            if compounds:
                breakdown += "**Beneficial Compounds:**\n"
                for compound in compounds[:3]:  # Top 3 compounds
                    breakdown += f"• {compound}\n"
                breakdown += "\n"
        
        # Healthy aspects
        healthy_aspects = analysis.get('healthy_aspects', [])
        if healthy_aspects:
            breakdown += "### ✅ What Makes It Healthy\n\n"
            for aspect in healthy_aspects:
                breakdown += f"• **{aspect.get('title', '')}**: {aspect.get('description', '')}\n"
            breakdown += "\n"
        
        # Watch points
        watch_points = analysis.get('watch_points', [])
        if watch_points:
            breakdown += "### ⚠️ What to Watch Out For\n\n"
            for point in watch_points:
                breakdown += f"• **{point.get('ingredient', '')}**: {point.get('concern', '')}\n"
            breakdown += "\n"
        
        # Dietary considerations
        dietary = analysis.get('dietary_considerations', {})
        if dietary:
            breakdown += "### 🍽️ Dietary Considerations\n\n"
            
            suitable = dietary.get('suitable_for', [])
            if suitable:
                breakdown += f"**Suitable for:** {', '.join(suitable)}\n\n"
            
            modifications = dietary.get('modifications_for_conditions', {})
            if modifications:
                breakdown += "**Health Condition Recommendations:**\n"
                for condition, advice in list(modifications.items())[:4]:  # Top 4 conditions
                    breakdown += f"• **{condition.title()}**: {advice}\n"
                breakdown += "\n"
        
        # Improvement tips
        tips = analysis.get('improvement_tips', [])
        if tips:
            breakdown += "### 💡 Tips to Make It Healthier\n\n"
            for tip in tips[:5]:  # Top 5 tips
                tip_text = self._extract_text_from_item(tip, ['tip', 'description'])
                if tip_text:
                    breakdown += f"• {tip_text}\n"
            breakdown += "\n"
        
        # Meal pairing suggestions
        pairings = analysis.get('meal_pairing_suggestions', [])
        if pairings:
            breakdown += "### 🥘 Suggested Pairings\n\n"
            for pairing in pairings[:3]:  # Top 3 pairings
                pairing_text = self._extract_text_from_item(pairing, ['suggestion', 'pairing', 'description'])
                if pairing_text:
                    breakdown += f"• {pairing_text}\n"
            breakdown += "\n"
        
        return breakdown
    
    def _extract_text_from_item(self, item: Any, keys: List[str]) -> str:
        """Extract text from an item that could be a string, dict, or string representation of dict"""
        
        # If it's already a clean string
        if isinstance(item, str):
            # Check if it's a string representation of a dictionary
            if item.startswith("{") and item.endswith("}"):
                try:
                    # Try to parse it as a dictionary
                    parsed = ast.literal_eval(item)
                    if isinstance(parsed, dict):
                        # Extract the value from known keys
                        for key in keys:
                            if key in parsed:
                                return str(parsed[key])
                        # If no known key, get the first value
                        if parsed:
                            return str(list(parsed.values())[0])
                except (ValueError, SyntaxError):
                    # If parsing fails, clean up the string manually
                    # Look for patterns like {'tip': 'actual text'}
                    for key in keys:
                        pattern = f"'{key}':\\s*'([^']+)'"
                        match = re.search(pattern, item)
                        if match:
                            return match.group(1)
                    # Fallback: remove dictionary formatting
                    item = re.sub(r"^\{['\"]?\w+['\"]?:\s*['\"]?", "", item)
                    item = re.sub(r"['\"]?\}$", "", item)
                    return item.strip("'\"")
            return item
        
        # If it's a dictionary
        elif isinstance(item, dict):
            # Extract the value from known keys
            for key in keys:
                if key in item:
                    return str(item[key])
            # If no known key, get the first value
            if item:
                return str(list(item.values())[0])
        
        # Fallback to string conversion
        return str(item)
    
    def _basic_analysis(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback basic analysis when AI is not available"""
        
        # Simple scoring based on ingredients
        score = 5.0
        healthy_points = []
        watch_points = []
        
        ingredients = recipe_data.get('ingredients', [])
        for ing in ingredients:
            name = ing.get('name', '').lower()
            
            # Check for vegetables
            if any(veg in name for veg in ['okra', 'bhindi', 'spinach', 'tomato', 'onion']):
                score += 0.5
                healthy_points.append(f"🥬 {ing['name']}: Good source of vitamins and fiber")
            
            # Check for oil
            if 'oil' in name:
                quantity = ing.get('quantity', '1')
                try:
                    if float(quantity) > 1:
                        score -= 0.5
                        watch_points.append(f"Oil ({quantity} {ing.get('unit', '')}): High calorie content")
                except:
                    pass
            
            # Check for nuts
            if any(nut in name for nut in ['peanut', 'cashew', 'almond']):
                healthy_points.append(f"🥜 {ing['name']}: Healthy fats and protein")
        
        # Check cooking method
        instructions_text = ' '.join(recipe_data.get('instructions', [])).lower()
        if 'air fry' in instructions_text or 'air-fry' in instructions_text:
            score += 1
            healthy_points.append("✅ Air frying: Minimal oil cooking method")
        elif 'deep fry' in instructions_text:
            score -= 2
            watch_points.append("Deep frying: High oil absorption")
        
        score = max(1, min(10, score))
        
        breakdown = f"""**Health Score: {score}/10**

### ✅ What Makes It Healthy

"""
        for point in healthy_points:
            breakdown += f"{point}\n\n"
        
        if watch_points:
            breakdown += "### ⚠️ What to Watch Out For\n\n"
            for point in watch_points:
                breakdown += f"{point}\n\n"
        
        breakdown += """### 💡 Tips to Make It Healthier

• Use less oil where possible
• Add more vegetables
• Pair with whole grains
"""
        
        return {
            "score": score,
            "breakdown": breakdown,
            "healthy_points": healthy_points,
            "watch_points": watch_points
        }