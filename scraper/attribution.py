"""Attribution validation and formatting utilities."""
from typing import Dict, Any


def validate_usage_rights(source: str) -> bool:
    """Validate that source has redistribution permissions.
    
    Args:
        source: Source name (e.g., 'unsplash', 'pexels')
        
    Returns:
        True if source is allowed
    """
    allowed_sources = ["unsplash", "pexels", "civitai"]
    return source in allowed_sources


def format_attribution(metadata: Dict[str, Any]) -> str:
    """Format attribution string for display.
    
    Args:
        metadata: Metadata dictionary containing attribution
        
    Returns:
        Formatted attribution string
    """
    attribution = metadata.get("attribution", {})
    photographer = attribution.get("photographer", "Unknown")
    platform = attribution.get("platform", "Unknown")
    
    return f"Photo by {photographer} on {platform}"


def is_allowed_for_training(source: str) -> bool:
    """Check if source is allowed for model training.
    
    Args:
        source: Source name
        
    Returns:
        True if source can be used for training
    """
    training_allowed_sources = ["unsplash", "pexels", "civitai"]
    return source in training_allowed_sources

