"""Model registry for tracking training runs and versions."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for tracking model training runs and versions."""
    
    def __init__(self, config: dict):
        """Initialize model registry.
        
        Args:
            config: Configuration dictionary
        """
        self.models_path = Path(config["storage"]["models_path"])
        self.registry_path = self.models_path / "registry.json"
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize registry file
        if not self.registry_path.exists():
            self._init_registry()
        
        logger.info("Model registry initialized")
    
    def _init_registry(self):
        """Initialize registry file with empty array."""
        with open(self.registry_path, 'w') as f:
            json.dump([], f)
    
    def register(self, model_name: str, metrics: Dict[str, Any]) -> str:
        """Register a new model training run.
        
        Args:
            model_name: Name of the model (e.g., "vit", "freqnet")
            metrics: Training metrics
            
        Returns:
            Version string for the registered model
        """
        # Generate version
        existing_entries = self.list_models(model_name)
        version = f"v{len(existing_entries) + 1}"
        
        # Create registry entry
        entry = {
            "model": model_name,
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            **metrics
        }
        
        # Add to registry
        with open(self.registry_path, 'r') as f:
            registry = json.load(f)
        
        registry.append(entry)
        
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"Registered model: {model_name} {version}")
        return version
    
    def list_models(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered models.
        
        Args:
            model_name: Filter by model name (optional)
            
        Returns:
            List of model entries
        """
        with open(self.registry_path, 'r') as f:
            registry = json.load(f)
        
        if model_name:
            return [entry for entry in registry if entry.get("model") == model_name]
        
        return registry
    
    def get_latest(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Latest model entry or None
        """
        models = self.list_models(model_name)
        if not models:
            return None
        
        # Sort by timestamp and return latest
        models.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return models[0]
    
    def get_model_info(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model version.
        
        Args:
            model_name: Name of the model
            version: Version string
            
        Returns:
            Model entry or None
        """
        models = self.list_models(model_name)
        for model in models:
            if model.get("version") == version:
                return model
        return None

