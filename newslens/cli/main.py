#!/usr/bin/env python3
"""
NewsLens CLI - Main entry point
"""

import sys
import click
import pycountry
import json
import pickle
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from newslens import __version__
from newslens.data.fetcher import NewsFetcher
from newslens.data.async_fetcher import AsyncNewsFetcher
from newslens.data.mock import MockNewsFetcher
from newslens.data.sources import SourceDatabase, NewsSource
from newslens.analysis.engine import NewsAnalyzer
from newslens.utils.visualizer import NewsVisualizer, ColorKey
from newslens.utils.config import Config

console = Console()
config = Config()

# Cache for the last analysis results
last_headlines = []

# File to store headlines between commands
def get_cache_dir() -> Path:
    """Get the cache directory, creating it if necessary."""
    home = Path.home()
    cache_dir = home / ".cache" / "newslens"
    
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir

def save_headlines(headlines):
    """Save headlines to a cache file."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / "headlines_cache.pickle"
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(headlines, f)
    except Exception as e:
        print(f"Error saving headlines cache: {e}", file=sys.stderr)

def load_headlines():
    """Load headlines from cache file."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / "headlines_cache.pickle"
    
    if not cache_file.exists():
        return []
    
    try:
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading headlines cache: {e}", file=sys.stderr)
        return []

@click.group()
@click.version_option(__version__)
def cli():
    """NewsLens: Analyze news coverage across the political spectrum."""
    pass

@cli.command()
@click.option('--country', '-c', help='Country code (ISO 3166-1 alpha-2) or name')
def headlines(country):
    """Show top headlines with political coverage breakdown."""
    if country:
        try:
            # Try to get country by name or code
            if len(country) == 2:
                country_obj = pycountry.countries.get(alpha_2=country.upper())
            else:
                country_obj = pycountry.countries.get(name=country.capitalize())
            
            if country_obj:
                country_name = country_obj.name
                country_code = country_obj.alpha_2
            else:
                console.print("[bold red]Error:[/bold red] Invalid country code or name.")
                return
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            return
    else:
        # Use configured country
        country_code = config.get("country", "US")
        country_name = config.get_country_name()
    
    console.print(f"Fetching news for [bold]{country_name}[/bold]...")
    
    # Initialize components
    # Use mock fetcher for development to avoid network issues
    use_mock_data = config.get("use_mock_data", True)  # Default to mock data for now
    
    if use_mock_data:
        fetcher = MockNewsFetcher()
        # Fetch news synchronously for mock data
        with console.status("Fetching news...", spinner="dots"):
            news_items = fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5))
    else:
        # Use async fetcher for real data
        fetcher = AsyncNewsFetcher()
        # Fetch news asynchronously for real data
        with console.status("Fetching news...", spinner="dots"):
            news_items = asyncio.run(fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5)))
    
    analyzer = NewsAnalyzer()
    visualizer = NewsVisualizer(console)
    
    # Display mock data notice if using mock data
    if config.get("use_mock_data", True):
        console.print("[bold yellow]NOTE:[/bold yellow] Using mock data for demonstration. Use [bold]newslens configure --use-real[/bold] to switch to real RSS feeds.")
    
    if not news_items:
        console.print("[bold yellow]No news found.[/bold yellow] Check your internet connection or try a different country.")
        return
    
    # Analyze coverage
    with console.status("Analyzing coverage...", spinner="dots"):
        analysis = analyzer.analyze_coverage(news_items, country_code)
    
    # Debug output
    console.print(f"Found {len(news_items)} news items")
    console.print(f"Produced {len(analysis)} analysis results")
    
    # Display results
    ColorKey.display(console)
    visualizer.display_analysis(analysis, country_name)
    
    # Save the analysis results for later reference
    global last_headlines
    last_headlines = analysis
    save_headlines(analysis)
    
    # Show instructions for reading articles
    console.print("\nTo read any article in full, use: [bold]newslens read STORY_NUMBER[/bold]")

@cli.command()
@click.option('--country', '-c', help='Country code (ISO 3166-1 alpha-2) or name')
def blindspots(country):
    """Show stories with blindspots in coverage."""
    if country:
        try:
            # Try to get country by name or code
            if len(country) == 2:
                country_obj = pycountry.countries.get(alpha_2=country.upper())
            else:
                country_obj = pycountry.countries.get(name=country.capitalize())
            
            if country_obj:
                country_name = country_obj.name
                country_code = country_obj.alpha_2
            else:
                console.print("[bold red]Error:[/bold red] Invalid country code or name.")
                return
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            return
    else:
        # Use configured country
        country_code = config.get("country", "US")
        country_name = config.get_country_name()
    
    console.print(f"Finding blindspots in [bold]{country_name}[/bold] news coverage...")
    
    # Initialize components
    # Use mock fetcher for development to avoid network issues
    use_mock_data = config.get("use_mock_data", True)  # Default to mock data for now
    
    if use_mock_data:
        fetcher = MockNewsFetcher()
        # Fetch news synchronously for mock data
        with console.status("Fetching news...", spinner="dots"):
            news_items = fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5))
    else:
        # Use async fetcher for real data
        fetcher = AsyncNewsFetcher()
        # Fetch news asynchronously for real data
        with console.status("Fetching news...", spinner="dots"):
            news_items = asyncio.run(fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5)))
    
    analyzer = NewsAnalyzer()
    visualizer = NewsVisualizer(console)
    
    # Display mock data notice if using mock data
    if config.get("use_mock_data", True):
        console.print("[bold yellow]NOTE:[/bold yellow] Using mock data for demonstration. Use [bold]newslens configure --use-real[/bold] to switch to real RSS feeds.")
    
    if not news_items:
        console.print("[bold yellow]No news found.[/bold yellow] Check your internet connection or try a different country.")
        return
    
    # Analyze coverage and find blindspots
    with console.status("Analyzing coverage...", spinner="dots"):
        analysis = analyzer.analyze_coverage(news_items, country_code)
        blindspot_analysis = [a for a in analysis if a.blindspot is not None]
    
    # Display results
    if not blindspot_analysis:
        console.print("[bold green]No blindspots found[/bold green] in the current news cycle. All major stories are covered across the political spectrum.")
        return
    
    console.print(Panel(f"Blindspots in {country_name} News Coverage", 
                         style="bold yellow", box=box.DOUBLE))
    
    ColorKey.display(console)
    visualizer.display_analysis(blindspot_analysis, country_name)
    
    # Save the analysis results for later reference
    global last_headlines
    last_headlines = blindspot_analysis
    save_headlines(blindspot_analysis)
    
    # Show instructions for reading articles
    console.print("\nTo read any article in full, use: [bold]newslens read STORY_NUMBER[/bold]")

@cli.command()
@click.option('--country', '-c', help='Country code (ISO 3166-1 alpha-2) or name to filter sources')
def sources(country):
    """List and manage news sources and their bias ratings."""
    source_db = SourceDatabase()
    
    if country:
        try:
            # Try to get country by name or code
            if len(country) == 2:
                country_obj = pycountry.countries.get(alpha_2=country.upper())
            else:
                country_obj = pycountry.countries.get(name=country.capitalize())
            
            if country_obj:
                country_name = country_obj.name
                country_code = country_obj.alpha_2
                
                sources = source_db.get_sources_by_country(country_code)
                
                if not sources:
                    console.print(f"[bold yellow]No sources found for {country_name}.[/bold yellow]")
                    return
                
                console.print(Panel(f"News Sources for {country_name}", style="bold blue"))
                
                # Create a table for sources
                table = Table(show_header=True, header_style="bold")
                table.add_column("Name")
                table.add_column("URL")
                table.add_column("Bias", justify="center")
                table.add_column("Reliability", justify="center")
                
                for source in sources:
                    bias_style = "white"
                    if source.bias_category in ["Left", "Far Left"]:
                        bias_style = "blue"
                    elif source.bias_category == "Center":
                        bias_style = "green"
                    elif source.bias_category in ["Right", "Far Right"]:
                        bias_style = "red"
                    
                    table.add_row(
                        source.name,
                        source.url,
                        f"[{bias_style}]{source.bias_category}[/{bias_style}]",
                        source.reliability_category
                    )
                
                console.print(table)
            else:
                console.print("[bold red]Error:[/bold red] Invalid country code or name.")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    else:
        # List all countries with sources
        countries = source_db.get_available_countries()
        
        if not countries:
            console.print("[bold yellow]No sources found in the database.[/bold yellow]")
            return
        
        console.print(Panel("Available Countries with News Sources", style="bold blue"))
        
        # Create a table of countries
        table = Table(show_header=True, header_style="bold")
        table.add_column("Country")
        table.add_column("Code")
        table.add_column("Sources", justify="right")
        
        for country_code in sorted(countries):
            try:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                if country_obj:
                    country_name = country_obj.name
                    source_count = len(source_db.get_sources_by_country(country_code))
                    table.add_row(country_name, country_code, str(source_count))
            except Exception:
                # Skip countries that can't be resolved
                pass
        
        console.print(table)
        console.print("\nUse [bold]newslens sources --country CODE[/bold] to see sources for a specific country.")

@cli.command()
@click.option('--country', '-c', required=True, help='Country code (ISO 3166-1 alpha-2)')
@click.option('--name', required=True, help='Source name')
@click.option('--url', required=True, help='Source URL')
@click.option('--bias', type=float, required=True, help='Bias score (-10 to +10)')
@click.option('--reliability', type=float, required=True, help='Reliability score (0 to 10)')
@click.option('--rss', help='RSS feed URL')
def add_source(country, name, url, bias, reliability, rss):
    """Add a new news source to the database."""
    # Validate country code
    try:
        country_obj = pycountry.countries.get(alpha_2=country.upper())
        if not country_obj:
            console.print("[bold red]Error:[/bold red] Invalid country code.")
            return
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return
    
    # Validate scores
    if bias < -10 or bias > 10:
        console.print("[bold red]Error:[/bold red] Bias score must be between -10 and +10.")
        return
    
    if reliability < 0 or reliability > 10:
        console.print("[bold red]Error:[/bold red] Reliability score must be between 0 and 10.")
        return
    
    # Create and add the source
    source_db = SourceDatabase()
    
    source = NewsSource(
        name=name,
        url=url,
        country_code=country.upper(),
        bias_score=bias,
        reliability_score=reliability,
        rss_url=rss
    )
    
    source_db.add_source(source)
    
    console.print(f"[bold green]Success![/bold green] Added {name} to the database.")

@cli.command()
@click.option('--country', '-c', required=True, help='Country code (ISO 3166-1 alpha-2)')
@click.option('--name', required=True, help='Source name to remove')
def remove_source(country, name):
    """Remove a news source from the database."""
    source_db = SourceDatabase()
    success = source_db.remove_source(country.upper(), name)
    
    if success:
        console.print(f"[bold green]Success![/bold green] Removed {name} from the database.")
    else:
        console.print(f"[bold red]Error:[/bold red] Could not find source {name} for country {country}.")

@cli.command()
@click.option('--country', '-c', help='Set default country code (ISO 3166-1 alpha-2)')
@click.option('--max-items', type=int, help='Maximum number of items to fetch per source')
@click.option('--cache-hours', type=int, help='Number of hours to cache news data')
@click.option('--use-mock', is_flag=True, help='Use mock data instead of real RSS feeds')
@click.option('--use-real', is_flag=True, help='Use real RSS feeds instead of mock data')
def configure(country, max_items, cache_hours, use_mock, use_real):
    """Configure NewsLens settings."""
    if not any([country, max_items, cache_hours, use_mock, use_real]):
        # Display current configuration
        console.print(Panel("Current Configuration", style="bold blue"))
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Setting")
        table.add_column("Value")
        
        current_country = config.get("country", "US")
        try:
            country_obj = pycountry.countries.get(alpha_2=current_country)
            country_name = f"{current_country} ({country_obj.name})" if country_obj else current_country
        except Exception:
            country_name = current_country
        
        table.add_row("Country", country_name)
        table.add_row("Max Items Per Source", str(config.get("max_items_per_source", 5)))
        table.add_row("Cache Hours", str(config.get("cache_hours", 1)))
        table.add_row("Bias Threshold", str(config.get("bias_threshold", 0.2)))
        table.add_row("Use Mock Data", "Yes (mock data)" if config.get("use_mock_data", True) else "No (async RSS fetching)")
        
        console.print(table)
        
        console.print("\nUse options to change settings:")
        console.print("  [bold]--country[/bold]: Set default country")
        console.print("  [bold]--max-items[/bold]: Set maximum items per source")
        console.print("  [bold]--cache-hours[/bold]: Set cache duration in hours")
        console.print("  [bold]--use-mock[/bold]: Use mock data instead of real RSS feeds")
        console.print("  [bold]--use-real[/bold]: Use real RSS feeds instead of mock data")
        return
    
    # Update settings
    if country:
        try:
            country_obj = pycountry.countries.get(alpha_2=country.upper())
            if country_obj:
                config.set("country", country.upper())
                console.print(f"Default country set to [bold]{country.upper()} ({country_obj.name})[/bold]")
            else:
                console.print("[bold red]Error:[/bold red] Invalid country code.")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    if max_items is not None:
        if max_items > 0:
            config.set("max_items_per_source", max_items)
            console.print(f"Max items per source set to [bold]{max_items}[/bold]")
        else:
            console.print("[bold red]Error:[/bold red] Max items must be greater than 0.")
    
    if cache_hours is not None:
        if cache_hours >= 0:
            config.set("cache_hours", cache_hours)
            console.print(f"Cache duration set to [bold]{cache_hours} hours[/bold]")
        else:
            console.print("[bold red]Error:[/bold red] Cache hours must be non-negative.")
            
    # Handle mock data flags
    if use_mock:
        config.set("use_mock_data", True)
        console.print("[bold]Mock data mode enabled.[/bold] The application will use sample data instead of real RSS feeds.")
    
    if use_real:
        config.set("use_mock_data", False)
        console.print("[bold]Real data mode enabled with async fetching.[/bold] The application will use actual RSS feeds using parallel requests.")

@cli.command()
def countries():
    """List all available country codes."""
    console.print(Panel("Available Countries", style="bold blue"))
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Code")
    
    # Show countries alphabetically
    countries = sorted(list(pycountry.countries), key=lambda x: x.name)
    
    for country in countries:
        table.add_row(country.name, country.alpha_2)
    
    console.print(table)


@cli.command()
@click.argument('story_number', type=int)
@click.option('--source', '-s', help='Specific source to read from')
def read(story_number, source):
    """Read a specific story in reader mode."""
    # Load headlines from cache
    global last_headlines
    if not last_headlines:
        last_headlines = load_headlines()
    
    # Check if we have any headlines cached
    if not last_headlines:
        console.print("[bold yellow]No stories available.[/bold yellow] Run 'newslens headlines' first to fetch stories.")
        return
    
    # Adjust for 1-based indexing in display
    index = story_number - 1
    
    # Validate the story number
    if index < 0 or index >= len(last_headlines):
        console.print(f"[bold red]Error:[/bold red] Story number {story_number} is out of range. Available range is 1-{len(last_headlines)}.")
        return
    
    # Get the selected story
    selected_story = last_headlines[index]
    
    # If a specific source was requested, find that article version
    if source:
        source_items = [item for item in selected_story.story.items if item.source_name.lower() == source.lower()]
        if not source_items:
            console.print(f"[bold yellow]Source not found.[/bold yellow] '{source}' does not have an article for this story.")
            sources_list = ", ".join([item.source_name for item in selected_story.story.items])
            console.print(f"Available sources: {sources_list}")
            return
        
        article = source_items[0]
    else:
        # Just take the first article in the cluster
        article = selected_story.story.items[0]
    
    # Display the article in reader mode
    title = article.title
    source_name = article.source_name
    url = article.url
    content = article.content or "No content available for this article."
    
    # Display the article
    console.print(Panel(f"[bold]{title}[/bold]", style="bold blue"))
    console.print(f"Source: [bold]{source_name}[/bold]")
    console.print(f"URL: {url}\n")
    
    # Display article content in a nicely formatted way
    for paragraph in content.split("\n\n"):
        console.print(paragraph)
        console.print("")
    
    # List other available sources
    if len(selected_story.story.items) > 1:
        console.print("\n[bold]Also covered by:[/bold]")
        other_sources = [item.source_name for item in selected_story.story.items if item.source_name != source_name]
        console.print(", ".join(other_sources))
        console.print("\nUse [bold]newslens read " + str(story_number) + " --source SOURCE[/bold] to read a different version.")

if __name__ == '__main__':
    cli()
