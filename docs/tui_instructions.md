# NewsLens TUI

The NewsLens Terminal User Interface (TUI) provides an interactive way to explore news bias and read articles directly in your terminal.

## Features

- Interactive navigation with keyboard shortcuts
- Real-time news fetching and analysis
- Article reading mode with scrollable content
- Focus management between headlines and article view
- Country switching without leaving the interface
- Visual indicators for political bias

## Keyboard Shortcuts

### Navigation
- `Up/Down`: Navigate headlines or scroll article (when in article view)
- `j/k`: Vim-style navigation (down/up)
- `Tab`: Switch focus between headlines and article view
- `Enter`: Read selected article

### Article Reading
- `Page Up/Down`: Fast scrolling in article view
- `Home/End`: Jump to top/bottom of article
- Mouse scrolling is also supported

### Application Controls
- `r`: Refresh headlines
- `f`: Toggle between mock/real data
- `c`: Change country
- `q`: Quit

## Installation

Ensure you have the required dependencies:

```bash
pip install textual
```

If installing from source, install the entire package with:

```bash
pip install -e .
```

## Running the TUI

```bash
newslens tui
```

## Interface Regions

The TUI is divided into several regions:

1. **Header bar**: Shows the application title and version
2. **Control bar**: Contains country selector and action buttons
3. **Headlines table**: Lists news stories with their political bias indicators
4. **Article view**: Displays the selected article with scrollable content
5. **Status bar**: Shows the current application status and timestamp

## Color Indicators

The headlines table includes color indicators for political bias:

- **Blue**: Left-leaning coverage
- **Green**: Centrist coverage
- **Red**: Right-leaning coverage
- **White**: Balanced coverage across the spectrum

## Interface Flow

1. Select a country from the dropdown menu
2. Browse headlines in the headlines table
3. Select a story to read
4. Use navigation keys to scroll through the article
5. Press Tab to return to the headlines table

## Tips and Troubleshooting

- **Terminal Size**: For the best experience, use a terminal with at least 80x24 characters
- **Color Support**: Make sure your terminal supports 256 colors for proper bias indicators
- **No Articles Loading**: Try toggling between mock and real data with the 'f' key
- **Keyboard Navigation Issues**: If keyboard navigation doesn't work, try clicking on the article view first to give it focus
- **Slow Performance**: If fetching real articles is slow, configure the application to use fewer sources:
  ```bash
  newslens configure --max-items 3
  ```

## Future Enhancements

The TUI is continually being improved. Planned features include:

- Side-by-side comparison of the same story from different sources
- Persistent user preferences for preferred news sources
- Improved visualization of bias with graphs and charts
- Saved/bookmarked articles for later reading