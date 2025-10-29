"""Fetcher manager for coordinating multiple image sources."""
import logging
from typing import List, Tuple

from scraper.base_fetcher import BaseFetcher
from scraper.unsplash_fetcher import UnsplashFetcher
from scraper.pexels_fetcher import PexelsFetcher
from scraper.civitai_fetcher import CivitAIFetcher
from utils.config_loader import load_sources_config

logger = logging.getLogger(__name__)


class FetcherManager:
    """Manages multiple image fetchers."""
    
    def __init__(self, config: dict):
        """Initialize fetcher manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.sources_config = load_sources_config()
        self.fetchers = self._initialize_fetchers()
        
        logger.info(f"Initialized {len(self.fetchers)} image fetchers")
    
    def _initialize_fetchers(self) -> List[BaseFetcher]:
        """Initialize enabled fetchers based on configuration."""
        fetchers = []
        sources = self.sources_config.get("sources", [])
        
        for source in sources:
            if not source.get("enabled", True):
                continue
                
            name = source["name"]
            
            try:
                if name == "unsplash":
                    fetchers.append(UnsplashFetcher(self.config))
                elif name == "pexels":
                    fetchers.append(PexelsFetcher(self.config))
                elif name == "civitai":
                    fetchers.append(CivitAIFetcher(self.config))
            except Exception as e:
                logger.error(f"Failed to initialize {name} fetcher: {e}")
        
        return fetchers
    
    async def fetch_all(self, limit_per_source: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch from all enabled sources.
        
        Args:
            limit_per_source: Maximum images to fetch per source
            
        Returns:
            List of (image_bytes, metadata) tuples from all sources
        """
        all_samples = []
        
        for fetcher in self.fetchers:
            try:
                samples = await fetcher.fetch_images(limit_per_source)
                all_samples.extend(samples)
                logger.info(f"Fetched {len(samples)} images from {fetcher.get_source_name()}")
            except Exception as e:
                logger.error(f"Error fetching from {fetcher.get_source_name()}: {e}")
        
        logger.info(f"Total fetched: {len(all_samples)} images from {len(self.fetchers)} sources")
        return all_samples
    
    def get_active_sources(self) -> List[str]:
        """Get list of active source names."""
        return [fetcher.get_source_name() for fetcher in self.fetchers]

