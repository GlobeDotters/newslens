"""
Configuration management for NewsLens.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pycountry


class Config:
    """Manages user configuration for NewsLens."""
    
    def __init__(self):
        # Get config directory
        home = Path.home()
        self.config_dir = home / ".config" / "newslens"
        self.config_file = self.config_dir / "config.json"
        
        # Create directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        # Try to determine country from locale
        country_code = self._get_system_country() or "US"
        
        config = {
            "country": country_code,
            "max_items_per_source": 5,
            "cache_hours": 1,
            "bias_threshold": 0.2,  # For blindspot detection
            "use_mock_data": True,  # Default to mock data for development
            "ui": {
                "color_theme": "default",
                "show_descriptions": True
            }
        }
        
        # Save the default config
        self.save(config)
        
        return config
    
    def _get_system_country(self) -> Optional[str]:
        """Try to determine the country from system locale."""
        try:
            # This is a simplistic approach and may not work on all systems
            locale = os.environ.get('LANG', '')
            if '_' in locale:
                country = locale.split('_')[1].split('.')[0]
                if len(country) == 2:
                    return country
        except Exception:
            pass
        
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self.config[key] = value
        self.save()
    
    def save(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file."""
        if config is not None:
            self.config = config
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_country_name(self) -> str:
        """Get the full name of the configured country."""
        country_code = self.get("country", "US")
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            if country:
                return country.name
        except Exception:
            pass
        
        return "United States"  # Default fallback
