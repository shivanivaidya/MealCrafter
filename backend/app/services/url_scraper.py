import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

class URLRecipeScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def scrape_recipe(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape recipe content from a URL
        Returns extracted recipe text or structured data
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find JSON-LD structured data first (most recipe sites use this)
            json_ld = self._extract_json_ld(soup)
            if json_ld:
                return self._parse_json_ld_recipe(json_ld)
            
            # Fallback to manual extraction
            return self._extract_recipe_manually(soup)
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse recipe: {str(e)}")
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON-LD structured data from the page"""
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Handle arrays of JSON-LD objects
                if isinstance(data, list):
                    for item in data:
                        if self._is_recipe_schema(item):
                            return item
                elif self._is_recipe_schema(data):
                    return data
                    
                # Check for @graph structure
                if '@graph' in data:
                    for item in data['@graph']:
                        if self._is_recipe_schema(item):
                            return item
                            
            except json.JSONDecodeError:
                continue
                
        return None
    
    def _is_recipe_schema(self, data: Dict) -> bool:
        """Check if the JSON-LD data is a Recipe schema"""
        if not isinstance(data, dict):
            return False
            
        schema_type = data.get('@type', '')
        if isinstance(schema_type, list):
            return 'Recipe' in schema_type
        return schema_type == 'Recipe'
    
    def _parse_json_ld_recipe(self, data: Dict) -> Dict[str, Any]:
        """Parse Recipe schema.org JSON-LD data"""
        recipe_text = []
        
        # Add title
        title = data.get('name', 'Untitled Recipe')
        recipe_text.append(f"# {title}\n")
        
        # Extract image URL
        image_url = None
        if 'image' in data:
            image_data = data['image']
            if isinstance(image_data, str):
                image_url = image_data
            elif isinstance(image_data, dict):
                image_url = image_data.get('url') or image_data.get('@url')
            elif isinstance(image_data, list) and image_data:
                # Take the first image if it's a list
                first_image = image_data[0]
                if isinstance(first_image, str):
                    image_url = first_image
                elif isinstance(first_image, dict):
                    image_url = first_image.get('url') or first_image.get('@url')
        
        # Add description
        if 'description' in data:
            recipe_text.append(f"{data['description']}\n")
        
        # Add yield/servings
        if 'recipeYield' in data:
            yield_value = data['recipeYield']
            if isinstance(yield_value, list):
                yield_value = yield_value[0]
            recipe_text.append(f"Servings: {yield_value}\n")
        
        # Add prep/cook time
        if 'prepTime' in data:
            prep_time = self._parse_duration(data['prepTime'])
            recipe_text.append(f"Prep Time: {prep_time}")
        
        if 'cookTime' in data:
            cook_time = self._parse_duration(data['cookTime'])
            recipe_text.append(f"Cook Time: {cook_time}")
        
        if 'totalTime' in data:
            total_time = self._parse_duration(data['totalTime'])
            recipe_text.append(f"Total Time: {total_time}")
        
        recipe_text.append("")  # Empty line
        
        # Add ingredients
        recipe_text.append("## Ingredients:\n")
        ingredients = data.get('recipeIngredient', [])
        for ingredient in ingredients:
            # Clean up ingredient text
            ingredient = re.sub(r'<[^>]+>', '', str(ingredient))  # Remove HTML tags
            ingredient = ingredient.strip()
            if ingredient:
                recipe_text.append(f"- {ingredient}")
        
        recipe_text.append("")  # Empty line
        
        # Add instructions
        recipe_text.append("## Instructions:\n")
        instructions = data.get('recipeInstructions', [])
        
        for i, instruction in enumerate(instructions, 1):
            instruction_text = ""
            
            if isinstance(instruction, dict):
                # HowToStep format
                if 'text' in instruction:
                    instruction_text = instruction['text']
                elif 'name' in instruction:
                    instruction_text = instruction['name']
            else:
                # Plain text format
                instruction_text = str(instruction)
            
            # Clean up instruction text
            instruction_text = re.sub(r'<[^>]+>', '', instruction_text)  # Remove HTML tags
            instruction_text = instruction_text.strip()
            
            if instruction_text:
                recipe_text.append(f"{i}. {instruction_text}")
        
        # Add nutrition info if available
        if 'nutrition' in data:
            nutrition = data['nutrition']
            recipe_text.append("\n## Nutrition Information:\n")
            
            if 'calories' in nutrition:
                calories = nutrition['calories']
                if isinstance(calories, str):
                    calories = re.sub(r'[^\d]', '', calories)
                recipe_text.append(f"- Calories: {calories}")
            
            # Add other nutrition facts
            nutrition_mapping = {
                'proteinContent': 'Protein',
                'carbohydrateContent': 'Carbohydrates',
                'fatContent': 'Fat',
                'fiberContent': 'Fiber',
                'sugarContent': 'Sugar',
                'sodiumContent': 'Sodium'
            }
            
            for key, label in nutrition_mapping.items():
                if key in nutrition:
                    value = nutrition[key]
                    if isinstance(value, str):
                        value = re.sub(r'[^\d.]', '', value)
                    recipe_text.append(f"- {label}: {value}g")
        
        # Join all text
        full_text = "\n".join(recipe_text)
        
        return {
            "source": "url",
            "url": data.get('url', ''),
            "text": full_text,
            "image_url": image_url,
            "structured_data": {
                "title": title,
                "ingredients": ingredients,
                "instructions": [inst.get('text', inst) if isinstance(inst, dict) else str(inst) 
                               for inst in instructions],
                "servings": data.get('recipeYield'),
                "nutrition": data.get('nutrition', {})
            }
        }
    
    def _extract_recipe_manually(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Fallback method to extract recipe manually from HTML"""
        recipe_text = []
        extracted_title = None
        image_url = None
        
        # Try to find recipe image
        for selector in [
            'img[itemprop="image"]',
            'img.recipe-image',
            'img.recipe-photo',
            '[class*="recipe"] img',
            'article img',
            'main img'
        ]:
            img_elem = soup.select_one(selector)
            if img_elem:
                # Get the image URL from various possible attributes
                image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                if image_url:
                    # Make sure it's an absolute URL
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        # Need to get the base URL from the page
                        canonical = soup.find('link', {'rel': 'canonical'})
                        if canonical and canonical.get('href'):
                            from urllib.parse import urljoin
                            base_url = canonical['href']
                            image_url = urljoin(base_url, image_url)
                    break
        
        # Try Open Graph image as fallback
        if not image_url:
            og_image = soup.find('meta', {'property': 'og:image'})
            if og_image and og_image.get('content'):
                image_url = og_image['content']
        
        # Try to find the title
        title = None
        for selector in ['h1.recipe-name', 'h1.recipe-title', 'h1[itemprop="name"]', 'h1']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                extracted_title = title
                recipe_text.append(f"# {title}\n")
                break
        
        if not title:
            title = soup.find('title')
            if title:
                title = title.get_text(strip=True)
                # Clean common suffixes from page titles
                title = re.sub(r'\s*[\|\-–]\s*.*$', '', title)  # Remove site name after | or -
                extracted_title = title
                recipe_text.append(f"# {title}\n")
        
        # Look for ingredients
        ingredients_found = False
        for selector in [
            '[class*="ingredient"]',
            '[itemprop="recipeIngredient"]',
            '.recipe-ingredient',
            '.ingredient-list li',
            'ul.ingredients li'
        ]:
            ingredients = soup.select(selector)
            if ingredients:
                recipe_text.append("## Ingredients:\n")
                for ing in ingredients:
                    text = ing.get_text(strip=True)
                    if text:
                        recipe_text.append(f"- {text}")
                ingredients_found = True
                break
        
        # If no ingredients found with selectors, look for text patterns
        if not ingredients_found:
            # Look for "Ingredients" heading and its list
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'ingredient' in heading.get_text().lower():
                    next_elem = heading.find_next_sibling()
                    if next_elem and next_elem.name in ['ul', 'ol']:
                        recipe_text.append("## Ingredients:\n")
                        for li in next_elem.find_all('li'):
                            text = li.get_text(strip=True)
                            if text:
                                recipe_text.append(f"- {text}")
                        break
        
        recipe_text.append("")  # Empty line
        
        # Look for instructions
        instructions_found = False
        for selector in [
            '[class*="instruction"]',
            '[class*="direction"]',
            '[itemprop="recipeInstructions"]',
            '.recipe-instruction',
            '.directions li',
            'ol.instructions li'
        ]:
            instructions = soup.select(selector)
            if instructions:
                recipe_text.append("## Instructions:\n")
                for i, inst in enumerate(instructions, 1):
                    text = inst.get_text(strip=True)
                    if text:
                        recipe_text.append(f"{i}. {text}")
                instructions_found = True
                break
        
        # If no instructions found with selectors, look for text patterns
        if not instructions_found:
            # Look for "Instructions" or "Directions" heading
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                heading_text = heading.get_text().lower()
                if 'instruction' in heading_text or 'direction' in heading_text or 'method' in heading_text:
                    next_elem = heading.find_next_sibling()
                    if next_elem and next_elem.name in ['ul', 'ol']:
                        recipe_text.append("## Instructions:\n")
                        for i, li in enumerate(next_elem.find_all('li'), 1):
                            text = li.get_text(strip=True)
                            if text:
                                recipe_text.append(f"{i}. {text}")
                        break
                    elif next_elem and next_elem.name == 'div':
                        # Sometimes instructions are in divs
                        recipe_text.append("## Instructions:\n")
                        paragraphs = next_elem.find_all(['p', 'div'])
                        for i, p in enumerate(paragraphs, 1):
                            text = p.get_text(strip=True)
                            if text and len(text) > 10:
                                recipe_text.append(f"{i}. {text}")
                        break
        
        # Get all text if structured extraction failed
        if len(recipe_text) < 5:
            # Fall back to extracting all meaningful text
            recipe_text = ["# Recipe from URL\n"]
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                # Extract paragraphs and lists
                for elem in main_content.find_all(['p', 'li', 'h2', 'h3']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10:
                        if elem.name in ['h2', 'h3']:
                            recipe_text.append(f"\n## {text}\n")
                        elif elem.name == 'li':
                            recipe_text.append(f"- {text}")
                        else:
                            recipe_text.append(text)
        
        full_text = "\n".join(recipe_text)
        
        return {
            "source": "url",
            "url": soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else '',
            "text": full_text,
            "image_url": image_url,
            "structured_data": {
                "title": extracted_title
            } if extracted_title else None
        }
    
    def _parse_duration(self, duration: str) -> str:
        """Parse ISO 8601 duration to readable format"""
        if not duration or not isinstance(duration, str):
            return str(duration)
        
        # Parse ISO 8601 duration (e.g., PT30M)
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration)
        if match:
            hours = match.group(1)
            minutes = match.group(2)
            
            parts = []
            if hours:
                parts.append(f"{hours} hour{'s' if int(hours) > 1 else ''}")
            if minutes:
                parts.append(f"{minutes} minute{'s' if int(minutes) > 1 else ''}")
            
            return " ".join(parts)
        
        return duration