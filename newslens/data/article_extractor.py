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
        """Clean up extracted text to remove common noise and improve formatting."""
        if not text:
            return text
            
        # Common patterns to remove
        patterns_to_remove = [
            # Social media buttons and text
            r"(Copy Link|Print|Email|X|LinkedIn|Bluesky|Flipboard|Pinterest|Reddit)\s*(copied|Read More)",
            r"Share this (article|story|post)",
            r"Share on \w+",
            r"Follow us on \w+",
            r"Read on (Flipboard|Twitter|Facebook|LinkedIn|X)",
            r"View on (Flipboard|Twitter|Facebook|LinkedIn|X)",
            r"Share this article on (Flipboard|Twitter|Facebook|LinkedIn|X|Pinterest|Reddit)",
            r"View original article on (Flipboard|Twitter|Facebook|LinkedIn|X|Pinterest|Reddit)",
            
            # Social media and RSS feed references
            r"Flipboard",
            r"Read more on Flipboard",
            r"Read the original article on \w+",
            r"View the original article on \w+",
            r"Source: \w+",
            r"Via \w+ feed",
            r"From \w+ feed",
            r"RSS Feed",
            r"View in \w+",
            r"View on \w+",
            r"via \w+",
            
            # Navigation
            r"(Next|Previous) Article",
            # Comments sections markers
            r"\d+ Comments",
            r"Show Comments",
            r"Comment[s]? \(\d+\)",
            # Cookie notices
            r"We use cookies",
            r"Accept (all )?cookies",
            r"This website uses cookies",
            # Subscribe prompts
            r"Subscribe (now|today)",
            r"Sign up for our newsletter",
            r"Join our \w+ newsletter",
            # Loading indicators
            r"Loading\.\.\.",
            # Advertisement/sponsor text
            r"Advertisement",
            r"Sponsored",
            r"Sponsored Content",
            r"ADVERTISEMENT",
            # AP News specific patterns
            r"Copy Link copied",
            r"Print Email Read More",
            # Social media blocks
            r"SHARE THIS ARTICLE",
            r"Share Tweet",
            r"\d+ shares",
            # URLS that might be in text
            r"https?://[\w\d\./\-_]+"
        ]
        
        # Apply all the patterns
        for pattern in patterns_to_remove:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Remove excessive newlines (more than 2 in a row)
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Remove lines that are just social media service names or UI elements
        social_media = ["Facebook", "Twitter", "X", "Instagram", "LinkedIn", "Pinterest", "Reddit", "YouTube", "TikTok", "Threads", "Bluesky", "Flipboard"]
        ui_elements = ["close", "cancel", "accept", "continue reading", "read more", "read full article", "back to top", "more", "next", "previous"]
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
                
            # Skip social media platform names
            if line in social_media:
                continue
                
            # Skip very short lines that might be UI elements
            if len(line) < 4 and not line.isdigit():
                continue
                
            # Skip common UI elements and buttons text
            if line.lower() in ui_elements:
                continue
                
            # Skip advertisement markers
            if line.lower() in ['advertisement', 'ad', 'sponsored', 'advertisement.', 'sponsored content', 'click to read more', 'flipboard']:
                continue
                
            # Skip if the line is just a social media/RSS feed reference
            if any(service in line for service in ['Flipboard', 'RSS Feed', 'Subscribe', 'Newsletter']):
                if len(line.split()) < 5:  # Only skip short lines that are likely just labels
                    continue
                
            # Skip timestamp lines (often found in articles)
            if re.match(r'^\d{1,2}:\d{2} (AM|PM)|^[A-Za-z]{3} \d{1,2}, \d{4}|^\d{1,2}/\d{1,2}/\d{2,4}$', line):
                continue
                
            # Clean up lines with social sharing options
            if any(term in line for term in ['Copy Link', 'Share', 'Email', 'Print', 'Posted']) and len(line.split()) < 10:
                # If the line is mostly about sharing/copying, skip it
                share_terms = ['copy', 'link', 'share', 'email', 'print', 'facebook', 'twitter', 'posted', 'updated', 'flipboard', 'feed', 'read', 'view', 'original']
                words = line.lower().split()
                if words and sum(word in share_terms for word in words) / len(words) > 0.3:
                    continue
            
            # Some articles have strange encoding artifacts or random characters
            if len(line) < 10 and ('\ufffd' in line or re.search(r'[\x00-\x1F\x7F-\xFF]', line)):
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
    
    def _format_text_for_display(self, text: str) -> str:
        """Format text for display in the TUI.
        
        This ensures proper paragraph breaks and clean formatting.
        """
        if not text:
            return ""
        
        # Split into paragraphs (single or multiple newlines)
        paragraphs = re.split(r'\n+', text)
        
        # Filter out empty paragraphs and trim whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Join with double newlines for proper paragraph spacing
        return "\n\n".join(paragraphs)
    
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
            
            # Format for display
            text = self._format_text_for_display(text)
            
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
