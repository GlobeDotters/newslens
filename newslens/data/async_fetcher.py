"""
Asynchronous news fetching module for parallel downloading from sources.
"""

import asyncio
import time
import json
import aiohttp
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .fetcher import NewsItem
from .sources import NewsSource, SourceDatabase


class AsyncNewsFetcher:
    """Fetches news from various sources asynchronously."""
    
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
    
    async def fetch_feed(self, session: aiohttp.ClientSession, source: NewsSource) -> Tuple[List[NewsItem], Optional[Exception]]:
        """Fetch a single RSS feed asynchronously."""
        items = []
        error = None
        
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
                    return items, None
                except Exception as e:
                    # If cache loading fails, continue to fetch fresh data
                    error = e
        
        # If no RSS URL is available, we can't fetch news
        if not source.rss_url:
            return [], None
        
        try:
            # Fetch RSS feed
            async with session.get(source.rss_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse with feedparser (not async, but fast enough)
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries[:10]:  # Limit to 10 items per source
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
                    
                    return items, None
                else:
                    return [], Exception(f"HTTP Error: {response.status}")
        except Exception as e:
            return [], e
    
    async def fetch_from_source(self, source: NewsSource, max_items: int = 10) -> List[NewsItem]:
        """Fetch news from a specific source asynchronously."""
        async with aiohttp.ClientSession() as session:
            items, error = await self.fetch_feed(session, source)
            
            if error:
                print(f"Error fetching from {source.name}: {error}")
                return []
            
            return items[:max_items]
    
    async def fetch_by_country(self, country_code: str, max_per_source: int = 5) -> List[NewsItem]:
        """Fetch news from all sources in a specific country asynchronously."""
        sources = self.source_db.get_sources_by_country(country_code)
        
        if not sources:
            return []
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for each source
            tasks = [self.fetch_feed(session, source) for source in sources]
            
            # Gather results
            results = await asyncio.gather(*tasks)
            
            # Process results
            all_items = []
            for items, error in results:
                if items:
                    all_items.extend(items[:max_per_source])
            
            # Sort by publication date, newest first
            all_items.sort(key=lambda x: x.published_at, reverse=True)
            
            return all_items
