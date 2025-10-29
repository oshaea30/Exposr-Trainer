"""Lexica.art API fetcher for AI-generated images."""
import os
import aiohttp
import hashlib
import logging
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from scraper.base_fetcher import BaseFetcher
from scraper.image_cleaner import is_valid_image

logger = logging.getLogger(__name__)


class LexicaFetcher(BaseFetcher):
    """Fetch images from Lexica.art API (AI-generated images)."""
    
    def __init__(self, config: dict):
        """Initialize Lexica fetcher."""
        self.config = config
        # Lexica has a public JSON API (no auth required)
        self.api_url = "https://lexica.art/api/v1/search"
        
        source_config = config.get("lexica", {})
        self.queries = source_config.get("queries", ["portrait", "landscape", "character"])
        self.limit_per_query = source_config.get("limit_per_query", 10)
    
    async def fetch_images(self, limit: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch AI-generated images from Lexica.art."""
        samples = []
        
        try:
            conn = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=conn) as session:
                for query in self.queries[:2]:  # Limit to 2 queries
                    if len(samples) >= limit:
                        break
                    
                    # Search images - Lexica public JSON API
                    url = self.api_url
                    params = {
                        "q": query,
                        "limit": min(self.limit_per_query, limit - len(samples))
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            images = data.get("images", [])
                            
                            for item in images:
                                if len(samples) >= limit:
                                    break
                                
                                # Get image URL
                                image_url = item.get("src") or item.get("url")
                                if not image_url:
                                    continue
                                
                                # Download image
                                image_bytes = await self._download_image(session, image_url)
                                if not image_bytes or not is_valid_image(image_bytes):
                                    continue
                                
                                # Create metadata
                                metadata = self._create_metadata(item, image_url, image_bytes)
                                samples.append((image_bytes, metadata))
                        else:
                            logger.warning(f"Lexica API returned status {response.status}")
                        
                        logger.info(f"Fetched {len(samples)} images from Lexica (query: {query})")
        
        except Exception as e:
            logger.error(f"Error fetching from Lexica: {e}")
        
        return samples
    
    async def _download_image(self, session: aiohttp.ClientSession, url: str) -> bytes:
        """Download image from URL."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            logger.debug(f"Error downloading image from {url}: {e}")
        
        return None
    
    def _create_metadata(self, item: dict, image_url: str, image_bytes: bytes) -> dict:
        """Create metadata dictionary for Lexica image."""
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        return {
            "id": str(uuid4()),
            "image_url": image_url,
            "source": "lexica",
            "label": "ai_generated",
            "confidence": None,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": image_hash,
            "attribution": {
                "platform": "Lexica.art",
                "creator": "Community",
                "license": "Community content",
                "url": f"https://lexica.art/?q={item.get('prompt', '')}"
            },
            "api_data": {
                "image_id": item.get("id"),
                "width": item.get("width"),
                "height": item.get("height"),
                "prompt": item.get("prompt"),
                "model": item.get("model", "stable-diffusion")
            }
        }
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "lexica"

