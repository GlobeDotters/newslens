"""
NewsLens TUI main application.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from functools import partial

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, DataTable, Select
from textual import events, work, on
from rich.text import Text

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
        self.add_column("Left", width=5)
        self.add_column("Center", width=7) 
        self.add_column("Right", width=6)
        self.add_column("Source", width=15)
        self.zebra_stripes = True

    def add_headline(self, idx: int, story: CoverageAnalysis) -> None:
        """Add a headline to the table."""
        title = story.story.title
        
        if len(title) > 70:
            title = title[:67] + "..."
        
        bias_indicator = "●"
        if story.left_sources > 0 and story.right_sources == 0:
            bias_class = "bias-left"
        elif story.right_sources > 0 and story.left_sources == 0:
            bias_class = "bias-right"
        elif story.center_sources > 0 and story.left_sources == 0 and story.right_sources == 0:
            bias_class = "bias-center"
        else:
            bias_class = "bias-balanced"
        
        bias_text = Text(bias_indicator)
        bias_text.stylize(bias_class)
        
        first_source = story.story.sources[0] if story.story.sources else ""
        
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


class ArticleView(ScrollableContainer):
    """A widget for displaying article content."""
    
    # Add keyboard bindings for scrolling
    BINDINGS = [
        ("up", "scroll_up", "Scroll Up"),
        ("down", "scroll_down", "Scroll Down"),
        ("k", "scroll_up", "Scroll Up"),
        ("j", "scroll_down", "Scroll Down"),
        ("page_up", "page_up", "Page Up"),
        ("page_down", "page_down", "Page Down"),
        ("home", "scroll_home", "Scroll to Top"),
        ("end", "scroll_end", "Scroll to Bottom"),
    ]
    
    article_title = reactive("")
    article_source = reactive("")
    article_url = reactive("")
    article_content = reactive("")

    def load_article(self, title: str, source: str, url: str, content: str) -> None:
        """Load article content into the view."""
        # First set properties
        self.article_title = title
        self.article_source = source
        self.article_url = url
        # Update content last to trigger the update
        self.article_content = content

    def watch_article_content(self) -> None:
        """Automatically update content when article_content changes."""
        self.update_content()
        
    async def action_scroll_up(self) -> None:
        """Scroll the content up."""
        self.scroll_up()
        
    async def action_scroll_down(self) -> None:
        """Scroll the content down."""
        self.scroll_down()
        
    async def action_page_up(self) -> None:
        """Scroll up by one page."""
        self.scroll_page_up()
        
    async def action_page_down(self) -> None:
        """Scroll down by one page."""
        self.scroll_page_down()
        
    async def action_scroll_home(self) -> None:
        """Scroll to the top of the content."""
        self.scroll_home()
        
    async def action_scroll_end(self) -> None:
        """Scroll to the bottom of the content."""
        self.scroll_end()

    def update_content(self) -> None:
        """Update the displayed content."""
        # Clear previous content
        if self.query(Static).first is not None:
            self.query(Static).remove()
        
        if not self.article_title:
            welcome_text = Text("""
Welcome to NewsLens Reader

Select an article from the headlines above to read it here.

Keyboard shortcuts:
• Up/Down or j/k: Navigate and scroll 
• Enter: Read selected article
• PgUp/PgDn: Page navigation
• Home/End: Jump to top/bottom
• Tab: Switch between headlines and article
• R: Refresh headlines 
• F: Toggle mock/real data
• C: Change country
• Q: Quit""")
            welcome_text.stylize("bold", 0, 26)
            welcome_text.stylize("dim", 115, 135)
            self.mount(Static(welcome_text))
            return
        
        # Create main content container
        article_content = Static()
        
        # Create main content with proper formatting
        main_content = [
            Text(f"\n{self.article_title}", style="bold"),
            Text(f"\n{self.article_source} • ", style="italic"),
            Text(f"{self.article_url}", style=f"underline link {self.article_url}"),
            Text("\n\n", style="")
        ]

        # Add article content paragraphs
        if self.article_content:
            paragraphs = self.article_content.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    main_content.append(Text(paragraph + "\n"))

        # Combine all elements and update
        final_content = Text.assemble(*main_content)
        article_content.update(final_content)
        
        # Mount the content to the scrollable container
        self.mount(article_content)


class StatusBar(Static):
    """Status bar for displaying app status."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_status("Ready")
    
    def set_status(self, status: str, style: str = "white") -> None:
        """Set the status text."""
        status_text = Text(status, style=style)
        now = datetime.now().strftime("%H:%M:%S")
        timestamp = Text(f" [{now}]", style="dim")
        self.update(Text.assemble(status_text, timestamp))


class NewsLensApp(App):
    """The main NewsLens TUI application."""
    
    CSS_PATH = "styles.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("f", "toggle_mock", "Toggle Mock Data"),
        ("c", "cycle_country", "Change Country"),  
        ("a", "read_article", "Read Article"),
        ("tab", "switch_focus", "Switch Focus"),
        ("shift+tab", "switch_focus_backward", "Switch Focus Backward"),
    ]
    
    stories = reactive([])
    country_code = reactive("US")
    use_mock_data = reactive(True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = Config()
        self.use_mock_data = self.config.get("use_mock_data", True)
        self.country_code = self.config.get("country", "US")
        self.analyzer = NewsAnalyzer()  
        self.article_extractor = ArticleExtractor()
        self._analysis_worker = None
    
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        yield Footer()
        yield Container(
            Horizontal(
                Select(
                    [(c, c) for c in ["US", "UK", "CA", "AU"]],
                    value=self.country_code, 
                    id="country-select",
                    prompt="Country:",
                    classes="country-select"
                ),
                Button("Refresh", id="refresh-button", variant="primary"),
                Button(
                    "Mock Data: ON" if self.use_mock_data else "Mock Data: OFF",
                    id="mock-button", 
                    variant="default"
                )
            ),
            HeadlinesTable(id="headlines-table"),
            ArticleView(id="article-view"),
            id="main-container"   
        )
        yield StatusBar(id="status-bar")
    
    async def on_mount(self) -> None:
        """Event handler called when app is mounted."""  
        self.query_one(HeadlinesTable).focus()
        self.refresh_headlines()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler for button presses."""
        button_id = event.button.id
        if button_id == "refresh-button":
            self.refresh_headlines()
        elif button_id == "mock-button":
            await self.action_toggle_mock()
    
    async def on_select_changed(self, event: Select.Changed) -> None:  
        """Event handler for select changes."""
        self.country_code = event.value
        self.config.set("country", self.country_code)
        self.refresh_headlines()
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Event handler for table row selection."""
        if event.row_key is not None:
            try:
                idx = int(event.row_key.value)
                await self.on_read_article(idx)
            except (ValueError, IndexError):
                self.notify("Invalid story selection", severity="error")
        
    async def action_toggle_mock(self) -> None:
        """Toggle between mock and real data."""  
        self.use_mock_data = not self.use_mock_data  
        self.config.set("use_mock_data", self.use_mock_data)
        self.refresh_headlines()
    
    async def action_cycle_country(self) -> None:
        """Cycle through available countries."""
        countries = ["US", "UK", "CA", "AU"]
        current_idx = countries.index(self.country_code) if self.country_code in countries else 0
        next_idx = (current_idx + 1) % len(countries)
        self.country_code = countries[next_idx]
        self.config.set("country", self.country_code)
        self.refresh_headlines()

    @work
    async def refresh_headlines(self) -> None:
        """Worker method to refresh headlines."""
        self.set_status("Fetching headlines...", "yellow bold")
        
        headlines_table = self.query_one(HeadlinesTable)
        headlines_table.clear_headlines()
        
        try:
            if self.use_mock_data:
                fetcher = MockNewsFetcher()  
                news_items = fetcher.fetch_by_country(self.country_code)
            else:
                fetcher = AsyncNewsFetcher()
                news_items = await fetcher.fetch_by_country(self.country_code)
            
            if not news_items:
                self.set_status("No news found", "red bold")
                return
            
            self.set_status(f"Analyzing {len(news_items)} news items...", "cyan bold")
            
            # Run blocking analysis in a thread
            analyze = partial(self.analyzer.analyze_coverage, news_items, self.country_code)
            self._analysis_worker = self.run_worker(analyze, thread=True, exclusive=False)
            await self._analysis_worker.wait()
            
            if self._analysis_worker.result is not None:
                self.stories = self._analysis_worker.result
                for idx, story in enumerate(self.stories):
                    headlines_table.add_headline(idx, story)
                
                now = datetime.now().strftime("%H:%M")
                self.set_status(f"Updated at {now} - {len(self.stories)} stories", "green bold")
        
        except Exception as e:
            self.set_status(f"Error: {str(e)}", "red bold")

    async def on_read_article(self, idx: int) -> None:
        """Handle reading an article."""
        if not (0 <= idx < len(self.stories)):
            self.notify(f"Story index {idx} is out of range", severity="error")
            return
    
        story = self.stories[idx]
        article = story.story.items[0]
        
        article_view = self.query_one(ArticleView)
        article_view.load_article(
            title=article.title,
            source=article.source_name,
            url=article.url,
            content=article.content or ""
        )
        
        if not article.content:
            self.set_status(f"Fetching from {article.source_name}...", "cyan bold")
            try:
                _, content, _ = await self.article_extractor.extract_content(article.url)
                if content:
                    article.content = content
                    article_view.article_content = content
                    self.set_status("Article loaded", "green bold")
                else:
                    article_view.article_content = "Could not extract article content."
                    self.set_status("Could not load article", "red bold")
            except Exception as e: 
                article_view.article_content = f"Error loading article: {str(e)}"
                self.set_status(f"Error loading article: {str(e)}", "red bold")
        else:
            article_view.article_content = article.content
            self.set_status("Showing cached content", "green bold")
        
        # Focus the article view after loading
        article_view.focus()

    def set_status(self, message: str, style: str = "white") -> None:
        """Set the status bar message."""  
        self.query_one(StatusBar).set_status(message, style)
    
    async def action_switch_focus(self) -> None:
        """Switch focus between headlines table and article view."""
        if self.focused is self.query_one(HeadlinesTable):
            self.query_one(ArticleView).focus()
        else:
            self.query_one(HeadlinesTable).focus()
    
    async def action_switch_focus_backward(self) -> None:
        """Switch focus in reverse order."""
        await self.action_switch_focus()


def run_app() -> None:
    """Run the NewsLens TUI application."""
    app = NewsLensApp()
    app.run()


if __name__ == "__main__":
    run_app()