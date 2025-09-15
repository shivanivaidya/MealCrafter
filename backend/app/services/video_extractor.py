"""
Video recipe extraction service
Extracts recipe content from YouTube, Instagram, and other video platforms
"""
import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False
    YouTubeTranscriptApi = None
import yt_dlp

logger = logging.getLogger(__name__)


class VideoRecipeExtractor:
    """Extract recipe content from video platforms"""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            # Try to use browser cookies for authentication
            'cookiesfrombrowser': ('chrome',),  # Try Chrome first, can also use 'firefox', 'safari'
            # Add user agent to avoid detection
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }
        }
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract recipe content from a video URL
        Supports YouTube, Instagram, TikTok, and other platforms
        """
        try:
            # Detect platform
            platform = self._detect_platform(url)
            logger.info(f"Detected platform: {platform} for URL: {url}")
            
            if platform == "youtube":
                return self._extract_youtube(url)
            elif platform == "instagram":
                return self._extract_instagram(url)
            elif platform == "tiktok":
                return self._extract_tiktok(url)
            else:
                # Try generic extraction with yt-dlp
                return self._extract_generic(url)
                
        except Exception as e:
            logger.error(f"Failed to extract video content: {str(e)}")
            raise ValueError(f"Failed to extract video content: {str(e)}")
    
    def _detect_platform(self, url: str) -> str:
        """Detect which platform the URL is from"""
        domain = urlparse(url).netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'instagram.com' in domain:
            return 'instagram'
        elif 'tiktok.com' in domain:
            return 'tiktok'
        elif 'facebook.com' in domain or 'fb.watch' in domain:
            return 'facebook'
        elif 'vimeo.com' in domain:
            return 'vimeo'
        else:
            return 'unknown'
    
    def _extract_youtube(self, url: str) -> Dict[str, Any]:
        """Extract content from YouTube videos"""
        try:
            # Extract video ID
            video_id = self._get_youtube_video_id(url)
            if not video_id:
                logger.error(f"Could not extract YouTube video ID from URL: {url}")
                raise ValueError(f"Could not extract YouTube video ID from URL: {url}")
            
            # Get video metadata using yt-dlp
            metadata = self._get_video_metadata(url)
            
            if not metadata:
                logger.warning(f"Could not get metadata for video: {url}")
                metadata = {}
            
            # Try to get transcript/captions
            transcript = self._get_youtube_transcript(video_id)
            
            # Get video description which often contains recipe
            description = metadata.get('description', '')
            
            # Combine all text content
            full_text = f"# {metadata.get('title', 'Video Recipe')}\n\n"
            
            if description:
                full_text += f"## Description:\n{description}\n\n"
            
            if transcript:
                full_text += f"## Video Transcript:\n{transcript}\n\n"
            
            # For videos, always use the full text (description + transcript)
            # The AI parser is better at extracting the complete recipe
            # Don't try to pre-extract as it might miss content
            recipe_text = full_text
            
            # Get the best thumbnail
            thumbnail = self._get_best_thumbnail(metadata)
            
            return {
                'platform': 'youtube',
                'title': metadata.get('title', ''),
                'author': metadata.get('uploader', ''),
                'url': url,
                'thumbnail': thumbnail,
                'duration': metadata.get('duration', 0),
                'description': description,
                'transcript': transcript,
                'full_text': full_text,
                'recipe_text': recipe_text or full_text,
                'raw_metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract YouTube content: {str(e)}")
            raise
    
    def _extract_instagram(self, url: str) -> Dict[str, Any]:
        """Extract content from Instagram posts/reels"""
        try:
            # Instagram requires authentication for most content
            # Provide clear error message to users
            logger.warning(f"Instagram extraction attempted for: {url}")
            
            # Try yt-dlp first with browser cookies
            try:
                metadata = self._get_video_metadata(url)
                description = metadata.get('description', '')
                
                # If we got content, use it
                if description and len(description) > 50:
                    title = metadata.get('title', 'Instagram Recipe')
                    author = metadata.get('uploader', metadata.get('creator', 'Unknown'))
                    thumbnail = self._get_best_thumbnail(metadata)
                    
                    logger.info(f"Successfully extracted Instagram content: {len(description)} chars")
                    
                    # Build full text for AI processing
                    full_text = f"# {title}\n\n"
                    full_text += f"By: {author}\n\n"
                    full_text += f"Source: Instagram ({url})\n\n"
                    full_text += f"## Content:\n{description}\n\n"
                    
                    # For Instagram, always use the full description as it contains the complete recipe
                    # Don't try to extract/truncate it
                    logger.info(f"Using full Instagram description for recipe extraction")
                    
                    return {
                        'platform': 'instagram',
                        'title': title,
                        'author': author,
                        'url': url,
                        'thumbnail': thumbnail,
                        'description': description,
                        'full_text': full_text,
                        'recipe_text': full_text,  # Use full text, not extracted
                        'raw_metadata': metadata
                    }
                    
            except Exception as e:
                logger.warning(f"Could not extract Instagram content: {str(e)}")
            
            # If we get here, extraction failed
            error_msg = """Instagram requires authentication to access most content.
            
To add an Instagram recipe, please:
1. Copy the recipe text from the Instagram post
2. Paste it directly into MealCrafter
3. Or save the Instagram post and re-upload when it becomes publicly accessible

Alternative: Use recipe videos from YouTube or TikTok which don't require authentication."""
            
            raise ValueError(error_msg)
            
        except Exception as e:
            logger.error(f"Failed to extract Instagram content: {str(e)}")
            raise
    
    def _extract_tiktok(self, url: str) -> Dict[str, Any]:
        """Extract content from TikTok videos"""
        try:
            # Use yt-dlp for TikTok
            metadata = self._get_video_metadata(url)
            
            description = metadata.get('description', '')
            
            full_text = f"# {metadata.get('title', 'TikTok Recipe')}\n\n"
            full_text += f"By: {metadata.get('creator', metadata.get('uploader', 'Unknown'))}\n\n"
            
            if description:
                full_text += f"## Description:\n{description}\n\n"
            
            # TikTok recipes are often in description or comments
            recipe_text = self._extract_recipe_from_text(description)
            
            # For TikTok, just use the raw title from metadata
            # The AI parser will clean it up when processing the recipe
            title = metadata.get('title', 'TikTok Recipe')
            
            # Get the best thumbnail - prefer food images over people
            thumbnail = self._get_best_thumbnail(metadata)
            
            return {
                'platform': 'tiktok',
                'title': title,
                'author': metadata.get('creator', metadata.get('uploader', '')),
                'url': url,
                'thumbnail': thumbnail,
                'description': description,
                'full_text': full_text,
                'recipe_text': recipe_text or full_text,
                'raw_metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract TikTok content: {str(e)}")
            raise
    
    def _extract_generic(self, url: str) -> Dict[str, Any]:
        """Generic extraction for any video platform using yt-dlp"""
        try:
            metadata = self._get_video_metadata(url)
            
            title = metadata.get('title', 'Video Recipe')
            description = metadata.get('description', '')
            
            full_text = f"# {title}\n\n"
            
            if metadata.get('uploader'):
                full_text += f"By: {metadata.get('uploader')}\n\n"
            
            if description:
                full_text += f"## Description:\n{description}\n\n"
            
            # Try to extract recipe from description
            recipe_text = self._extract_recipe_from_text(description)
            
            return {
                'platform': 'other',
                'title': title,
                'author': metadata.get('uploader', ''),
                'url': url,
                'thumbnail': metadata.get('thumbnail', ''),
                'description': description,
                'full_text': full_text,
                'recipe_text': recipe_text or full_text,
                'raw_metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract generic video content: {str(e)}")
            raise
    
    def _get_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)',
            r'(?:youtube\.com\/v\/)([\w-]+)',
            r'(?:youtube\.com\/shorts\/)([\w-]+)'  # Added support for YouTube Shorts
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try parsing query parameters
        parsed = urlparse(url)
        if parsed.netloc in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                return query_params['v'][0]
            # Also check path for shorts
            if '/shorts/' in parsed.path:
                match = re.search(r'/shorts/([\w-]+)', parsed.path)
                if match:
                    return match.group(1)
        
        return None
    
    def _get_youtube_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript/captions from YouTube video"""
        if not TRANSCRIPT_AVAILABLE:
            logger.warning("youtube-transcript-api not installed, skipping transcript extraction")
            return None
            
        try:
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            transcript_data = api.fetch(video_id)
            
            # Convert transcript objects to text
            transcript_text = []
            for entry in transcript_data:
                # Access the text attribute directly
                if hasattr(entry, 'text'):
                    transcript_text.append(entry.text)
            
            if transcript_text:
                return ' '.join(transcript_text)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not get YouTube transcript: {str(e)}")
            return None
    
    def _get_video_metadata(self, url: str) -> Dict[str, Any]:
        """Get video metadata using yt-dlp"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Failed to get video metadata: {str(e)}")
            return {}
    
    def _extract_recipe_from_text(self, text: str) -> Optional[str]:
        """
        Try to extract structured recipe from text
        Look for patterns like ingredients lists and numbered instructions
        """
        if not text:
            return None
        
        lines = text.split('\n')
        recipe_parts = []
        
        # Look for ingredients section
        ingredients_keywords = ['ingredients', 'you need', 'you\'ll need', 'recipe:', 'items needed']
        instructions_keywords = ['instructions', 'directions', 'method', 'steps', 'how to', 'preparation']
        
        in_ingredients = False
        in_instructions = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check for ingredients section
            if any(keyword in line_lower for keyword in ingredients_keywords):
                in_ingredients = True
                in_instructions = False
                recipe_parts.append(f"\n## Ingredients:\n")
                continue
            
            # Check for instructions section  
            if any(keyword in line_lower for keyword in instructions_keywords):
                in_instructions = True
                in_ingredients = False
                recipe_parts.append(f"\n## Instructions:\n")
                continue
            
            # Add content if in a section
            if in_ingredients and line.strip():
                # Skip lines that contain URLs or social media
                if 'http' in line or 'www.' in line or '@' in line:
                    continue
                # Skip common non-ingredient phrases
                if any(skip in line.lower() for skip in ['follow', 'subscribe', 'watch', 'click', 'link', 'comment', 'video', 'channel']):
                    continue
                # Clean up common ingredient patterns
                cleaned = re.sub(r'^[-•*]\s*', '', line.strip())
                # Only add if it looks like an ingredient (contains common food words or measurements)
                if cleaned and len(cleaned) > 2 and not cleaned.startswith('#'):
                    recipe_parts.append(f"- {cleaned}")
            
            elif in_instructions and line.strip():
                # Clean up instruction numbering
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
                if cleaned:
                    recipe_parts.append(f"{len([p for p in recipe_parts if p.startswith('## Instructions')]) + 1}. {cleaned}")
        
        # Only return recipe if we found actual content
        if recipe_parts:
            # Check if we have at least some ingredients or instructions
            has_ingredients = any('## Ingredients:' in part for part in recipe_parts) and \
                             any(part.startswith('- ') for part in recipe_parts)
            has_instructions = any('## Instructions:' in part for part in recipe_parts) and \
                              len([p for p in recipe_parts if p.startswith('1. ') or p.startswith('2. ')]) > 0
            
            if has_ingredients or has_instructions:
                return '\n'.join(recipe_parts)
        
        # If no structured recipe found, return None
        return None
    
    def _get_best_thumbnail(self, metadata: Dict[str, Any]) -> str:
        """
        Get the best thumbnail from video metadata
        Prefers images that might show food over people
        """
        thumbnail = metadata.get('thumbnail', '')
        
        # If there are multiple thumbnails available
        if metadata.get('thumbnails'):
            thumbnails = metadata.get('thumbnails', [])
            
            # Sort thumbnails by preference
            # 1. Look for thumbnails that might be from the end of the video (often show final dish)
            # 2. Prefer higher resolution thumbnails
            # 3. For TikTok/Instagram, often the last frame shows the final product
            
            # Try to get thumbnails sorted by quality/resolution
            sorted_thumbs = []
            for thumb in thumbnails:
                if isinstance(thumb, dict) and thumb.get('url'):
                    # Assign priority based on various factors
                    priority = 0
                    
                    # Check if thumbnail URL contains keywords suggesting it's from end of video
                    url = thumb.get('url', '')
                    if any(keyword in url.lower() for keyword in ['final', 'end', 'last', 'result']):
                        priority += 10
                    
                    # Prefer higher resolution (if width/height available)
                    width = thumb.get('width', 0)
                    height = thumb.get('height', 0)
                    if width and height:
                        priority += (width * height) / 1000000  # Normalize to avoid huge numbers
                    
                    # Check preference/id that might indicate position
                    thumb_id = thumb.get('id', '')
                    if thumb_id and thumb_id.isdigit():
                        # Higher ID numbers often mean later in video
                        priority += int(thumb_id) / 100
                    
                    sorted_thumbs.append((priority, thumb.get('url')))
            
            # Sort by priority (highest first)
            sorted_thumbs.sort(key=lambda x: x[0], reverse=True)
            
            # Return the best thumbnail URL
            if sorted_thumbs:
                thumbnail = sorted_thumbs[0][1]
            elif thumbnails:
                # Fallback: just get any valid thumbnail
                for thumb in thumbnails:
                    if isinstance(thumb, dict) and thumb.get('url'):
                        thumbnail = thumb['url']
                        break
                    elif isinstance(thumb, str):
                        thumbnail = thumb
                        break
        
        return thumbnail