"""Base fetcher abstraction for all image sources."""
from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseFetcher(ABC):
    """Abstract base class for all image fetchers."""
    
    @abstractmethod
    def fetch_images(self, limit: int = 25) -> List[Tuple[bytes, dict]]:
        """Fetch images from the source.
        
        Args:
            limit: Maximum number of images to fetch
            
        Returns:
            List of (image_bytes, metadata) tuples
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the source name (e.g., 'unsplash', 'pexels').
        
        Returns:
            Source name string
        """
        pass

