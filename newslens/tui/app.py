"""
NewsLens TUI main application.
"""

import os
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, Label, ListItem, ListView, Input, Select, DataTable
from textual.widgets._data_table import RowKey
from textual import events, work
from textual.css.query import NoMatches

from rich.text import Text
from rich.console import RenderableType

from ..data.async_fetcher import AsyncNewsFetcher
from ..data.mock import MockNewsFetcher
from ..data.article_extractor import ArticleExtractor
from ..analysis.engine import NewsAnalyzer, CoverageAnalysis
from ..utils.config import Config


class HeadlinesTable(DataTable):
    """A table for displaying news headlines."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.add_column("Title", width=50)
        self.add_column("", width=1)  # Color indicator
        self.add_column("Left", width=5, key="left")
        self.add_column("Center", width=7, key="center")
        self.add_column("Right", width=6, key="right")
        self.add_column("Source", width=15, key="source")
        self.zebra_stripes = True

    def add_headline(self, idx: int, story: CoverageAnalysis) -> None:
        """Add a headline to the table."""
        title = story.story.title
        
        # Truncate long titles
        if len(title) > 70:
            title = title[:67] + "..."
        
        # Determine bias indicator
        bias_indicator = "●"
        if story.left_sources > 0 and story.right_sources == 0:
            bias_class = "bias-left"
        elif story.right_sources > 0 and story.left_sources == 0:
            bias_class = "bias-right"
        elif story.center_sources > 0 and story.left_sources == 0 and story.right_sources == 0:
            bias_class = "bias-center"
        else:
            bias_class = "bias-balanced"
            bias_indicator = "○"  # Balanced
        
        bias_text = Text(bias_indicator)
        bias_text.stylize(f"@{bias_class}")
        
        # Get first source for display
        first_source = story.story.sources[0] if story.story.sources else ""
        
        # Mark blindspots
        blindspot_text = ""
        if story.blindspot:
            blindspot_text = "⚠️ " + story.blindspot
        
        self.add_row(
            title,
            bias_text,
            str(story.left_sources),
            str(story.center_sources),
            str(story.right_sources),
            first_source,
            key=str(idx)
        )

    def clear_headlines(self) -> None:
        """Clear all headlines from the table."""
        self.clear()


class ArticleView(Static):
    """A widget for displaying article content."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.article_title = ""
        self.article_source = ""
        self.article_url = ""
        self.article_content = ""
    
    def load_article(self, title: str, source: str, url: str, content: str) -> None:
        """Load article content into the view."""
        self.article_title = title
        self.article_source = source
        self.article_url = url
        self.article_content = content
        self.update_content()
    
    def update_content(self) -> None:
        """Update the displayed content."""
        if not self.article_title:
            welcome_text = """
            [bold]Welcome to NewsLens Reader[/bold]
            
            Select an article from the headlines above to read it here.
            
            [dim]Keyboard shortcuts:[/dim]
            • Up/Down: Navigate headlines
            • Enter: Read selected article
            • R: Refresh headlines
            • F: Toggle between mock/real data
            • C: Change country
            • Q: Quit
            """
            self.update(welcome_text)
            return
        
        # Format the article content nicely
        content = f"[bold]{self.article_title}[/bold]\n\n"
        content += f"[italic]{self.article_source}[/italic] • [link={self.article_url}]{self.article_url}[/link]\n\n"
        
        # Process the article content
        paragraphs = self.article_content.split('\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            # Skip empty paragraphs
            if not paragraph.strip():
                continue
                
            # Format paragraphs nicely
            formatted_paragraph = paragraph.strip()
            formatted_paragraphs.append(formatted_paragraph)
        
        content += "\n\n".join(formatted_paragraphs)
        
        self.update(content)


class StatusBar(Static):
    """Status bar for displaying app status."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update("Ready")
    
    def set_status(self, status: str, style: str = "white") -> None:
        """Set the status text."""
        status_text = Text(status)
        status_text.stylize(f"[{style}]")
        
        # Add timestamp
        now = datetime.now().strftime("%H:%M:%S")
        timestamp = Text(f" [{now}]", style="dim")
        
        # Combine status and timestamp
        full_status = Text.assemble(status_text, timestamp)
        self.update(full_status)

class NewsLensApp(App):
    """The main NewsLens TUI application."""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("f", "toggle_mock", "Toggle Mock Data"),
        ("c", "cycle_country", "Change Country"),
        ("a", "read_article", "Read Article"),
    ]
    
    stories = reactive([])
    country_code = reactive("US")
    use_mock_data = reactive(True)
    
    def __init__(self, *args, **kwargs):
        # Get the path to the CSS file
        css_path = os.path.join(os.path.dirname(__file__), "styles.css")
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                self.CSS = f.read()
        
        super().__init__(*args, **kwargs)
        self.config = Config()
        self.use_mock_data = self.config.get("use_mock_data", True)
        self.country_code = self.config.get("country", "US")
        self.analyzer = NewsAnalyzer()
        self.article_extractor = ArticleExtractor()
    
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header(id="header")
        
        with Container():
            with Horizontal(id="controls"):
                yield Select(
                    [(c, c) for c in ["US", "UK", "CA", "AU"]], 
                    value=self.country_code,
                    id="country-select",
                    prompt="Country:"
                )
                yield Button("Refresh", id="refresh-button", variant="primary")
                yield Button(
                    "Mock Data: ON" if self.use_mock_data else "Mock Data: OFF",
                    id="mock-button",
                    variant="default"
                )
            
            yield HeadlinesTable(id="headlines-table")
            yield ArticleView(id="article-view")
            yield StatusBar(id="status-bar")
            
        yield Footer()
    
    def on_mount(self) -> None:
        """Event handler called when app is mounted."""
        self.refresh_headlines()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler for button presses."""
        button_id = event.button.id
        
        if button_id == "refresh-button":
            self.refresh_headlines()
        
        elif button_id == "mock-button":
            self.toggle_mock_data()
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Event handler for select changes."""
        select_id = event.select.id
        
        if select_id == "country-select":
            self.country_code = event.value
            self.config.set("country", self.country_code)
            self.refresh_headlines()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Event handler for table row selection."""
        try:
            idx = int(event.row_key.value)
            self.read_article(idx)
        except (ValueError, IndexError):
            self.notify("Invalid story selection", severity="error")
    
    def action_toggle_mock(self) -> None:
        """Toggle between mock and real data."""
        self.use_mock_data = not self.use_mock_data
        self.config.set("use_mock_data", self.use_mock_data)
        
        try:
            mock_button = self.query_one("#mock-button", Button)
            mock_button.label = "Mock Data: ON" if self.use_mock_data else "Mock Data: OFF"
        except NoMatches:
            pass
            
        self.refresh_headlines()
    
    def action_cycle_country(self) -> None:
        """Cycle through available countries."""
        countries = ["US", "UK", "CA", "AU"]
        current_idx = countries.index(self.country_code) if self.country_code in countries else 0
        next_idx = (current_idx + 1) % len(countries)
        self.country_code = countries[next_idx]
        
        try:
            country_select = self.query_one("#country-select", Select)
            country_select.value = self.country_code
        except NoMatches:
            pass
            
        self.config.set("country", self.country_code)
        self.refresh_headlines()
    
    def action_read_article(self) -> None:
        """Read the selected article."""
        headlines_table = self.query_one("#headlines-table", HeadlinesTable)
        row_key = headlines_table.cursor_row
        
        if row_key is not None:
            try:
                idx = int(row_key)
                self.read_article(idx)
            except (ValueError, IndexError):
                self.notify("Invalid story selection", severity="error")
    
    @work(exclusive=True)
    async def refresh_headlines(self) -> None:
        """Refresh headlines from selected sources."""
        self.set_status("Fetching headlines...", "bold yellow")
        
        headlines_table = self.query_one("#headlines-table", HeadlinesTable)
        headlines_table.clear_headlines()
        
        if self.use_mock_data:
            fetcher = MockNewsFetcher()
            news_items = fetcher.fetch_by_country(self.country_code)
        else:
            fetcher = AsyncNewsFetcher()
            news_items = await fetcher.fetch_by_country(self.country_code)
        
        if not news_items:
            self.set_status("No news found", "bold red")
            return
        
        self.set_status(f"Analyzing {len(news_items)} news items...", "bold cyan")
        # We need to run the analysis in a thread to avoid blocking the UI
        self.stories = await self.run_worker(self._analyze_stories, news_items)
        
        # Update the table with the stories
        for idx, story in enumerate(self.stories):
            headlines_table.add_headline(idx, story)
        
        now = datetime.now().strftime("%H:%M:%S")
        self.set_status(f"Updated at {now} - {len(self.stories)} stories found", "bold green")
    
    async def _analyze_stories(self, news_items: List[Any]) -> List[CoverageAnalysis]:
        """Analyze news items for coverage analysis."""
        # This runs in a separate thread
        stories = self.analyzer.analyze_coverage(news_items, self.country_code)
        return stories
    
    @work(exclusive=True)
    async def read_article(self, story_idx: int) -> None:
        """Read the selected article."""
        if story_idx < 0 or story_idx >= len(self.stories):
            self.notify(f"Story index {story_idx} is out of range", severity="error")
            return
        
        story = self.stories[story_idx]
        article = story.story.items[0]  # Get the first article in the cluster
        
        article_view = self.query_one("#article-view", ArticleView)
        
        title = article.title
        source = article.source_name
        url = article.url
        content = article.content
        
        # If no content, try to fetch it
        if not content:
            self.set_status(f"Fetching article from {source}...", "bold cyan")
            
            # Run the extraction in a worker to avoid blocking
            _, extracted_text, _ = await self.run_worker(
                self.article_extractor.extract_content_sync, url
            )
            
            if extracted_text:
                content = extracted_text
                article.content = content  # Update the article object
                self.set_status("Article loaded", "bold green")
            else:
                content = "Could not extract article content. Please visit the URL to read the full article."
                self.set_status("Could not load article", "bold red")
        
        # Update the article view
        article_view.load_article(title, source, url, content)
    
    def set_status(self, message: str, style: str = "white") -> None:
        """Set the status bar message."""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_status(message, style)


def run_app() -> None:
    """Run the NewsLens TUI application."""
    app = NewsLensApp()
    app.run()


if __name__ == "__main__":
    run_app()
