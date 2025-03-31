"""
Article content extraction module.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
import asyncio
import aiohttp
import newspaper
from newspaper import Article
import re

class ArticleExtractor:
    """Extracts article content from news websites."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the article extractor with cache directory."""
        if cache_dir is None:
            home = Path.home()
            self.cache_dir = home / ".cache" / "newslens" / "articles"
        else:
            self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, url: str) -> Path:
        """Get the cache path for a URL."""
        # Create a hash of the URL to use as the filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"
    
    def _is_cached(self, url: str) -> bool:
        """Check if an article is cached."""
        cache_path = self._get_cache_path(url)
        return cache_path.exists()
    
    def _get_from_cache(self, url: str) -> Optional[Dict]:
        """Get article content from cache."""
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading article from cache: {e}")
            return None
    
    def _save_to_cache(self, url: str, content: Dict):
        """Save article content to cache."""
        cache_path = self._get_cache_path(url)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
        except Exception as e:
            print(f"Error saving article to cache: {e}")
            
    def _clean_text(self, text: str) -> str:
        """Clean up extracted text to remove common noise."""
        if not text:
            return text
            
        # Common patterns to remove
        patterns_to_remove = [
            # Social media buttons and text
            r"(Copy Link|Print|Email|X|LinkedIn|Bluesky|Flipboard|Pinterest|Reddit)\s*(copied|Read More)",
            r"Share this article",
            r"Share on \w+",
            # Navigation
            r"(Next|Previous) Article",
            # Comments sections markers
            r"\d+ Comments",
            r"Show Comments",
            # Cookie notices
            r"We use cookies",
            r"Accept (all )?cookies",
            # Subscribe prompts
            r"Subscribe (now|today)",
            r"Sign up for our newsletter",
            # Loading indicators
            r"Loading\.\.\."   ,
            # AP News specific patterns
            r"Copy Link copied",
            r"Print Email Read More"         
        ]
        
        # Apply all the patterns
        for pattern in patterns_to_remove:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Remove excessive newlines (more than 2 in a row)
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Remove lines that are just social media service names
        social_media = ["Facebook", "Twitter", "Instagram", "LinkedIn", "Pinterest", "Reddit", "YouTube", "TikTok"]
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines or lines that are just social media names
            if not line or line in social_media:
                continue
            # Skip very short lines that might be UI elements
            if len(line) < 4 and not line.isdigit():
                continue
            # Skip advertisement markers
            if line.lower() in ['advertisement', 'ad', 'sponsored', 'advertisement.', 'sponsored content']:
                continue
            # Remove lines with just button text or common UI elements
            if line.lower() in ['close', 'cancel', 'accept', 'continue reading', 'read more']:
                continue
            
            # Clean up lines with Copy Link etc.
            if any(term in line for term in ['Copy Link', 'Share', 'Email', 'Print']):
                # If the line is mostly about sharing/copying, skip it
                share_terms = ['copy', 'link', 'share', 'email', 'print', 'facebook', 'twitter']
                words = line.lower().split()
                if len(words) < 10 and sum(word in share_terms for word in words) / len(words) > 0.3:
                    continue
            
            cleaned_lines.append(line)
        
        # Process lines to find and remove footers
        # Most articles have bylines, copyright notices, etc. at the end
        end_markers = [
            "©", "copyright", "all rights reserved", "associated press", 
            "follow us on", "follow ap", "ap news", "terms of use", "privacy policy"
        ]
        
        # Find the first line that might be a footer
        footer_start_idx = len(cleaned_lines)
        for i, line in enumerate(cleaned_lines):
            line_lower = line.lower()
            if any(marker in line_lower for marker in end_markers):
                # If this is in the last 25% of the article, it's likely a footer
                if i > len(cleaned_lines) * 0.75:
                    footer_start_idx = i
                    break
        
        # Remove the footer if found
        cleaned_text = "\n\n".join(cleaned_lines[:footer_start_idx])
        
        return cleaned_text
    
    def extract_content_sync(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract article content synchronously."""
        # Check cache first
        if self._is_cached(url):
            cached = self._get_from_cache(url)
            if cached:
                return cached.get("title"), cached.get("text"), cached.get("html")
        
        try:
            # Download and parse article
            article = Article(url)
            article.download()
            article.parse()
            
            # Extract content
            title = article.title
            text = article.text
            html = article.html
            
            # Special handling for AP News
            if "apnews.com" in url:
                # AP News articles often have a specific format
                import bs4
                soup = bs4.BeautifulSoup(html, 'html.parser')
                
                # Find the main article content
                story_content = soup.find('div', class_=['Article', 'story-body'])
                if story_content:
                    paragraphs = story_content.find_all('p')
                    if paragraphs:
                        text = '\n\n'.join([p.get_text() for p in paragraphs])
            
            # Clean the text
            text = self._clean_text(text)
            
            # Save to cache
            self._save_to_cache(url, {
                "title": title,
                "text": text,
                "html": html
            })
            
            return title, text, html
        except Exception as e:
            print(f"Error extracting article content: {e}")
            return None, None, None
    
    async def extract_content(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract article content asynchronously."""
        # Check cache first
        if self._is_cached(url):
            cached = self._get_from_cache(url)
            if cached:
                return cached.get("title"), cached.get("text"), cached.get("html")
        
        # Use asyncio to run the CPU-bound task in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract_content_sync, url)
