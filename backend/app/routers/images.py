from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging
from urllib.parse import quote, unquote
from typing import AsyncGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/proxy/{encoded_url:path}")
async def proxy_image(encoded_url: str):
    """
    Proxy external images to avoid CORS issues.
    Especially useful for Instagram CDN images that block cross-origin requests.
    """
    try:
        # Decode the URL
        image_url = unquote(encoded_url)
        
        logger.info(f"Proxying image: {image_url}")
        
        # Validate that it's an image URL
        if not any(domain in image_url.lower() for domain in [
            'cdninstagram.com', 
            'tiktokcdn', 
            'ytimg.com',
            'googleapis.com'
        ]):
            raise HTTPException(status_code=400, detail="Invalid image domain")
        
        async with httpx.AsyncClient() as client:
            # Set headers to mimic a more recent browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/avif,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'identity',  # Don't compress for streaming
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://www.instagram.com/',
                'Sec-CH-UA': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'DNT': '1'
            }
            
            # Stream the image response
            async with client.stream('GET', image_url, headers=headers, timeout=30.0) as response:
                if response.status_code == 403:
                    logger.warning(f"Instagram CDN blocked request (403) for URL: {image_url}")
                    # Return a placeholder or retry with different approach
                    raise HTTPException(status_code=503, detail="Image temporarily unavailable due to CDN restrictions")
                elif response.status_code != 200:
                    logger.error(f"Failed to fetch image: {response.status_code}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch image")
                
                content_type = response.headers.get('content-type', 'image/jpeg')
                content_length = response.headers.get('content-length')
                
                # Create headers for the response
                response_headers = {
                    'Content-Type': content_type,
                    'Cache-Control': 'public, max-age=86400',  # Cache for 1 day
                    'Access-Control-Allow-Origin': '*',  # Allow CORS
                }
                
                if content_length:
                    response_headers['Content-Length'] = content_length
                
                async def generate() -> AsyncGenerator[bytes, None]:
                    try:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    except httpx.StreamClosed:
                        logger.warning(f"Stream was closed during image transfer: {image_url}")
                        # Stream was closed, but we've already yielded some data
                        # The client will receive a partial image
                    except Exception as e:
                        logger.error(f"Error during stream: {e}")
                        # Let the error propagate to be handled by FastAPI
                
                return StreamingResponse(
                    generate(), 
                    media_type=content_type, 
                    headers=response_headers
                )
                
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching image: {image_url}")
        raise HTTPException(status_code=408, detail="Timeout fetching image")
    except Exception as e:
        logger.error(f"Error proxying image: {e}")
        raise HTTPException(status_code=500, detail="Failed to proxy image")