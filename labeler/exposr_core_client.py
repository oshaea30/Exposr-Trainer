"""Exposr-Core API client for image detection."""
import os
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ExposrCoreClient:
    """Client for interacting with Exposr-Core detection API."""
    
    def __init__(self, endpoint: str, enabled: bool = True):
        """Initialize Exposr-Core client.
        
        Args:
            endpoint: Exposr-Core API endpoint
            enabled: Whether to enable the client
        """
        self.endpoint = endpoint
        self.enabled = enabled
    
    async def detect(self, image_bytes: bytes) -> Optional[float]:
        """Detect if image is AI-generated using Exposr-Core.
        
        Args:
            image_bytes: Image data
            
        Returns:
            AI probability score (0.0-1.0) or None if unavailable
        """
        if not self.enabled:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
                
                async with session.post(self.endpoint, data=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Assume API returns {ai_probability: float}
                        return result.get('ai_probability', result.get('score', None))
                    else:
                        logger.warning(f"Exposr-Core returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error calling Exposr-Core: {e}")
            return None

