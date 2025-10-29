"""Model synchronization with Exposr-Core."""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def push_latest_model(config: dict) -> Optional[Dict[str, Any]]:
    """Get information about the latest trained model for Exposr-Core.
    
    This is a placeholder function that Exposr-Core can call to discover
    the latest model version and download it.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with latest model info or None
    """
    registry_path = Path(config["storage"]["models_path"]) / "registry.json"
    
    if not registry_path.exists():
        return None
    
    # Load registry
    with open(registry_path, 'r') as f:
        registry = json.load(f)
    
    if not registry:
        return None
    
    # Get latest model entry
    latest_entry = None
    latest_timestamp = None
    
    for entry in registry:
        timestamp_str = entry.get("timestamp", "")
        if timestamp_str and (not latest_timestamp or timestamp_str > latest_timestamp):
            latest_timestamp = timestamp_str
            latest_entry = entry
    
    if not latest_entry:
        return None
    
    # Return model info for Exposr-Core
    model_info = {
        "model_version": latest_entry.get("version"),
        "model_name": latest_entry.get("model"),
        "timestamp": latest_entry.get("timestamp"),
        "metrics": {
            "val_accuracy": latest_entry.get("val_acc"),
            "val_auc": latest_entry.get("val_auc"),
            "val_loss": latest_entry.get("val_loss"),
            "dataset_size": latest_entry.get("dataset_size")
        },
        "download_url": f"models/{latest_entry.get('model')}/{latest_entry.get('version')}/weights.pt"
    }
    
    logger.info(f"Latest model info for Exposr-Core: version {latest_entry.get('version')}")
    
    return model_info


def get_model_path(config: dict, model_name: str, version: str) -> str:
    """Get the path to a specific model version.
    
    Args:
        config: Configuration dictionary
        model_name: Name of the model
        version: Version string
        
    Returns:
        Path to model weights
    """
    models_path = Path(config["storage"]["models_path"])
    model_path = models_path / model_name / version / "weights.pt"
    
    return str(model_path)


def list_available_models(config: dict) -> list:
    """List all available trained models.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of model entries
    """
    registry_path = Path(config["storage"]["models_path"]) / "registry.json"
    
    if not registry_path.exists():
        return []
    
    with open(registry_path, 'r') as f:
        return json.load(f)

