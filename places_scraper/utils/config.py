"""Configuration handling module."""
import json
import os
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file.
    
    Returns:
        Dict containing configuration settings
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as config_file:
        return json.load(config_file)

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration settings.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ['search_term', 'radius_km', 'categories', 'max_places']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")
        
    if not isinstance(config['categories'], list):
        raise ValueError("Categories must be a list")
        
    if not isinstance(config['max_places'], int) or config['max_places'] <= 0:
        raise ValueError("max_places must be a positive integer")
        
    if not isinstance(config['radius_km'], (int, float)) or config['radius_km'] <= 0:
        raise ValueError("radius_km must be a positive number") 