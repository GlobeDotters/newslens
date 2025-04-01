"""
NewsLens TUI main application.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import partial
import re
import shutil
from pathlib import Path

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
from ..data.sources import SourceDatabase
from ..analysis.engine import NewsAnalyzer, CoverageAnalysis
from ..utils.config import Config


class HeadlinesTable(DataTable):
    """A table for displaying news headlines."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.add_column("Title", width=35)
        self.add_column("", width=1)  # Color indicator
        self.add_column("Political Spectrum", width=20)
        self.add_column("Source", width=16)
        self.add_column("Published", width=16)
        self.zebra_stripes = True

    def add_headline(self, idx: int, story: CoverageAnalysis) -> None:
        """Add a headline to the table."""
        title = story.story.title
        
        if len(title) > 35:
            title = title[:32] + "..."
        
        # Create bias indicator
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
        
        # Create a 10-square bar that shows the political spectrum
        total_sources = story.left_sources + story.center_sources + story.right_sources
        if total_sources > 0:
            # Get the actual bias scores from the sources
            source_db = SourceDatabase()
            bias_scores = []
            
            # For each news source in the story, get its bias score
            for item in story.story.items:
                source_name = item.source_name
                sources = source_db.get_sources_by_name(source_name)
                if sources and len(sources) > 0:
                    bias_scores.append(sources[0].bias_score)
            
            # Create a base 10-square empty bar (score runs from -10 to +10)
            base_bar = "□" * 10  # □□□□□□□□□□
            bias_bar = Text(base_bar, style="dim")
            
            # 10 squares represent the full -10 to +10 scale
            # Squares 0-3 for left, 4-6 for center, 7-9 for right
            # Calculate which squares to fill based on source bias scores
            filled_squares = set()
            
            for score in bias_scores:
                # Convert the -10 to +10 scale to 0-9 index
                # -10 to -3.4 = Left (squares 0-2)
                # -3.3 to +3.3 = Center (squares 3-6)
                # +3.4 to +10 = Right (squares 7-9)
                
                # Map the score to the appropriate square
                if score <= -6.7:  # Far left
                    filled_squares.add(0)
                elif score <= -3.4:  # Left
                    filled_squares.add(1)
                    filled_squares.add(2)
                elif score <= 0:  # Left-leaning center
                    filled_squares.add(3)
                    filled_squares.add(4)
                elif score <= 3.3:  # Right-leaning center
                    filled_squares.add(5)
                    filled_squares.add(6)
                elif score <= 6.7:  # Right
                    filled_squares.add(7)
                    filled_squares.add(8)
                else:  # Far right
                    filled_squares.add(9)
            
            # Create colored squares
            squares = []
            for i in range(10):
                if i in filled_squares:
                    if i <= 2:  # Left region
                        squares.append(Text("■", style="blue bold"))  # ■
                    elif i <= 6:  # Center region
                        squares.append(Text("■", style="green bold"))  # ■
                    else:  # Right region
                        squares.append(Text("■", style="red bold"))  # ■
                else:
                    squares.append(Text("□", style="dim"))  # □
            
            # Assemble the political spectrum bar
            bias_bar = Text("")
            for square in squares:
                bias_bar.append(square)
        else:
            # No sources - just show an empty bar
            bias_bar = Text("□" * 10, style="dim")  # □□□□□□□□□□
        
        first_source = story.story.sources[0] if story.story.sources else ""
        
        # Format the published date and time
        published_at = None
        if story.story.items:
            published_at = story.story.items[0].published_at
        
        formatted_date = ""
        if published_at:
            # Always include the date for consistency
            formatted_date = published_at.strftime("%b %d, %H:%M")
        
        self.add_row(
            title,
            bias_text, 
            bias_bar,
            first_source,
            formatted_date,
            key=str(idx)
        )
        
    def clear_headlines(self) -> None:
        """Clear all headlines from the table."""
        self.clear()
        
    async def on_focus(self) -> None:
        """Handle focus events on the headlines table."""
        app = self.app
        if hasattr(app, 'set_status'):
            app.set_status("Headlines View - Use Up/Down to navigate, Enter to read article", "green bold")


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
    article_published_at = reactive(None)

    def load_article(self, title: str, source: str, url: str, content: str, published_at: Optional[datetime] = None) -> None:
        """Load article content into the view."""
        # First set properties
        self.article_title = title
        self.article_source = source
        self.article_url = url
        self.article_published_at = published_at
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
        
    async def on_focus(self) -> None:
        """Handle focus events on the article view."""
        app = self.app
        if hasattr(app, 'set_status'):
            app.set_status("Article View - Use Up/Down/PgUp/PgDn/Home/End to navigate", "cyan bold")

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
            Text(f"\n{self.article_title}", style="bold white on #6b21a8"),
            Text("\n"),
            Text(f"{self.article_source}", style="italic yellow")
        ]
        
        # Add publication date if available
        if self.article_published_at:
            formatted_date = self.article_published_at.strftime("%B %d, %Y at %H:%M")
            main_content.append(Text(" • ", style="dim"))
            main_content.append(Text(f"Published {formatted_date}", style="cyan"))
            
        # Add URL and separator
        main_content.extend([
            Text("\n"),
            Text(f"{self.article_url}", style=f"underline link {self.article_url}"),
            Text("\n\n", style=""),
            # Add a separator line
            Text("━" * 50, style="dim"),
            Text("\n\n", style="")
        ])

        # Add article content paragraphs
        if self.article_content:
            # Split by double newlines to get paragraphs
            paragraphs = re.split(r'\n\n+', self.article_content)
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    # First paragraph styling (often the lede)
                    if i == 0:
                        main_content.append(Text(paragraph, style="bold italic"))
                    else:
                        main_content.append(Text(paragraph, style=""))
                    # Add extra spacing between paragraphs for better readability
                    main_content.append(Text("\n\n\n", style=""))

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
                    "Mock Data: ON" if self.use_mock_data else "Real Data: ON",
                    id="mock-button", 
                    variant="warning" if self.use_mock_data else "success"
                ),
                Button(
                    "Clear Cache",
                    id="clear-cache-button",
                    variant="error"
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
        elif button_id == "clear-cache-button":
            await self.clear_cache()
    
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
        
    async def clear_cache(self) -> None:
        """Clear all cached articles and news data."""
        # Set status
        self.set_status("Clearing cache...", "yellow bold")
        
        try:
            # Clear article cache
            cache_dir = Path.home() / ".cache" / "newslens"
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Reset the article extractor to use the new cache dir
            self.article_extractor = ArticleExtractor()
            
            # Show success message
            self.set_status("Cache cleared successfully", "green bold")
            self.notify("Cache has been cleared", title="Success", severity="information")
            
            # Refresh headlines
            self.refresh_headlines()
        except Exception as e:
            self.set_status(f"Error clearing cache: {str(e)}", "red bold")
            self.notify(f"Error: {str(e)}", title="Cache Clear Failed", severity="error")
    
    async def action_toggle_mock(self) -> None:
        """Toggle between mock and real data."""  
        self.use_mock_data = not self.use_mock_data  
        self.config.set("use_mock_data", self.use_mock_data)
        
        # Update the button text and style
        mock_button = self.query_one("#mock-button")
        mock_button.label = "Mock Data: ON" if self.use_mock_data else "Real Data: ON"
        mock_button.variant = "warning" if self.use_mock_data else "success"
        
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
                
                # Update the status bar with a color legend
                status_bar = self.query_one(StatusBar)
                status_text = Text(f"Updated at {now} - {len(self.stories)} stories | Political bias scale: ")
                status_text.append(Text("■", style="blue bold"))
                status_text.append(Text(" Far Left / Left ", style="white"))
                status_text.append(Text("■", style="green bold"))
                status_text.append(Text(" Center ", style="white"))
                status_text.append(Text("■", style="red bold"))
                status_text.append(Text(" Right / Far Right ", style="white"))
                status_text.append(Text("□", style="dim"))
                status_text.append(Text(" No Coverage", style="white"))
                status_bar.update(status_text)
        
        except Exception as e:
            self.set_status(f"Error: {str(e)}", "red bold")

    async def on_read_article(self, idx: int) -> None:
        """Handle reading an article."""
        if not (0 <= idx < len(self.stories)):
            self.notify(f"Story index {idx} is out of range", severity="error")
            return
    
        story = self.stories[idx]
        article = story.story.items[0]
        
        # Get bias information
        bias_info = ""
        if story.left_sources > 0 and story.right_sources == 0:
            bias_info = " (Only covered by left-leaning sources)"
        elif story.right_sources > 0 and story.left_sources == 0:
            bias_info = " (Only covered by right-leaning sources)"
        elif story.center_sources > 0 and story.left_sources == 0 and story.right_sources == 0:
            bias_info = " (Only covered by center sources)"
        elif story.left_sources > 0 and story.right_sources > 0:
            bias_info = " (Covered across political spectrum)"
        
        article_view = self.query_one(ArticleView)
        article_view.load_article(
            title=article.title,
            source=f"{article.source_name}{bias_info}",
            url=article.url,
            content=article.content or "",
            published_at=article.published_at
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