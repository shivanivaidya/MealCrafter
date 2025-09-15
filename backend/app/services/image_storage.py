import os
import uuid
import httpx
import logging
from pathlib import Path
from typing import Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageStorageService:
    def __init__(self):
        self.storage_dir = Path("static/recipe_images")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    async def download_and_store_image(self, image_url: str, recipe_id: Optional[int] = None) -> Optional[str]:
        """
        Download an image from a URL and store it locally.
        Returns the local file path if successful, None otherwise.
        """
        try:
            # Generate unique filename
            file_extension = self._get_image_extension(image_url)
            if recipe_id:
                filename = f"recipe_{recipe_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            else:
                filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            file_path = self.storage_dir / filename
            
            # Download the image
            async with httpx.AsyncClient() as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/avif,image/svg+xml,image/*,*/*;q=0.8',
                    'Referer': 'https://www.instagram.com/',
                }
                
                async with client.stream('GET', image_url, headers=headers, timeout=30.0) as response:
                    if response.status_code != 200:
                        logger.error(f"Failed to download image: HTTP {response.status_code}")
                        return None
                    
                    # Read the image data
                    image_data = b""
                    async for chunk in response.aiter_bytes():
                        image_data += chunk
                    
                    # Validate and optimize the image
                    processed_image_data = self._process_image(image_data)
                    if not processed_image_data:
                        return None
                    
                    # Save to file
                    with open(file_path, 'wb') as f:
                        f.write(processed_image_data)
                    
                    logger.info(f"Successfully stored image: {file_path}")
                    return f"/static/recipe_images/{filename}"
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout downloading image: {image_url}")
        except Exception as e:
            logger.error(f"Error downloading and storing image: {e}")
        
        return None
    
    def _get_image_extension(self, url: str) -> str:
        """Extract image extension from URL, default to jpg"""
        try:
            # Remove query parameters
            clean_url = url.split('?')[0]
            extension = clean_url.split('.')[-1].lower()
            if extension in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                return 'jpg'  # Convert all to jpg for consistency
            return 'jpg'
        except:
            return 'jpg'
    
    def _process_image(self, image_data: bytes) -> Optional[bytes]:
        """Process and optimize the image"""
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (handles RGBA, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1200x1200 for better quality)
            max_size = (1200, 1200)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as JPEG with higher quality
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def delete_image(self, image_path: str) -> bool:
        """Delete a stored image file"""
        try:
            if image_path.startswith('/static/recipe_images/'):
                filename = image_path.replace('/static/recipe_images/', '')
                file_path = self.storage_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted image: {file_path}")
                    return True
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
        return False

# Global instance
image_storage = ImageStorageService()