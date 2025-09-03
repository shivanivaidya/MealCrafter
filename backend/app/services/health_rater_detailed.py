from typing import Dict, List, Any, Tuple
import re

class DetailedHealthRater:
    def __init__(self):
        self.healthy_ingredients = {
            # Vegetables
            'okra': (2, '🥬 Low in calories, high in fiber, vitamin C, and folate. Good for digestion and blood sugar stability'),
            'bhindi': (2, '🥬 Low in calories, high in fiber, vitamin C, and folate. Good for digestion and blood sugar stability'),
            'spinach': (2.5, '🥬 Packed with iron, vitamins A, C, K, and antioxidants'),
            'kale': (2.5, '🥬 Nutrient powerhouse with vitamins A, C, K, calcium'),
            'broccoli': (2, '🥦 High in fiber, vitamin C, and cancer-fighting compounds'),
            'carrot': (1.5, '🥕 Rich in beta-carotene and fiber'),
            'tomato': (1.5, '🍅 Contains lycopene, vitamin C, potassium'),
            'onion': (1, '🧅 Adds prebiotic fiber and flavor without high calories'),
            'garlic': (1.5, '🧄 Anti-inflammatory and immune-boosting properties'),
            'ginger': (1.5, '🫚 Anti-inflammatory and digestive benefits'),
            
            # Proteins
            'dal': (2, '🌱 Plant-based protein, high in fiber and minerals'),
            'lentil': (2, '🌱 Excellent source of plant protein and iron'),
            'paneer': (1, '🧀 Good protein source but high in saturated fat'),
            'chicken': (1.5, '🍗 Lean protein when grilled or baked'),
            'fish': (2, '🐟 Rich in omega-3 fatty acids and lean protein'),
            'egg': (1.5, '🥚 Complete protein with essential nutrients'),
            
            # Nuts and Seeds
            'peanut': (1.5, '🥜 Healthy fats, protein, and satiety-boosting'),
            'cashew': (1.5, '🥜 Good fats and minerals but calorie-dense'),
            'almond': (2, '🥜 Heart-healthy fats, vitamin E, and protein'),
            
            # Spices and Herbs
            'turmeric': (2, '🌿 Powerful anti-inflammatory properties'),
            'haldi': (2, '🌿 Powerful anti-inflammatory properties'),
            'cumin': (1.5, '🌿 Aids digestion and metabolism'),
            'jeera': (1.5, '🌿 Aids digestion and metabolism'),
            'coriander': (1, '🌿 Rich in antioxidants'),
            'dhania': (1, '🌿 Rich in antioxidants'),
            'asafoetida': (1.5, '🌿 Excellent for digestion'),
            'hing': (1.5, '🌿 Excellent for digestion'),
            'curry leaves': (1.5, '🍃 Anti-inflammatory and digestive benefits'),
            'mustard': (1, '🌿 Metabolism booster'),
            'chili': (1, '🌶️ Metabolism booster, vitamin C'),
            'mirchi': (1, '🌶️ Metabolism booster, vitamin C'),
        }
        
        self.unhealthy_aspects = {
            'oil': (-0.5, '🛢️ Adds calories - each tbsp adds ~120 calories'),
            'butter': (-1, '🧈 High in saturated fat'),
            'ghee': (-0.5, '🧈 High in calories but has some benefits'),
            'sugar': (-2, '🍬 Empty calories, blood sugar spikes'),
            'cream': (-1.5, '🥛 High in saturated fat and calories'),
            'mayo': (-1.5, '🥫 Very high in calories and processed'),
            'fried': (-2, '🍳 Significantly increases calorie content'),
            'deep-fried': (-3, '🍳 Very high in unhealthy fats'),
        }
        
        self.cooking_methods = {
            'air fry': (1.5, '✅ Uses minimal oil while achieving crispy texture'),
            'air-fry': (1.5, '✅ Uses minimal oil while achieving crispy texture'),
            'steam': (2, '✅ Preserves nutrients without added fats'),
            'grill': (1.5, '✅ Allows fat to drip away'),
            'bake': (1, '✅ No added oil needed'),
            'boil': (1, '✅ No added fats'),
            'saute': (0, '⚠️ Moderate oil use'),
            'fry': (-1, '⚠️ Requires significant oil'),
            'deep fry': (-2, '❌ Very high oil absorption'),
        }
    
    def rate_health_detailed(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns detailed health rating with breakdown
        """
        ingredients = recipe_data.get('ingredients', [])
        instructions = recipe_data.get('instructions', [])
        nutrition = recipe_data.get('nutrition_data', {})
        
        # Calculate base score
        base_score = 5.0
        healthy_points = []
        watch_points = []
        
        # Analyze ingredients
        ingredient_scores = self._analyze_ingredients(ingredients)
        for score, reason in ingredient_scores['healthy']:
            base_score += score
            healthy_points.append(reason)
        
        for score, reason in ingredient_scores['unhealthy']:
            base_score += score  # score is negative
            watch_points.append(reason)
        
        # Analyze cooking methods
        cooking_scores = self._analyze_cooking_methods(instructions)
        for score, reason in cooking_scores['healthy']:
            base_score += score
            healthy_points.append(reason)
        
        for score, reason in cooking_scores['unhealthy']:
            base_score += score
            watch_points.append(reason)
        
        # Analyze nutrition
        nutrition_analysis = self._analyze_nutrition(nutrition)
        if nutrition_analysis['concerns']:
            watch_points.extend(nutrition_analysis['concerns'])
            base_score -= len(nutrition_analysis['concerns']) * 0.5
        
        # Check for missing components
        missing = self._check_missing_components(ingredients)
        if missing:
            watch_points.append(f"📝 Could be more complete with: {', '.join(missing)}")
            base_score -= 0.5
        
        # Calculate final score
        final_score = max(1.0, min(10.0, base_score))
        
        # Format the breakdown
        breakdown = self._format_breakdown(final_score, healthy_points, watch_points, ingredients)
        
        return {
            "score": round(final_score, 1),
            "breakdown": breakdown,
            "healthy_points": healthy_points,
            "watch_points": watch_points
        }
    
    def _analyze_ingredients(self, ingredients: List[Dict[str, Any]]) -> Dict[str, List[Tuple[float, str]]]:
        healthy = []
        unhealthy = []
        oil_count = 0
        nut_calories = 0
        
        for ingredient in ingredients:
            name = ingredient.get('name', '').lower()
            quantity = self._parse_quantity(ingredient.get('quantity', '1'))
            unit = (ingredient.get('unit', '') or '').lower()
            
            # Extract English name if translation exists
            if '(' in name and ')' in name:
                english_name = name[name.index('(')+1:name.index(')')].strip()
                check_name = english_name
            else:
                check_name = name
            
            # Check healthy ingredients
            for key, (score, desc) in self.healthy_ingredients.items():
                if key in check_name:
                    if (key, desc) not in [(h[1].split(' ')[0], h[1]) for h in healthy]:
                        healthy.append((score, desc))
                    break
            
            # Check unhealthy aspects
            for key, (score, desc) in self.unhealthy_aspects.items():
                if key in check_name:
                    # Track oil usage
                    if 'oil' in key:
                        oil_count += quantity
                        if unit in ['tbsp', 'tablespoon']:
                            calories = quantity * 120
                            unhealthy.append((score, f"{desc} ({quantity} {unit} = ~{int(calories)} calories)"))
                    else:
                        unhealthy.append((score, desc))
                    break
            
            # Track nuts
            if any(nut in check_name for nut in ['peanut', 'cashew', 'almond', 'nut']):
                if unit in ['cup', 'cups']:
                    nut_calories += quantity * 800
                elif unit in ['tbsp', 'tablespoon']:
                    nut_calories += quantity * 50
                else:
                    nut_calories += quantity * 160
        
        if nut_calories > 200:
            unhealthy.append((-0.5, f"🥜 Nuts are healthy but calorie-dense (~{int(nut_calories)} calories total)"))
        
        return {"healthy": healthy, "unhealthy": unhealthy}
    
    def _analyze_cooking_methods(self, instructions: List[str]) -> Dict[str, List[Tuple[float, str]]]:
        healthy = []
        unhealthy = []
        all_instructions = ' '.join(instructions).lower()
        
        for method, (score, desc) in self.cooking_methods.items():
            if method in all_instructions:
                if score > 0:
                    healthy.append((score, desc))
                else:
                    unhealthy.append((score, desc))
        
        return {"healthy": healthy, "unhealthy": unhealthy}
    
    def _analyze_nutrition(self, nutrition: Dict[str, Any]) -> Dict[str, List[str]]:
        concerns = []
        
        if nutrition and 'per_serving' in nutrition:
            per_serving = nutrition['per_serving']
            
            # Check calories
            calories = per_serving.get('calories', 0)
            if calories > 800:
                concerns.append(f"⚠️ High calories per serving ({calories})")
            
            # Check sodium
            sodium = per_serving.get('sodium', 0)
            if sodium > 1000:
                concerns.append(f"⚠️ High sodium ({sodium}mg per serving)")
            
            # Check sugar
            sugar = per_serving.get('sugar', 0)
            if sugar > 25:
                concerns.append(f"⚠️ High sugar content ({sugar}g per serving)")
        
        return {"concerns": concerns}
    
    def _check_missing_components(self, ingredients: List[Dict[str, Any]]) -> List[str]:
        missing = []
        all_ingredients = ' '.join([ing.get('name', '').lower() for ing in ingredients])
        
        # Check for whole grains
        if not any(grain in all_ingredients for grain in ['rice', 'roti', 'bread', 'quinoa', 'wheat']):
            missing.append("whole grains (roti, rice)")
        
        # Check for greens
        if not any(green in all_ingredients for green in ['spinach', 'kale', 'lettuce', 'methi', 'palak']):
            missing.append("leafy greens")
        
        return missing
    
    def _format_breakdown(self, score: float, healthy: List[str], watch: List[str], ingredients: List[Dict]) -> str:
        breakdown = f"**Health Score: {score}/10**\n\n"
        
        if score >= 8:
            breakdown += "This is a very healthy recipe! "
        elif score >= 6:
            breakdown += "This recipe has good nutritional value with some areas to watch. "
        elif score >= 4:
            breakdown += "This recipe is moderately healthy but could be improved. "
        else:
            breakdown += "This recipe needs significant improvements for better health. "
        
        breakdown += "Here's the detailed breakdown:\n\n"
        
        if healthy:
            breakdown += "### ✅ What Makes It Healthy\n\n"
            # Group similar items
            seen = set()
            for point in healthy:
                if point not in seen:
                    breakdown += f"{point}\n\n"
                    seen.add(point)
        
        if watch:
            breakdown += "### ⚠️ What to Watch Out For\n\n"
            for point in watch:
                breakdown += f"{point}\n\n"
        
        # Add suggestions
        breakdown += "### 💡 Tips to Make It Healthier\n\n"
        if any('oil' in w.lower() for w in watch):
            breakdown += "• Consider reducing oil or using cooking spray\n"
        if any('fry' in w.lower() for w in watch):
            breakdown += "• Try baking or air-frying instead of deep frying\n"
        if 'whole grains' in ' '.join(watch).lower():
            breakdown += "• Pair with brown rice or whole wheat roti\n"
        if 'leafy greens' in ' '.join(watch).lower():
            breakdown += "• Add a side salad or sautéed greens\n"
        
        return breakdown
    
    def _parse_quantity(self, quantity_str: str) -> float:
        if not quantity_str or quantity_str == "to taste":
            return 0.5
        
        try:
            quantity_str = str(quantity_str).strip()
            if '/' in quantity_str:
                parts = quantity_str.split('/')
                return float(parts[0]) / float(parts[1])
            elif '-' in quantity_str:
                parts = quantity_str.split('-')
                return (float(parts[0]) + float(parts[1])) / 2
            else:
                return float(quantity_str)
        except:
            return 1