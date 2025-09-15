"""
Food Image Search Service
Searches for and caches real food images from various sources
"""
import logging
import requests
from typing import Optional, List
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class FoodImageSearch:
    """Search for real food images from various sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Cache to avoid repeated searches
        self.image_cache = {}
    
    def search_food_image(self, recipe_name: str) -> Optional[str]:
        """
        Search for a food image based on recipe name
        Returns the first high-quality food image URL found
        """
        # Check cache first
        if recipe_name in self.image_cache:
            logger.info(f"Using cached image for: {recipe_name}")
            return self.image_cache[recipe_name]
        
        # Try multiple search strategies
        image_url = None
        
        # Strategy 1: Search Google Images (using a scraping-friendly approach)
        image_url = self._search_google_images(recipe_name)
        
        # Strategy 2: Search recipe websites directly
        if not image_url:
            image_url = self._search_recipe_sites(recipe_name)
        
        # Strategy 3: Search Pexels (free stock photos)
        if not image_url:
            image_url = self._search_pexels(recipe_name)
        
        # Cache the result
        if image_url:
            self.image_cache[recipe_name] = image_url
            logger.info(f"Found image for {recipe_name}: {image_url}")
        else:
            logger.warning(f"No image found for {recipe_name}")
        
        return image_url
    
    def _search_google_images(self, query: str) -> Optional[str]:
        """Search Google Images for food photos"""
        try:
            # Use Google's image search with specific parameters for high-res food images
            search_query = f"{query} recipe food high resolution"
            # Add size parameter for large images
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&tbm=isch&tbs=isz:l,itp:photo"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code != 200:
                return None
            
            # Parse the HTML to find image URLs
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for high-res image URLs
            # Google embeds multiple versions - we want the highest quality
            high_res_patterns = [
                r'https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*(?:maxwidth=\d{4,}|size=\d{4,}|=s0)',
                r'https?://[^"]+\.(?:jpg|jpeg|png|webp)(?:\?[^"]*)?'
            ]
            
            scripts = soup.find_all('script')
            best_urls = []
            
            for script in scripts:
                if script.string:
                    for pattern in high_res_patterns:
                        urls = re.findall(pattern, script.string)
                        for url in urls:
                            # Skip thumbnails and small images
                            if any(skip in url.lower() for skip in ['thumb', '=s90', '=s180', '=s360', 'small', 'tiny']):
                                continue
                            # Prefer larger images
                            if any(large in url for large in ['=s0', '=s1600', '=s1200', '=s1000', 'original', 'large', 'full']):
                                best_urls.insert(0, url)  # Priority
                            else:
                                best_urls.append(url)
            
            # Return the best URL found
            for url in best_urls:
                if self._validate_image_url(url):
                    logger.info(f"Found high-res Google image: {url[:100]}...")
                    return url
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Google Images: {str(e)}")
            return None
    
    def _search_recipe_sites(self, query: str) -> Optional[str]:
        """Search popular recipe sites for images"""
        recipe_sites = [
            {
                'name': 'AllRecipes',
                'search_url': f'https://www.allrecipes.com/search?q={quote_plus(query)}',
                'image_selector': 'img.card__img'
            },
            {
                'name': 'FoodNetwork',
                'search_url': f'https://www.foodnetwork.com/search/{quote_plus(query)}-',
                'image_selector': 'img.m-MediaBlock__a-Image'
            },
            {
                'name': 'Epicurious',
                'search_url': f'https://www.epicurious.com/search?q={quote_plus(query)}',
                'image_selector': 'img.photo'
            }
        ]
        
        for site in recipe_sites:
            try:
                response = requests.get(site['search_url'], headers=self.headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find recipe images
                    images = soup.select(site['image_selector'])
                    for img in images:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            # Make URL absolute if needed
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                base_url = '/'.join(site['search_url'].split('/')[:3])
                                img_url = base_url + img_url
                            
                            if self._validate_image_url(img_url):
                                logger.info(f"Found image on {site['name']}")
                                return img_url
                                
            except Exception as e:
                logger.warning(f"Error searching {site['name']}: {str(e)}")
                continue
        
        return None
    
    def _search_pexels(self, query: str) -> Optional[str]:
        """Search Pexels for free stock food photos"""
        try:
            # Pexels provides free stock photos in high resolution
            search_url = f"https://www.pexels.com/search/{quote_plus(query + ' food')}/"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for high-res image URLs in various places
                # Pexels provides multiple resolutions
                image_sources = []
                
                # Try to find the highest quality version
                # Look in img tags with various data attributes
                for img in soup.find_all('img'):
                    # Pexels uses data attributes for lazy loading high-res versions
                    for attr in ['data-big-src', 'data-large-src', 'data-large2x-src', 'srcset']:
                        img_url = img.get(attr)
                        if img_url:
                            # Extract the highest resolution from srcset if present
                            if attr == 'srcset':
                                # Parse srcset to get the highest resolution
                                urls = img_url.split(',')
                                for url_part in urls:
                                    url_part = url_part.strip()
                                    if '2x' in url_part or 'large' in url_part:
                                        url = url_part.split(' ')[0]
                                        image_sources.append(url)
                            else:
                                image_sources.append(img_url)
                    
                    # Also check regular src as fallback
                    if img.get('src'):
                        src = img.get('src')
                        # Modify Pexels URLs to get larger versions
                        if 'images.pexels.com' in src:
                            # Replace size parameters for larger image
                            large_src = re.sub(r'\?.*$', '?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260', src)
                            image_sources.append(large_src)
                
                # Return the first valid high-res image
                for img_url in image_sources:
                    if img_url and self._validate_image_url(img_url):
                        logger.info(f"Found high-res image on Pexels: {img_url[:100]}...")
                        return img_url
                        
        except Exception as e:
            logger.warning(f"Error searching Pexels: {str(e)}")
        
        return None
    
    def _validate_image_url(self, url: str) -> bool:
        """Validate that the URL is a valid image URL"""
        if not url:
            return False
        
        # Check if it's a valid URL format
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check if it has an image extension or looks like an image URL
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        has_extension = any(ext in url.lower() for ext in image_extensions)
        
        # Some URLs don't have extensions but are still images (CDN URLs)
        looks_like_image = any(keyword in url.lower() for keyword in ['image', 'img', 'photo', 'pic'])
        
        return has_extension or looks_like_image
    
    def get_fallback_image(self, recipe_name: str) -> str:
        """
        Get a fallback image if no real image is found
        Uses high-resolution fallback services
        """
        # Use foodish API which provides random food images
        try:
            # Foodish provides random food images by category
            # Try to map the recipe to a category
            categories = {
                'burger': ['burger', 'hamburger', 'cheeseburger'],
                'pizza': ['pizza', 'margherita', 'pepperoni'],
                'pasta': ['pasta', 'spaghetti', 'lasagna', 'macaroni', 'penne', 'noodle'],
                'rice': ['rice', 'fried rice', 'risotto', 'pilaf'],
                'dessert': ['cake', 'cookie', 'brownie', 'dessert', 'sweet', 'chocolate'],
                'biryani': ['biryani', 'pulao'],
                'dosa': ['dosa', 'idli', 'uttapam'],
                'idly': ['idly', 'idli'],
                'samosa': ['samosa', 'pakora'],
                'butter-chicken': ['butter chicken', 'chicken curry', 'tikka'],
                'dosa': ['dosa'],
                'pizza': ['pizza'],
            }
            
            recipe_lower = recipe_name.lower()
            selected_category = None
            
            # Check for specific categories
            for category, keywords in categories.items():
                if any(keyword in recipe_lower for keyword in keywords):
                    selected_category = category
                    break
            
            # If we found a category, use foodish API
            if selected_category:
                response = requests.get(f'https://foodish-api.com/api/images/{selected_category}', timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    if 'image' in data:
                        # Foodish returns high-quality images
                        logger.info(f"Using Foodish fallback image for category: {selected_category}")
                        return data['image']
            
            # Fallback to generic food image
            response = requests.get('https://foodish-api.com/api/', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if 'image' in data:
                    logger.info("Using generic Foodish fallback image")
                    return data['image']
                    
        except Exception as e:
            logger.warning(f"Error getting Foodish image: {str(e)}")
        
        # Final fallback: use Lorem Picsum with larger dimensions
        # Request a high-resolution image
        fallback_url = f"https://picsum.photos/1200/800?random={hash(recipe_name)}"
        logger.info(f"Using Lorem Picsum fallback: {fallback_url}")
        return fallback_url