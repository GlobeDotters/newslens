#!/usr/bin/env python3
"""
NewsLens CLI - Main entry point
"""

import click
import pycountry
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from newslens import __version__
from newslens.data.fetcher import NewsFetcher
from newslens.data.sources import SourceDatabase, NewsSource
from newslens.analysis.engine import NewsAnalyzer
from newslens.utils.visualizer import NewsVisualizer, ColorKey
from newslens.utils.config import Config

console = Console()
config = Config()

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
    fetcher = NewsFetcher()
    analyzer = NewsAnalyzer()
    visualizer = NewsVisualizer(console)
    
    # Fetch news
    with console.status("Fetching news...", spinner="dots"):
        news_items = fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5))
    
    if not news_items:
        console.print("[bold yellow]No news found.[/bold yellow] Check your internet connection or try a different country.")
        return
    
    # Analyze coverage
    with console.status("Analyzing coverage...", spinner="dots"):
        analysis = analyzer.analyze_coverage(news_items, country_code)
    
    # Display results
    ColorKey.display(console)
    visualizer.display_analysis(analysis, country_name)

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
    fetcher = NewsFetcher()
    analyzer = NewsAnalyzer()
    visualizer = NewsVisualizer(console)
    
    # Fetch news
    with console.status("Fetching news...", spinner="dots"):
        news_items = fetcher.fetch_by_country(country_code, config.get("max_items_per_source", 5))
    
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
def configure(country, max_items, cache_hours):
    """Configure NewsLens settings."""
    if not any([country, max_items, cache_hours]):
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
        
        console.print(table)
        
        console.print("\nUse options to change settings:")
        console.print("  [bold]--country[/bold]: Set default country")
        console.print("  [bold]--max-items[/bold]: Set maximum items per source")
        console.print("  [bold]--cache-hours[/bold]: Set cache duration in hours")
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

if __name__ == '__main__':
    cli()
