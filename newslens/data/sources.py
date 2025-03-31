"""
News sources and bias classification handling.
"""

import json
import os
import pkg_resources
from pathlib import Path
from typing import Dict, List, Optional, Union

class NewsSource:
    """A news source with bias and reliability information."""
    
    def __init__(
        self,
        name: str,
        url: str,
        country_code: str,
        bias_score: float,  # -10 (far left) to +10 (far right)
        reliability_score: float,  # 0 (unreliable) to 10 (highly reliable)
        rss_url: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ):
        self.name = name
        self.url = url
        self.country_code = country_code
        self.bias_score = bias_score
        self.reliability_score = reliability_score
        self.rss_url = rss_url
        self.api_endpoint = api_endpoint
    
    @property
    def bias_category(self) -> str:
        """Return the bias category based on the bias score."""
        if self.bias_score < -6.7:
            return "Far Left"
        elif self.bias_score < -3.3:
            return "Left"
        elif self.bias_score < 3.3:
            return "Center"
        elif self.bias_score < 6.7:
            return "Right"
        else:
            return "Far Right"
    
    @property
    def reliability_category(self) -> str:
        """Return the reliability category based on the reliability score."""
        if self.reliability_score < 3.3:
            return "Low"
        elif self.reliability_score < 6.7:
            return "Medium"
        else:
            return "High"
    
    def to_dict(self) -> Dict:
        """Convert the source to a dictionary for serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "country_code": self.country_code,
            "bias_score": self.bias_score,
            "reliability_score": self.reliability_score,
            "rss_url": self.rss_url,
            "api_endpoint": self.api_endpoint
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsSource':
        """Create a NewsSource from a dictionary."""
        return cls(
            name=data["name"],
            url=data["url"],
            country_code=data["country_code"],
            bias_score=data["bias_score"],
            reliability_score=data["reliability_score"],
            rss_url=data.get("rss_url"),
            api_endpoint=data.get("api_endpoint")
        )


class SourceDatabase:
    """Manager for news sources database."""
    
    def __init__(self):
        self.sources: Dict[str, List[NewsSource]] = {}
        self.data_dir = self._get_data_dir()
        self._load_sources()
    
    def _get_data_dir(self) -> Path:
        """Get the data directory, creating it if necessary."""
        # First, try to use user's config directory
        home = Path.home()
        data_dir = home / ".config" / "newslens"
        
        # Create directory if it doesn't exist
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Fall back to package data directory
                data_dir = Path(pkg_resources.resource_filename('newslens', 'data'))
        
        return data_dir
    
    def _load_sources(self):
        """Load sources from the database file."""
        db_path = self.data_dir / "sources.json"
        
        # If user database doesn't exist, copy from package data
        if not db_path.exists():
            default_db = pkg_resources.resource_filename('newslens', 'data/default_sources.json')
            if os.path.exists(default_db):
                with open(default_db, 'r') as f:
                    default_data = json.load(f)
                
                # Write to user's data directory
                with open(db_path, 'w') as f:
                    json.dump(default_data, f, indent=2)
                
                # Load the data
                for country_code, sources_data in default_data.items():
                    self.sources[country_code] = [
                        NewsSource.from_dict(src) for src in sources_data
                    ]
            else:
                # Create empty database
                self.sources = {}
        else:
            # Load from user's database
            try:
                with open(db_path, 'r') as f:
                    data = json.load(f)
                
                for country_code, sources_data in data.items():
                    self.sources[country_code] = [
                        NewsSource.from_dict(src) for src in sources_data
                    ]
            except Exception as e:
                print(f"Error loading sources database: {e}")
                self.sources = {}
    
    def save(self):
        """Save the current sources to the database file."""
        db_path = self.data_dir / "sources.json"
        
        # Convert to serializable format
        data = {}
        for country_code, sources in self.sources.items():
            data[country_code] = [src.to_dict() for src in sources]
        
        # Save to file
        with open(db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_sources_by_country(self, country_code: str) -> List[NewsSource]:
        """Get list of sources for a specific country."""
        return self.sources.get(country_code, [])
    
    def add_source(self, source: NewsSource):
        """Add a new source to the database."""
        if source.country_code not in self.sources:
            self.sources[source.country_code] = []
        
        self.sources[source.country_code].append(source)
        self.save()
    
    def remove_source(self, country_code: str, source_name: str) -> bool:
        """Remove a source from the database."""
        if country_code not in self.sources:
            return False
        
        initial_count = len(self.sources[country_code])
        self.sources[country_code] = [
            src for src in self.sources[country_code] 
            if src.name != source_name
        ]
        
        if len(self.sources[country_code]) < initial_count:
            self.save()
            return True
        return False
    
    def get_available_countries(self) -> List[str]:
        """Get list of country codes with available sources."""
        return list(self.sources.keys())


# Create a default sources list for initial setup
def create_default_sources():
    """Create a default list of sources for initial setup."""
    sources = {
        "US": [
            {
                "name": "CNN",
                "url": "https://www.cnn.com",
                "country_code": "US",
                "bias_score": -5.0,
                "reliability_score": 7.0,
                "rss_url": "http://rss.cnn.com/rss/cnn_topstories.rss"
            },
            {
                "name": "Fox News",
                "url": "https://www.foxnews.com",
                "country_code": "US",
                "bias_score": 7.0,
                "reliability_score": 6.0,
                "rss_url": "https://moxie.foxnews.com/google-publisher/latest.xml"
            },
            {
                "name": "AP News",
                "url": "https://apnews.com",
                "country_code": "US",
                "bias_score": 0.0,
                "reliability_score": 9.0,
                "rss_url": "https://rsshub.app/apnews/topics/apf-topnews"
            },
            {
                "name": "New York Times",
                "url": "https://www.nytimes.com",
                "country_code": "US",
                "bias_score": -3.0,
                "reliability_score": 8.0,
                "rss_url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
            },
            {
                "name": "Wall Street Journal",
                "url": "https://www.wsj.com",
                "country_code": "US",
                "bias_score": 4.0,
                "reliability_score": 8.0,
                "rss_url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
            }
        ],
        "UK": [
            {
                "name": "BBC",
                "url": "https://www.bbc.co.uk/news",
                "country_code": "UK",
                "bias_score": -1.0,
                "reliability_score": 9.0,
                "rss_url": "http://feeds.bbci.co.uk/news/rss.xml"
            },
            {
                "name": "The Guardian",
                "url": "https://www.theguardian.com",
                "country_code": "UK",
                "bias_score": -6.0,
                "reliability_score": 7.5,
                "rss_url": "https://www.theguardian.com/uk/rss"
            },
            {
                "name": "Daily Mail",
                "url": "https://www.dailymail.co.uk",
                "country_code": "UK",
                "bias_score": 6.0,
                "reliability_score": 4.0,
                "rss_url": "https://www.dailymail.co.uk/home/index.rss"
            }
        ]
    }
    
    return sources
