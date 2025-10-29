"""Fetcher manager for coordinating multiple image sources."""
import asyncio
import logging
import time
from typing import List, Tuple, Optional
from pathlib import Path
import json
from collections import defaultdict

from scraper.base_fetcher import BaseFetcher
from scraper.unsplash_fetcher import UnsplashFetcher
from scraper.pexels_fetcher import PexelsFetcher
from scraper.civitai_fetcher import CivitAIFetcher
from scraper.lexica_fetcher import LexicaFetcher
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
        
        # Rate limiting tracking: {source_name: [(timestamp, count), ...]}
        self.rate_limit_history = defaultdict(list)
        
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
                elif name == "lexica":
                    fetchers.append(LexicaFetcher(self.config))
            except Exception as e:
                logger.error(f"Failed to initialize {name} fetcher: {e}")
        
        return fetchers
    
    async def fetch_all(self, limit_per_source: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch from all enabled sources with balanced ratios.
        
        Args:
            limit_per_source: Maximum images to fetch per source
            
        Returns:
            List of (image_bytes, metadata) tuples from all sources
        """
        all_samples = []
        
        # Identify AI and real sources
        ai_fetchers = []
        real_fetchers = []
        
        for fetcher in self.fetchers:
            source_name = fetcher.get_source_name()
            # CivitAI and Lexica provide AI images, others provide real images
            if source_name in ("civitai", "lexica"):
                ai_fetchers.append(fetcher)
            else:
                real_fetchers.append(fetcher)
        
        # Get latest model accuracy to determine target ratio
        latest_accuracy = self._get_latest_accuracy()
        
        # Determine target ratio based on accuracy
        # - Below 0.8: 1:1 ratio (balanced)
        # - At/above 0.8: 60:40 real:AI ratio
        if latest_accuracy and latest_accuracy >= 0.8:
            # 60:40 real:AI ratio -> (real * 2):ai = 60:40 -> real:ai = 30:40 = 0.75:1
            ai_fetch_limit = limit_per_source
            real_fetch_limit = int(limit_per_source * 0.75)
            target_ratio = "60:40 (real:AI)"
        else:
            # 1:1 ratio (balanced)
            ai_fetch_limit = limit_per_source * 2  # Fetch 2x from AI sources
            real_fetch_limit = limit_per_source
            target_ratio = "1:1"
        
        acc_str = f"{latest_accuracy:.3f}" if latest_accuracy else "N/A"
        logger.info(f"Latest accuracy: {acc_str}, Target ratio: {target_ratio}")
        
        # Fetch from AI sources
        for fetcher in ai_fetchers:
            try:
                # Add delay between sources to respect rate limits
                await asyncio.sleep(0.5)  # 500ms delay between sources
                
                samples = await fetcher.fetch_images(ai_fetch_limit)
                all_samples.extend(samples)
                logger.info(f"Fetched {len(samples)} images from {fetcher.get_source_name()}")
            except Exception as e:
                logger.error(f"Error fetching from {fetcher.get_source_name()}: {e}")
        
        # Fetch from real sources
        for fetcher in real_fetchers:
            try:
                # Add delay between sources to respect rate limits
                await asyncio.sleep(0.5)  # 500ms delay between sources
                
                samples = await fetcher.fetch_images(real_fetch_limit)
                all_samples.extend(samples)
                logger.info(f"Fetched {len(samples)} images from {fetcher.get_source_name()}")
            except Exception as e:
                logger.error(f"Error fetching from {fetcher.get_source_name()}: {e}")
        
        # Report final ratio
        ai_count = sum(1 for _, meta in all_samples if meta.get("label") == "ai_generated")
        real_count = sum(1 for _, meta in all_samples if meta.get("label") == "real")
        
        logger.info(f"Total fetched: {len(all_samples)} images from {len(self.fetchers)} sources")
        logger.info(f"Ratio: {real_count} real : {ai_count} AI (~{real_count/max(ai_count,1):.2f}:1 ratio)")
        
        # Record API calls for rate limiting
        self._record_api_calls(ai_fetchers, ai_fetch_limit)
        self._record_api_calls(real_fetchers, real_fetch_limit)
        
        return all_samples
    
    def _record_api_calls(self, fetchers: List[BaseFetcher], limit: int):
        """Record API calls for rate limiting tracking."""
        current_time = time.time()
        
        for fetcher in fetchers:
            source_name = fetcher.get_source_name()
            # Estimate number of API calls based on limit
            # (each fetcher may make multiple queries)
            calls_made = min(limit, 10)  # Conservative estimate
            
            self.rate_limit_history[source_name].append((current_time, calls_made))
            
            # Clean up old history (keep last hour)
            cutoff = current_time - 3600
            self.rate_limit_history[source_name] = [
                (t, c) for t, c in self.rate_limit_history[source_name] if t > cutoff
            ]
    
    def get_active_sources(self) -> List[str]:
        """Get list of active source names."""
        return [fetcher.get_source_name() for fetcher in self.fetchers]
    
    def _get_latest_accuracy(self) -> Optional[float]:
        """Get the latest model validation accuracy.
        
        Returns:
            Latest validation accuracy (0.0-1.0) or None if no models trained yet
        """
        try:
            registry_path = Path(self.config["storage"]["models_path"]) / "registry.json"
            if not registry_path.exists():
                return None
            
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            
            if not registry:
                return None
            
            # Get latest model by timestamp
            latest = max(registry, key=lambda x: x.get("timestamp", ""))
            return latest.get("val_acc", latest.get("val_accuracy"))
            
        except Exception as e:
            logger.debug(f"Could not get latest accuracy: {e}")
            return None

