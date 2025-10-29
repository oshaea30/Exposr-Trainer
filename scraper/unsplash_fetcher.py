"""Unsplash API fetcher for real photography."""
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


class UnsplashFetcher(BaseFetcher):
    """Fetch images from Unsplash API (real photography)."""
    
    def __init__(self, config: dict):
        """Initialize Unsplash fetcher."""
        self.config = config
        self.api_url = "https://api.unsplash.com"
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        source_config = config.get("unsplash", {})
        self.topic = source_config.get("topic", "technology")
        self.queries = source_config.get("queries", ["portrait photography", "nature photography", "product photography"])
        self.limit_per_query = source_config.get("limit_per_query", 10)
    
    async def fetch_images(self, limit: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch images from Unsplash.
        
        Args:
            limit: Maximum number of images to fetch
            
        Returns:
            List of (image_bytes, metadata) tuples
        """
        if not self.access_key:
            logger.error("UNSPLASH_ACCESS_KEY not set")
            return []
        
        samples = []
        
        try:
            conn = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=conn) as session:
                for query in self.queries[:2]:  # Limit to 2 queries
                    if len(samples) >= limit:
                        break
                    
                    # Search photos
                    url = f"{self.api_url}/search/photos"
                    params = {
                        "query": query,
                        "per_page": min(self.limit_per_query, limit - len(samples)),
                        "client_id": self.access_key
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for photo in data.get("results", []):
                                if len(samples) >= limit:
                                    break
                                
                                # Download image
                                image_url = photo.get("urls", {}).get("regular")
                                if not image_url:
                                    continue
                                
                                image_bytes = await self._download_image(session, image_url)
                                if not image_bytes or not is_valid_image(image_bytes):
                                    continue
                                
                                # Create metadata
                                metadata = self._create_metadata(photo, image_url, image_bytes)
                                samples.append((image_bytes, metadata))
                        
                        logger.info(f"Fetched {len(samples)} images from Unsplash (query: {query})")
        
        except Exception as e:
            logger.error(f"Error fetching from Unsplash: {e}")
        
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
        """Create metadata dictionary for Unsplash photo."""
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        return {
            "id": str(uuid4()),
            "image_url": image_url,
            "source": "unsplash",
            "label": "real",
            "confidence": None,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": image_hash,
            "attribution": {
                "platform": "Unsplash",
                "photographer": photo.get("user", {}).get("name", "Unknown"),
                "license": "Unsplash License",
                "url": photo.get("links", {}).get("html", "")
            },
            "api_data": {
                "photo_id": photo.get("id"),
                "description": photo.get("description"),
                "likes": photo.get("likes"),
                "downloads": photo.get("downloads")
            }
        }
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "unsplash"

