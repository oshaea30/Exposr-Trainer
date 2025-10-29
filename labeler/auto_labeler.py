"""Auto-labeler for assigning labels to images."""
import logging
from typing import Dict, Any

from labeler.exposr_core_client import ExposrCoreClient

logger = logging.getLogger(__name__)


class AutoLabeler:
    """Auto-labeler that uses detection services to label images."""
    
    def __init__(self, config: dict):
        """Initialize auto-labeler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        exporsr_config = config.get("exposr_core", {})
        
        self.exposr_client = ExposrCoreClient(
            endpoint=exporsr_config.get("endpoint", "http://localhost:8000/detect"),
            enabled=exporsr_config.get("enabled", True)
        )
        
        logger.info("Auto-labeler initialized")
    
    async def label(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Label an image with detection scores.
        
        Args:
            image_bytes: Image data
            metadata: Existing metadata dictionary
            
        Returns:
            Metadata dictionary with labels and detection scores
        """
        detectors = {}
        
        # Call Exposr-Core
        try:
            score = await self.exposr_client.detect(image_bytes)
            if score is not None:
                detectors["exposr_core"] = score
        except Exception as e:
            logger.error(f"Error in Exposr-Core detection: {e}")
        
        # Determine label based on detection scores
        metadata["detectors"] = detectors
        
        # Only set label if not already set by fetcher
        if not metadata.get("label"):
            if detectors:
                # Use the highest score
                max_score = max(detectors.values())
                metadata["label"] = "ai_generated" if max_score > 0.5 else "real"
                metadata["confidence"] = max_score
            else:
                # No detections available
                metadata["label"] = None
                metadata["confidence"] = None
        
        return metadata

