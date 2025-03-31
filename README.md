# NewsLens CLI

An open-source news bias analyzer for the terminal.

![NewsLens TUI - Coming Soon](docs/placeholder.png)

## Overview

NewsLens is a command-line tool that helps you understand news coverage across the political spectrum. It identifies blindspots in coverage and provides insights into media bias for stories in your country.

## Features

- 🌍 Country-specific news analysis
- 🔍 Blindspot detection (stories ignored by parts of the media spectrum)
- 📊 Coverage visualization across political spectrum
- 🔄 Local news source database with bias classifications
- 🔊 Asynchronous news fetching for improved performance
- 📝 Full article extraction and reader mode
- 📱 Interactive Terminal User Interface (TUI)
- 💡 Bias detection and blindspot analysis

## Installation

```bash
# From PyPI (once published)
pip install newslens

# From source
git clone https://github.com/GlobeDotters/newslens.git
cd newslens
pip install -e .
```

### TUI Dependencies

To use the interactive TUI, you'll need to install the required dependencies:

```bash
pip install textual
```

## Usage

```bash
# Launch the interactive Terminal User Interface
newslens tui

# Show top headlines with political bias breakdown
newslens headlines

# Show headlines for a specific country
newslens headlines --country UK

# Read an article in reader mode
newslens read 1

# Read an article from a specific source
newslens read 1 --source "CNN"

# Clear cached articles and data
newslens clear_cache

# Show stories with blindspots in coverage
newslens blindspots

# List available news sources
newslens sources

# List sources for a specific country
newslens sources --country CA

# Add a new source
newslens add-source --country US --name "Example News" --url "https://example.com" --bias -2.5 --reliability 7.0 --rss "https://example.com/feed"

# Configure settings
newslens configure

# Show available country codes
newslens countries
```

## Methodology

NewsLens uses a multi-dimensional classification system for news sources:

- **Political bias** is rated on a scale from -10 (far left) to +10 (far right)
- **Reliability** is rated on a scale from 0 (unreliable) to 10 (highly reliable)

Blindspots are detected when a story has significant coverage from one side of the political spectrum but minimal coverage from the other.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source under the MIT license.
