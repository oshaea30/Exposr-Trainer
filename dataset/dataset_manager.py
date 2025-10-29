"""Dataset manager for storing and managing image datasets."""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from sqlite3 import connect as sqlite_connect

from dataset.storage import StorageDriver, get_storage_driver

logger = logging.getLogger(__name__)


class DatasetManager:
    """Manages dataset storage, deduplication, and statistics."""
    
    def __init__(self, config: dict):
        """Initialize dataset manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.storage = get_storage_driver(config)
        
        # Initialize deduplication database
        self.db_path = Path(config["storage"]["local_path"]) / "dedupe.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_dedup_db()
        
        logger.info("Dataset manager initialized")
    
    def _init_dedup_db(self):
        """Initialize deduplication database."""
        with sqlite_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    hash TEXT PRIMARY KEY,
                    sample_id TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()
    
    def add_sample(self, image_bytes: bytes, metadata: Dict[str, Any]) -> bool:
        """Add a sample to the dataset with deduplication.
        
        Args:
            image_bytes: Image data
            metadata: Sample metadata
            
        Returns:
            True if sample was added, False if duplicate
        """
        sample_hash = metadata.get("hash")
        if not sample_hash:
            logger.error("Sample metadata missing hash")
            return False
        
        # Check for duplicates
        if self._is_duplicate(sample_hash):
            logger.debug(f"Duplicate sample detected: {sample_hash[:8]}")
            return False
        
        # Generate storage paths
        date_str = datetime.now().strftime("%Y/%m/%d")
        sample_id = metadata.get("id", f"sample_{datetime.utcnow().timestamp()}")
        
        image_path = f"images/{date_str}/{sample_id}.jpg"
        meta_path = f"meta/{date_str}/{sample_id}.json"
        
        # Save to storage
        try:
            self.storage.save_image(image_bytes, image_path)
            self.storage.save_metadata(metadata, meta_path)
            
            # Record in dedup database
            with sqlite_connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO samples (hash, sample_id, timestamp)
                    VALUES (?, ?, ?)
                """, (sample_hash, sample_id, metadata.get("timestamp")))
                conn.commit()
            
            logger.debug(f"Added sample: {sample_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving sample: {e}")
            return False
    
    def _is_duplicate(self, sample_hash: str) -> bool:
        """Check if sample is duplicate.
        
        Args:
            sample_hash: SHA-256 hash of sample
            
        Returns:
            True if duplicate
        """
        with sqlite_connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM samples WHERE hash = ?",
                (sample_hash,)
            )
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get dataset statistics.
        
        Returns:
            Dictionary with dataset statistics
        """
        # Count by label
        total = 0
        ai_generated = 0
        real = 0
        
        # Traverse metadata files
        meta_dir = Path(self.config["storage"]["local_path"]) / "meta"
        if meta_dir.exists():
            for meta_file in meta_dir.rglob("*.json"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    label = metadata.get("label")
                    total += 1
                    
                    if label == "ai_generated" or label == "ai":
                        ai_generated += 1
                    elif label == "real":
                        real += 1
                        
                except Exception as e:
                    logger.debug(f"Error reading metadata file: {e}")
                    continue
        
        return {
            "total": total,
            "ai_generated": ai_generated,
            "real": real,
            "unlabeled": total - ai_generated - real
        }
    
    def list_samples(self, label: Optional[str] = None, limit: int = 100) -> list:
        """List samples from the dataset.
        
        Args:
            label: Filter by label (optional)
            limit: Maximum number of samples to return
            
        Returns:
            List of sample metadata
        """
        samples = []
        meta_dir = Path(self.config["storage"]["local_path"]) / "meta"
        
        if not meta_dir.exists():
            return samples
        
        for meta_file in meta_dir.rglob("*.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                if label is None or metadata.get("label") == label:
                    samples.append(metadata)
                    
                    if len(samples) >= limit:
                        break
                        
            except Exception as e:
                logger.debug(f"Error reading metadata file: {e}")
                continue
        
        return samples

