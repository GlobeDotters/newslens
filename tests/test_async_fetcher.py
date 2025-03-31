"""
Tests for the asynchronous fetcher module.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from newslens.data.async_fetcher import AsyncNewsFetcher
from newslens.data.sources import NewsSource


@pytest.mark.asyncio
async def test_fetch_feed_success():
    """Test successful feed fetching."""
    # Create a mock source
    source = NewsSource(
        name="Test Source",
        url="https://example.com",
        country_code="US",
        bias_score=0.0,
        reliability_score=8.0,
        rss_url="https://example.com/feed.xml"
    )
    
    # Sample feed content
    feed_content = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <link>https://example.com</link>
        <description>A test feed</description>
        <item>
            <title>Test Article</title>
            <link>https://example.com/article</link>
            <description>This is a test article</description>
            <pubDate>Tue, 31 Mar 2025 12:00:00 GMT</pubDate>
        </item>
    </channel>
    </rss>"""
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = asyncio.coroutine(lambda: feed_content)
    
    # Create mock session
    mock_session = MagicMock()
    mock_get = MagicMock()
    mock_get.__aenter__.return_value = mock_response
    mock_session.get.return_value = mock_get
    
    # Create fetcher
    fetcher = AsyncNewsFetcher()
    
    # Call fetch_feed with the mock session
    items, error = await fetcher.fetch_feed(mock_session, source)
    
    # Verify results
    assert error is None
    assert len(items) == 1
    assert items[0].title == "Test Article"
    assert items[0].url == "https://example.com/article"
    assert items[0].source_name == "Test Source"
    assert items[0].description == "This is a test article"


@pytest.mark.asyncio
async def test_fetch_feed_error():
    """Test feed fetching with error."""
    # Create a mock source
    source = NewsSource(
        name="Test Source",
        url="https://example.com",
        country_code="US",
        bias_score=0.0,
        reliability_score=8.0,
        rss_url="https://example.com/feed.xml"
    )
    
    # Create mock session that raises an exception
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Connection error")
    
    # Create fetcher
    fetcher = AsyncNewsFetcher()
    
    # Call fetch_feed with the mock session
    items, error = await fetcher.fetch_feed(mock_session, source)
    
    # Verify results
    assert isinstance(error, Exception)
    assert str(error) == "Connection error"
    assert items == []


@pytest.mark.asyncio
async def test_fetch_by_country():
    """Test fetching by country."""
    # Create a fetcher with mocked source_db
    fetcher = AsyncNewsFetcher()
    
    # Mock the source database
    mock_sources = [
        NewsSource(
            name="Source 1",
            url="https://example1.com",
            country_code="US",
            bias_score=-5.0,
            reliability_score=7.0,
            rss_url="https://example1.com/feed.xml"
        ),
        NewsSource(
            name="Source 2",
            url="https://example2.com",
            country_code="US",
            bias_score=5.0,
            reliability_score=6.0,
            rss_url="https://example2.com/feed.xml"
        ),
    ]
    
    # Patch the source_db get_sources_by_country method
    with patch('newslens.data.sources.SourceDatabase.get_sources_by_country', return_value=mock_sources):
        # Patch the fetch_feed method
        with patch.object(fetcher, 'fetch_feed', new=asyncio.coroutine(
            lambda session, source: (
                [
                    {
                        "title": f"Article from {source.name}",
                        "url": f"{source.url}/article",
                        "source_name": source.name,
                        "published_at": datetime.now(),
                        "description": f"Description for {source.name}"
                    }
                ],
                None
            )
        )):
            items = await fetcher.fetch_by_country("US", 5)
            
            # Verify results
            assert len(items) == 2
            assert "Source 1" in [item.source_name for item in items]
            assert "Source 2" in [item.source_name for item in items]
