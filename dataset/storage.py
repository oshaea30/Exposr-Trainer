"""Storage driver abstraction for local and S3 storage."""
import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, BinaryIO
import json
import logging

logger = logging.getLogger(__name__)


class StorageDriver(ABC):
    """Abstract storage driver interface."""
    
    @abstractmethod
    def save_image(self, image_bytes: bytes, relative_path: str) -> str:
        """Save image bytes to storage.
        
        Args:
            image_bytes: Image data
            relative_path: Relative path to save to
            
        Returns:
            Full path where image was saved
        """
        pass
    
    @abstractmethod
    def save_metadata(self, metadata: dict, relative_path: str) -> str:
        """Save metadata to storage.
        
        Args:
            metadata: Metadata dictionary
            relative_path: Relative path to save to
            
        Returns:
            Full path where metadata was saved
        """
        pass
    
    @abstractmethod
    def list_images(self, prefix: str) -> List[str]:
        """List image paths with given prefix.
        
        Args:
            prefix: Prefix to filter by
            
        Returns:
            List of image paths
        """
        pass
    
    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """Check if a path exists in storage.
        
        Args:
            path: Path to check
            
        Returns:
            True if path exists
        """
        pass


class LocalStorage(StorageDriver):
    """Local filesystem storage driver."""
    
    def __init__(self, config: dict):
        """Initialize local storage.
        
        Args:
            config: Configuration dictionary
        """
        self.base_path = Path(config["storage"]["local_path"])
        self.models_path = Path(config["storage"]["models_path"])
        
        # Create directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.models_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, image_bytes: bytes, relative_path: str) -> str:
        """Save image to local filesystem."""
        full_path = self.base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(image_bytes)
        
        return str(full_path)
    
    def save_metadata(self, metadata: dict, relative_path: str) -> str:
        """Save metadata to local filesystem."""
        full_path = self.base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return str(full_path)
    
    def list_images(self, prefix: str) -> List[str]:
        """List images with given prefix."""
        prefix_path = self.base_path / prefix
        if not prefix_path.exists():
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        images = []
        
        for file_path in prefix_path.rglob('*'):
            if file_path.suffix.lower() in image_extensions:
                images.append(str(file_path.relative_to(self.base_path)))
        
        return images
    
    def path_exists(self, path: str) -> bool:
        """Check if path exists."""
        full_path = self.base_path / path
        return full_path.exists()


class S3Storage(StorageDriver):
    """S3 storage driver (stubbed for future implementation)."""
    
    def __init__(self, config: dict):
        """Initialize S3 storage.
        
        Args:
            config: Configuration dictionary
        """
        logger.warning("S3Storage is stubbed and not yet implemented")
        self.bucket = config["storage"]["s3_bucket"]
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    def save_image(self, image_bytes: bytes, relative_path: str) -> str:
        """Save image to S3 (stubbed)."""
        logger.warning("S3 save_image not implemented")
        return f"s3://{self.bucket}/{relative_path}"
    
    def save_metadata(self, metadata: dict, relative_path: str) -> str:
        """Save metadata to S3 (stubbed)."""
        logger.warning("S3 save_metadata not implemented")
        return f"s3://{self.bucket}/{relative_path}"
    
    def list_images(self, prefix: str) -> List[str]:
        """List images in S3 (stubbed)."""
        logger.warning("S3 list_images not implemented")
        return []
    
    def path_exists(self, path: str) -> bool:
        """Check if path exists in S3 (stubbed)."""
        logger.warning("S3 path_exists not implemented")
        return False


def get_storage_driver(config: dict) -> StorageDriver:
    """Get the appropriate storage driver based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Storage driver instance
    """
    driver = os.getenv("STORAGE_DRIVER", config["storage"]["driver"])
    
    if driver == "s3":
        return S3Storage(config)
    
    return LocalStorage(config)

