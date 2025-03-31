"""
News fetching module for different sources.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import feedparser

from .sources import NewsSource, SourceDatabase


class NewsItem:
    """Represents a single news article."""
    
    def __init__(
        self,
        title: str,
        url: str,
        source_name: str,
        published_at: datetime,
        description: Optional[str] = None,
        content: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.title = title
        self.url = url
        self.source_name = source_name
        self.published_at = published_at
        self.description = description
        self.content = content
        self.image_url = image_url
    
    def to_dict(self) -> Dict:
        """Convert news item to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "published_at": self.published_at.isoformat(),
            "description": self.description,
            "content": self.content,
            "image_url": self.image_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsItem':
        """Create a NewsItem from a dictionary."""
        return cls(
            title=data["title"],
            url=data["url"],
            source_name=data["source_name"],
            published_at=datetime.fromisoformat(data["published_at"]),
            description=data.get("description"),
            content=data.get("content"),
            image_url=data.get("image_url")
        )


class NewsFetcher:
    """Fetches news from various sources."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.source_db = SourceDatabase()
        
        if cache_dir is None:
            home = Path.home()
            self.cache_dir = home / ".cache" / "newslens"
        else:
            self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_from_source(self, source: NewsSource, max_items: int = 10) -> List[NewsItem]:
        """Fetch news from a specific source."""
        items = []
        
        # Check if we have a recent cache for this source
        cache_path = self.cache_dir / f"{source.country_code}_{source.name.replace(' ', '_')}.json"
        if cache_path.exists():
            # Check if cache is recent (less than 1 hour old)
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < 3600:  # 1 hour
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    
                    items = [NewsItem.from_dict(item) for item in data]
                    return items[:max_items]
                except Exception:
                    # If cache loading fails, continue to fetch fresh data
                    pass
        
        # If no RSS URL is available, we can't fetch news
        if not source.rss_url:
            return []
        
        try:
            # Fetch from RSS feed
            feed = feedparser.parse(source.rss_url)
            
            for entry in feed.entries[:max_items]:
                # Extract publication date
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])
                else:
                    published_at = datetime.now()
                
                # Extract description or summary
                description = None
                if hasattr(entry, 'description'):
                    description = entry.description
                elif hasattr(entry, 'summary'):
                    description = entry.summary
                
                # Create news item
                item = NewsItem(
                    title=entry.title,
                    url=entry.link,
                    source_name=source.name,
                    published_at=published_at,
                    description=description
                )
                
                items.append(item)
            
            # Cache the results
            with open(cache_path, 'w') as f:
                json.dump([item.to_dict() for item in items], f, indent=2)
            
            return items
        
        except Exception as e:
            print(f"Error fetching from {source.name}: {e}")
            return []
    
    def fetch_by_country(self, country_code: str, max_per_source: int = 5) -> List[NewsItem]:
        """Fetch news from all sources in a specific country."""
        sources = self.source_db.get_sources_by_country(country_code)
        all_items = []
        
        for source in sources:
            items = self.fetch_from_source(source, max_per_source)
            all_items.extend(items)
        
        # Sort by publication date, newest first
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        
        return all_items
