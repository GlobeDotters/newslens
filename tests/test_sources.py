"""Tests for the sources module."""

import pytest
from newslens.data.sources import NewsSource


def test_news_source_init():
    """Test creation of a NewsSource object."""
    source = NewsSource(
        name="Test News",
        url="https://test-news.com",
        country_code="US",
        bias_score=1.5,
        reliability_score=8.0,
        rss_url="https://test-news.com/feed"
    )
    
    assert source.name == "Test News"
    assert source.url == "https://test-news.com"
    assert source.country_code == "US"
    assert source.bias_score == 1.5
    assert source.reliability_score == 8.0
    assert source.rss_url == "https://test-news.com/feed"


def test_bias_category():
    """Test the bias category calculation."""
    # Far Left
    source = NewsSource("Test1", "url", "US", -9.0, 8.0)
    assert source.bias_category == "Far Left"
    
    # Left
    source = NewsSource("Test2", "url", "US", -5.0, 8.0)
    assert source.bias_category == "Left"
    
    # Center
    source = NewsSource("Test3", "url", "US", 0.0, 8.0)
    assert source.bias_category == "Center"
    
    # Right
    source = NewsSource("Test4", "url", "US", 5.0, 8.0)
    assert source.bias_category == "Right"
    
    # Far Right
    source = NewsSource("Test5", "url", "US", 9.0, 8.0)
    assert source.bias_category == "Far Right"


def test_reliability_category():
    """Test the reliability category calculation."""
    # Low
    source = NewsSource("Test1", "url", "US", 0.0, 2.0)
    assert source.reliability_category == "Low"
    
    # Medium
    source = NewsSource("Test2", "url", "US", 0.0, 5.0)
    assert source.reliability_category == "Medium"
    
    # High
    source = NewsSource("Test3", "url", "US", 0.0, 8.0)
    assert source.reliability_category == "High"


def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    original = NewsSource(
        name="Test News",
        url="https://test-news.com",
        country_code="US",
        bias_score=1.5,
        reliability_score=8.0,
        rss_url="https://test-news.com/feed"
    )
    
    # Convert to dict
    source_dict = original.to_dict()
    
    # Convert back from dict
    recreated = NewsSource.from_dict(source_dict)
    
    # Check all properties match
    assert recreated.name == original.name
    assert recreated.url == original.url
    assert recreated.country_code == original.country_code
    assert recreated.bias_score == original.bias_score
    assert recreated.reliability_score == original.reliability_score
    assert recreated.rss_url == original.rss_url
