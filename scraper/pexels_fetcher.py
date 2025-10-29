"""Pexels API fetcher for real photography."""
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


class PexelsFetcher(BaseFetcher):
    """Fetch images from Pexels API (real photography)."""
    
    def __init__(self, config: dict):
        """Initialize Pexels fetcher."""
        self.config = config
        self.api_url = "https://api.pexels.com/v1"
        self.api_key = os.getenv("PEXELS_API_KEY")
        
        source_config = config.get("pexels", {})
        self.queries = source_config.get("queries", ["fashion", "lifestyle", "business"])
        self.limit_per_query = source_config.get("limit_per_query", 10)
    
    async def fetch_images(self, limit: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch images from Pexels."""
        if not self.api_key:
            logger.error("PEXELS_API_KEY not set")
            return []
        
        samples = []
        
        try:
            conn = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=conn) as session:
                headers = {"Authorization": self.api_key}
                
                for query in self.queries[:2]:  # Limit to 2 queries
                    if len(samples) >= limit:
                        break
                    
                    # Search photos
                    url = f"{self.api_url}/search"
                    params = {
                        "query": query,
                        "per_page": min(self.limit_per_query, limit - len(samples))
                    }
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for photo in data.get("photos", []):
                                if len(samples) >= limit:
                                    break
                                
                                # Download image
                                image_url = photo.get("src", {}).get("medium")
                                if not image_url:
                                    continue
                                
                                image_bytes = await self._download_image(session, image_url)
                                if not image_bytes or not is_valid_image(image_bytes):
                                    continue
                                
                                # Create metadata
                                metadata = self._create_metadata(photo, image_url, image_bytes)
                                samples.append((image_bytes, metadata))
                        
                        logger.info(f"Fetched {len(samples)} images from Pexels (query: {query})")
        
        except Exception as e:
            logger.error(f"Error fetching from Pexels: {e}")
        
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
    
    def _create_metadata(self, photo: dict, image_url: str, image_bytes: bytes) -> dict:
        """Create metadata dictionary for Pexels photo."""
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        return {
            "id": str(uuid4()),
            "image_url": image_url,
            "source": "pexels",
            "label": "real",
            "confidence": None,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": image_hash,
            "attribution": {
                "platform": "Pexels",
                "photographer": photo.get("photographer", "Unknown"),
                "license": "Free to use",
                "url": photo.get("url", "")
            },
            "api_data": {
                "photo_id": photo.get("id"),
                "width": photo.get("width"),
                "height": photo.get("height")
            }
        }
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "pexels"

