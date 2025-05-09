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
    required_fields = ['textQuery', 'radiusKm', 'categories', 'maxPlaces']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")
        
    if not isinstance(config['categories'], list):
        raise ValueError("Categories must be a list")
        
    if not isinstance(config['maxPlaces'], int) or config['maxPlaces'] <= 0:
        raise ValueError("maxPlaces must be a positive integer")
        
    if not isinstance(config['radiusKm'], (int, float)) or config['radiusKm'] <= 0:
        raise ValueError("radiusKm must be a positive number") 