"""
Visualization utilities for the terminal interface.
"""

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..analysis.engine import CoverageAnalysis


class NewsVisualizer:
    """Visualize news coverage and analysis in the terminal."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def coverage_bar(self, left: int, center: int, right: int, width: int = 10) -> str:
        """Create a visual bar showing coverage across the political spectrum."""
        total = left + center + right
        if total == 0:
            return "□" * width
        
        # Calculate proportions (ensure at least 1 character if there's any coverage)
        left_chars = max(1, int(width * left / total)) if left > 0 else 0
        right_chars = max(1, int(width * right / total)) if right > 0 else 0
        
        # Center gets the remainder, but at least 1 if there's any center coverage
        center_chars = width - left_chars - right_chars
        center_chars = max(1, center_chars) if center > 0 else center_chars
        
        # Adjust to fit within width
        if left_chars + center_chars + right_chars > width:
            if center_chars > 1:
                center_chars -= 1
            elif left_chars > 1:
                left_chars -= 1
            elif right_chars > 1:
                right_chars -= 1
        
        # Ensure we fill exactly the specified width
        remaining = width - (left_chars + center_chars + right_chars)
        center_chars += remaining
        
        # Create the bar
        left_bar = "■" * left_chars
        center_bar = "■" * center_chars
        right_bar = "■" * right_chars
        empty = "□" * (width - len(left_bar + center_bar + right_bar))
        
        return left_bar + center_bar + right_bar + empty
    
    def display_analysis(self, analysis: List[CoverageAnalysis], country_name: str):
        """Display coverage analysis in the terminal."""
        self.console.print(Panel(f"Top Stories Today ({country_name})", 
                          style="bold blue", box=box.DOUBLE))
        
        for idx, result in enumerate(analysis, 1):
            # Create the coverage bar
            bar = self.coverage_bar(
                result.left_sources,
                result.center_sources,
                result.right_sources
            )
            
            # Display story with coverage information
            title = result.story.title
            if len(title) > 80:
                title = title[:77] + "..."
                
            self.console.print(f"{idx}. [{bar}] {title}")
            self.console.print(
                f"   LEFT: {result.left_sources} sources  "
                f"CENTER: {result.center_sources} sources  "
                f"RIGHT: {result.right_sources} sources"
            )
            
            # Display blindspot warning if applicable
            if result.blindspot:
                self.console.print(f"   [bold yellow]⚠️ BLINDSPOT:[/bold yellow] {result.blindspot}")
            
            self.console.print("")
    
    def detailed_story_view(self, analysis: CoverageAnalysis):
        """Display detailed information about a single story."""
        story = analysis.story
        
        # Create panel for the story title
        self.console.print(Panel(story.title, style="bold blue"))
        
        # Coverage statistics
        table = Table(title="Coverage Statistics")
        table.add_column("Bias Category", style="cyan")
        table.add_column("Sources", style="magenta")
        table.add_column("Count", justify="right", style="green")
        
        table.add_row("Left", ", ".join(analysis.left_leaning_sources), str(analysis.left_sources))
        table.add_row("Center", ", ".join(analysis.center_leaning_sources), str(analysis.center_sources))
        table.add_row("Right", ", ".join(analysis.right_leaning_sources), str(analysis.right_sources))
        
        self.console.print(table)
        
        # Blindspot warning
        if analysis.blindspot:
            self.console.print(Panel(
                f"⚠️ {analysis.blindspot}",
                style="yellow",
                box=box.ROUNDED
            ))
        
        # Headlines comparison
        self.console.print("\n[bold underline]Headlines Across Sources:[/bold underline]")
        
        for item in story.items:
            source_style = ""
            if item.source_name in analysis.left_leaning_sources:
                source_style = "blue"
            elif item.source_name in analysis.center_leaning_sources:
                source_style = "green"
            elif item.source_name in analysis.right_leaning_sources:
                source_style = "red"
            
            self.console.print(f"[{source_style}]{item.source_name}[/{source_style}]: {item.title}")
            
            if item.description:
                description = item.description
                if len(description) > 100:
                    description = description[:97] + "..."
                self.console.print(f"  {description}\n")
            else:
                self.console.print("")


class ColorKey:
    """Displays a color key for political bias."""
    
    @staticmethod
    def display(console: Console):
        """Display the color key."""
        panel = Panel(
            "[blue]■[/blue] [bold]Left[/bold]    "
            "[green]■[/green] [bold]Center[/bold]    "
            "[red]■[/red] [bold]Right[/bold]",
            title="Color Key",
            box=box.ROUNDED
        )
        console.print(panel)
