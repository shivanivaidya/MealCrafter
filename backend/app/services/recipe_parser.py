import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ParsedRecipe:
    title: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    servings: int = 4

class RecipeParser:
    def __init__(self):
        self.ingredient_pattern = re.compile(
            r'(\d+(?:\.\d+)?(?:/\d+)?)\s*([\w\s]+)?\s+(.+)',
            re.IGNORECASE
        )
        
    def parse_recipe_text(self, text: str) -> ParsedRecipe:
        lines = text.strip().split('\n')
        
        title = self._extract_title(lines)
        ingredients_section, instructions_section = self._split_sections(lines)
        
        if not ingredients_section:
            raise ValueError("Could not identify ingredients section. Please ensure ingredients are clearly listed.")
        
        if not instructions_section:
            raise ValueError("Could not identify instructions section. Please ensure cooking steps are included.")
        
        ingredients = self._parse_ingredients(ingredients_section)
        instructions = self._parse_instructions(instructions_section)
        servings = self._extract_servings(text)
        
        return ParsedRecipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            servings=servings
        )
    
    def _extract_title(self, lines: List[str]) -> str:
        for line in lines:
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['ingredients', 'instructions', 'directions', 'method']):
                return line
        return "Untitled Recipe"
    
    def _split_sections(self, lines: List[str]) -> Tuple[List[str], List[str]]:
        ingredients_start = -1
        instructions_start = -1
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(word in line_lower for word in ['ingredient', 'you need', 'you\'ll need']):
                ingredients_start = i + 1
            elif any(word in line_lower for word in ['instruction', 'direction', 'method', 'step']):
                instructions_start = i + 1
                break
        
        if ingredients_start == -1:
            for i, line in enumerate(lines[1:], 1):
                if self._looks_like_ingredient(line):
                    ingredients_start = i
                    break
        
        if instructions_start == -1:
            for i in range(len(lines) - 1, ingredients_start, -1):
                if self._looks_like_instruction(lines[i]):
                    instructions_start = i
                    while instructions_start > ingredients_start and self._looks_like_ingredient(lines[instructions_start - 1]):
                        instructions_start -= 1
                    break
        
        ingredients_section = []
        instructions_section = []
        
        if ingredients_start != -1:
            end = instructions_start if instructions_start != -1 else len(lines)
            ingredients_section = [line for line in lines[ingredients_start:end] if line.strip()]
        
        if instructions_start != -1:
            instructions_section = [line for line in lines[instructions_start:] if line.strip()]
        
        return ingredients_section, instructions_section
    
    def _looks_like_ingredient(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        
        has_number = bool(re.search(r'\d', line))
        has_measurement = any(unit in line.lower() for unit in [
            'cup', 'tbsp', 'tsp', 'oz', 'lb', 'g', 'kg', 'ml', 'l',
            'tablespoon', 'teaspoon', 'ounce', 'pound', 'gram', 'kilogram',
            'milliliter', 'liter', 'pinch', 'dash', 'clove', 'piece'
        ])
        
        return has_number or has_measurement or (len(line.split()) <= 5 and not line.endswith('.'))
    
    def _looks_like_instruction(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        
        instruction_verbs = [
            'heat', 'cook', 'bake', 'fry', 'boil', 'simmer', 'stir', 'mix',
            'combine', 'add', 'pour', 'place', 'put', 'season', 'serve',
            'chop', 'dice', 'slice', 'cut', 'prepare', 'preheat', 'drain',
            'melt', 'whisk', 'blend', 'fold', 'knead', 'roll', 'spread'
        ]
        
        line_lower = line.lower()
        return any(verb in line_lower for verb in instruction_verbs) or line.endswith('.')
    
    def _parse_ingredients(self, lines: List[str]) -> List[Dict[str, Any]]:
        ingredients = []
        
        for line in lines:
            ingredient = self._parse_single_ingredient(line)
            if ingredient:
                ingredients.append(ingredient)
        
        if not ingredients:
            raise ValueError("No valid ingredients found. Please check the format of your ingredients list.")
        
        return ingredients
    
    def _parse_single_ingredient(self, line: str) -> Dict[str, Any]:
        line = line.strip()
        if not line:
            return None
        
        line = re.sub(r'[-•*]', '', line).strip()
        
        quantity_match = re.match(r'^(\d+(?:\.\d+)?(?:/\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*', line)
        quantity = None
        if quantity_match:
            quantity = quantity_match.group(1)
            line = line[quantity_match.end():]
        
        unit = None
        unit_patterns = [
            r'\b(cups?|c\.?)\b', r'\b(tablespoons?|tbsps?|T\.?)\b', r'\b(teaspoons?|tsps?|t\.?)\b',
            r'\b(ounces?|oz\.?)\b', r'\b(pounds?|lbs?\.?)\b', r'\b(grams?|g\.?)\b',
            r'\b(kilograms?|kg\.?)\b', r'\b(milliliters?|ml\.?)\b', r'\b(liters?|l\.?)\b',
            r'\b(pinch(?:es)?)\b', r'\b(dash(?:es)?)\b', r'\b(cloves?)\b', r'\b(pieces?)\b',
            r'\b(cans?)\b', r'\b(packages?|pkgs?\.?)\b', r'\b(bunches?)\b', r'\b(stalks?)\b'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                unit = match.group(1)
                line = line[:match.start()] + line[match.end():]
                break
        
        name = line.strip()
        name = re.sub(r',.*$', '', name).strip()
        
        if not name:
            return None
        
        return {
            "name": name,
            "quantity": quantity,
            "unit": unit
        }
    
    def _parse_instructions(self, lines: List[str]) -> List[str]:
        instructions = []
        current_instruction = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^Step\s+\d+:?\s*', '', line, flags=re.IGNORECASE)
            
            if line.endswith('.') or self._looks_like_instruction(line):
                if current_instruction:
                    current_instruction += " " + line
                    instructions.append(current_instruction.strip())
                    current_instruction = ""
                else:
                    instructions.append(line)
            else:
                current_instruction += " " + line if current_instruction else line
        
        if current_instruction:
            instructions.append(current_instruction.strip())
        
        return instructions if instructions else ["Follow standard cooking procedures for the listed ingredients."]
    
    def _extract_servings(self, text: str) -> int:
        servings_match = re.search(r'(?:serves?|servings?|yield[s]?)[:\s]+(\d+)', text, re.IGNORECASE)
        if servings_match:
            return int(servings_match.group(1))
        return 4