"""
OCR Service for extracting text from recipe images
"""
import io
import base64
from typing import Optional, Tuple
from PIL import Image
import pytesseract
import cv2
import numpy as np
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from recipe images using OCR and AI enhancement"""
    
    def __init__(self):
        """Initialize OCR service with OpenAI client for enhanced processing"""
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def extract_text_from_image(self, image_data: bytes, preserve_original: bool = False) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_data: Image file bytes
            preserve_original: Whether to preserve original text exactly
            
        Returns:
            Extracted text from the image
        """
        logger.debug(f"Extract text from image: preserve_original={preserve_original}")
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract text using Tesseract OCR
            raw_text = pytesseract.image_to_string(processed_image)
            
            # If we have OpenAI, use it to enhance the OCR output
            if self.client and raw_text.strip():
                enhanced_text = self._enhance_with_ai(raw_text, image_data, preserve_original)
                return enhanced_text
            
            return raw_text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Try multiple preprocessing approaches
        results = []
        
        # Approach 1: Simple threshold
        try:
            _, simple_thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            results.append(Image.fromarray(simple_thresh))
        except:
            pass
        
        # Approach 2: Adaptive threshold
        try:
            adaptive = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            results.append(Image.fromarray(adaptive))
        except:
            pass
        
        # Approach 3: Original grayscale
        results.append(Image.fromarray(gray))
        
        # Try OCR on each preprocessed image and use the one with most text
        best_text = ""
        best_image = image
        
        for processed in results:
            try:
                text = pytesseract.image_to_string(processed)
                if len(text.strip()) > len(best_text):
                    best_text = text.strip()
                    best_image = processed
            except:
                continue
        
        return best_image
    
    def _enhance_with_ai(self, ocr_text: str, image_data: bytes, preserve_original: bool = False) -> str:
        """
        Use GPT-4 Vision to enhance OCR results by analyzing the image directly
        
        Args:
            ocr_text: Raw text from OCR
            image_data: Original image bytes
            preserve_original: Whether to preserve original text exactly
            
        Returns:
            Enhanced and corrected text
        """
        logger.debug(f"Enhance with AI: preserve_original={preserve_original}, OCR text length={len(ocr_text)}")
        
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Different prompts based on preserve_original
            if preserve_original:
                system_prompt = """You are an expert at reading and transcribing recipes from images EXACTLY as written.
                Your task is to extract the recipe text from the provided image, correcting ONLY obvious OCR errors.
                DO NOT:
                - Reformat or reorganize the text
                - Change wording or phrasing
                - Add formatting like "###" or bullet points that aren't in the original
                - Improve grammar or style
                
                DO:
                - Fix obvious OCR errors (like 0 instead of O, 1 instead of l)
                - Keep the exact original wording and structure
                - Preserve the original formatting as much as possible
                
                Extract the text EXACTLY as it appears in the image."""
            else:
                system_prompt = """You are an expert at reading and transcribing recipes from images. 
                Your task is to extract the recipe text from the provided image, correcting any OCR errors 
                and formatting it properly. Focus on:
                1. Recipe title
                2. Ingredients list (with quantities and units)
                3. Instructions/directions
                4. Any notes about servings, cooking time, or temperature
                
                Format the output as clean, readable recipe text."""
            
            # Use GPT-4o to analyze the image and enhance OCR
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please extract and format the recipe from this image. Here's what OCR detected (may have errors): {ocr_text[:500]}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            enhanced_text = response.choices[0].message.content
            logger.debug(f"Enhanced text length: {len(enhanced_text)}, using {'preserve_original' if preserve_original else 'standard'} prompt")
            return enhanced_text
            
        except Exception as e:
            logger.warning(f"AI enhancement failed, using raw OCR: {e}")
            # If AI enhancement fails, try basic cleaning
            return self._basic_text_cleaning(ocr_text)
    
    def _basic_text_cleaning(self, text: str) -> str:
        """
        Basic text cleaning without AI
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Try to identify and format sections
        cleaned_lines = []
        current_section = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Identify sections
            if any(keyword in line_lower for keyword in ['ingredient', 'material', 'item']):
                current_section = 'ingredients'
                cleaned_lines.append(f"\nIngredients:")
            elif any(keyword in line_lower for keyword in ['instruction', 'direction', 'method', 'step']):
                current_section = 'instructions'
                cleaned_lines.append(f"\nInstructions:")
            elif any(keyword in line_lower for keyword in ['serve', 'serving', 'yield', 'make']):
                cleaned_lines.append(f"\n{line}")
                current_section = None
            else:
                # Add the line with appropriate formatting
                if current_section == 'ingredients' and line and not line.endswith(':'):
                    cleaned_lines.append(f"- {line}")
                elif current_section == 'instructions' and line and not line.endswith(':'):
                    # Try to detect numbered steps
                    if line[0].isdigit() or line.startswith(('•', '-', '*')):
                        cleaned_lines.append(line)
                    else:
                        cleaned_lines.append(f"- {line}")
                else:
                    cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Validate if the image is suitable for OCR
        
        Args:
            image_data: Image file bytes
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check image size
            width, height = image.size
            if width < 200 or height < 200:
                return False, "Image is too small. Minimum size is 200x200 pixels."
            
            if width > 4000 or height > 4000:
                return False, "Image is too large. Maximum size is 4000x4000 pixels."
            
            # Check file size
            if len(image_data) > 10 * 1024 * 1024:  # 10MB
                return False, "Image file is too large. Maximum file size is 10MB."
            
            return True, "Image is valid"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"