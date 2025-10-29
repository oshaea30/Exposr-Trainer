"""Configuration loader with YAML and environment variable support."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML and environment variables.
    
    Returns:
        Dict containing the merged configuration.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Load YAML config
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    if os.getenv("STORAGE_DRIVER"):
        config["storage"]["driver"] = os.getenv("STORAGE_DRIVER")
    
    if os.getenv("SCRAPE_EVERY_HOURS"):
        config["scheduler"]["scrape_interval_hours"] = int(os.getenv("SCRAPE_EVERY_HOURS"))
    
    if os.getenv("TRAIN_EVERY_DAYS"):
        config["scheduler"]["train_interval_days"] = int(os.getenv("TRAIN_EVERY_DAYS"))
    
    if os.getenv("EXPOSR_CORE_ENDPOINT"):
        config["exposr_core"]["endpoint"] = os.getenv("EXPOSR_CORE_ENDPOINT")
    
    return config


def load_sources_config() -> Dict[str, Any]:
    """Load sources configuration from YAML.
    
    Returns:
        Dict containing the sources configuration.
    """
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    with open(sources_path, 'r') as f:
        return yaml.safe_load(f)

