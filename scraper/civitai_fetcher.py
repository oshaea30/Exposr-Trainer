"""CivitAI API fetcher for AI-generated images."""
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


class CivitAIFetcher(BaseFetcher):
    """Fetch images from CivitAI API (AI-generated images)."""
    
    def __init__(self, config: dict):
        """Initialize CivitAI fetcher."""
        self.config = config
        self.api_url = os.getenv("CIVITAI_API_URL", "https://civitai.com/api/v1")
        self.api_key = os.getenv("CIVITAI_API_KEY", "")
        
        source_config = config.get("civitai", {})
        self.queries = source_config.get("queries", ["characters", "landscapes", "portraits"])
        self.limit_per_query = source_config.get("limit_per_query", 10)
    
    async def fetch_images(self, limit: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch AI-generated images from CivitAI."""
        samples = []
        
        try:
            conn = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=conn) as session:
                for query in self.queries[:2]:  # Limit to 2 queries
                    if len(samples) >= limit:
                        break
                    
                    # Search images
                    url = f"{self.api_url}/images"
                    params = {
                        "limit": min(self.limit_per_query, limit - len(samples)),
                        "nsfw": "false"
                    }
                    
                    headers = {}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for item in data.get("items", []):
                                if len(samples) >= limit:
                                    break
                                
                                # Get image URL
                                image_url = item.get("url")
                                if not image_url:
                                    continue
                                
                                # Download image
                                image_bytes = await self._download_image(session, image_url)
                                if not image_bytes or not is_valid_image(image_bytes):
                                    continue
                                
                                # Create metadata
                                metadata = self._create_metadata(item, image_url, image_bytes)
                                samples.append((image_bytes, metadata))
                        
                        logger.info(f"Fetched {len(samples)} images from CivitAI (query: {query})")
        
        except Exception as e:
            logger.error(f"Error fetching from CivitAI: {e}")
        
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
        """Create metadata dictionary for CivitAI image."""
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        return {
            "id": str(uuid4()),
            "image_url": image_url,
            "source": "civitai",
            "label": "ai",
            "confidence": None,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": image_hash,
            "attribution": {
                "platform": "CivitAI",
                "creator": "Community",
                "license": "Community content",
                "url": f"https://civitai.com/images/{item.get('id')}"
            },
            "api_data": {
                "image_id": item.get("id"),
                "width": item.get("width"),
                "height": item.get("height"),
                "model": item.get("model") or {}
            }
        }
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "civitai"

