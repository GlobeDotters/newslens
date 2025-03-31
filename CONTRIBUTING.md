# Contributing to NewsLens

Thank you for considering contributing to NewsLens! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the Issues section
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include screenshots if applicable

### Suggesting Features

- Check if the feature has already been suggested in the Issues section
- Use the feature request template when creating a new issue
- Explain why this feature would be useful to most users

### Adding News Sources

One of the most valuable contributions is adding or updating news sources:

1. Find reliable information about the news source's political leaning
2. Determine the source's RSS feed URL
3. Use the `newslens add-source` command or add directly to the sources database

### Source Classification Guidelines

When classifying news sources, please follow these guidelines:

- **Bias score** (-10 to +10):
  - Far Left: -10 to -7
  - Left: -6.9 to -3.3
  - Center: -3.2 to +3.2
  - Right: +3.3 to +6.9
  - Far Right: +7 to +10

- **Reliability score** (0 to 10):
  - Low: 0 to 3.3
  - Medium: 3.4 to 6.7
  - High: 6.8 to 10

- Use reputable media bias assessment sites as references

### Adding Support for New Countries

To add support for a new country:

1. Research the media landscape in that country
2. Identify at least 3-5 major news sources across the political spectrum
3. Find RSS feeds for those sources
4. Add the sources using the `newslens add-source` command

## Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-new-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the tests (`pytest`)
6. Commit your changes (`git commit -am 'Add some feature'`)
7. Push to the branch (`git push origin feature/my-new-feature`)
8. Create a new Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/newslens.git
cd newslens

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Style Guidelines

This project follows:
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- [Google style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for docstrings

## Questions?

If you have any questions, feel free to open an issue or reach out to the maintainers.
