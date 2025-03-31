"""
Mock data for development and testing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .fetcher import NewsItem


def get_mock_news_items_raw(country_code: str = "US") -> List[Dict]:
    """Return raw mock news items for testing."""
    now = datetime.now()
    
    us_items = [
        {
            "title": "Government Announces New Budget Plan",
            "url": "https://example.com/budget",
            "source_name": "CNN",
            "published_at": now - timedelta(hours=2),
            "description": "The government has announced a new budget plan with significant changes to taxes and spending."
        },
        {
            "title": "Budget Plan Draws Criticism from Opposition",
            "url": "https://example.com/budget-criticism",
            "source_name": "Fox News",
            "published_at": now - timedelta(hours=1),
            "description": "Opposition leaders have criticized the new budget plan, calling it 'irresponsible'."
        },
        {
            "title": "Analysis: What the Budget Means for Taxpayers",
            "url": "https://example.com/budget-analysis",
            "source_name": "AP News",
            "published_at": now - timedelta(hours=3),
            "description": "A detailed analysis of how the new budget will affect different income groups."
        },
        {
            "title": "New Climate Policy Unveiled by Administration",
            "url": "https://example.com/climate",
            "source_name": "New York Times",
            "published_at": now - timedelta(hours=4),
            "description": "The administration has announced ambitious new climate goals and policies."
        },
        {
            "title": "Scientists Welcome Climate Initiative",
            "url": "https://example.com/climate-scientists",
            "source_name": "CNN",
            "published_at": now - timedelta(hours=3),
            "description": "Climate scientists have welcomed the new policies, calling them 'a step in the right direction'."
        },
        {
            "title": "Climate Plan Criticized for Economic Impact",
            "url": "https://example.com/climate-economy",
            "source_name": "Wall Street Journal",
            "published_at": now - timedelta(hours=2),
            "description": "Industry analysts warn of potential economic consequences from the proposed climate regulations."
        },
        {
            "title": "Debate Over Immigration Policies Intensifies",
            "url": "https://example.com/immigration-debate",
            "source_name": "Fox News",
            "published_at": now - timedelta(hours=5),
            "description": "Lawmakers are engaged in heated debate over proposed changes to immigration policies."
        },
        {
            "title": "New Study Shows Immigration Economic Benefits",
            "url": "https://example.com/immigration-study",
            "source_name": "NPR",
            "published_at": now - timedelta(hours=6),
            "description": "A new academic study finds significant economic benefits from immigration."
        },
        {
            "title": "Immigration Reform Bill Introduced in Legislature",
            "url": "https://example.com/immigration-bill",
            "source_name": "Washington Post",
            "published_at": now - timedelta(hours=7),
            "description": "A bipartisan group of legislators has introduced a comprehensive immigration reform bill."
        }
    ]
    
    uk_items = [
        {
            "title": "PM Unveils New Economic Strategy",
            "url": "https://example.co.uk/economy",
            "source_name": "BBC",
            "published_at": now - timedelta(hours=2),
            "description": "The Prime Minister has unveiled a new economic strategy focusing on growth and innovation."
        },
        {
            "title": "Opposition Calls Economic Plan 'Inadequate'",
            "url": "https://example.co.uk/economic-criticism",
            "source_name": "The Guardian",
            "published_at": now - timedelta(hours=3),
            "description": "Opposition leaders have criticized the new economic plan as inadequate to address current challenges."
        },
        {
            "title": "Analysis: Winners and Losers in Economic Strategy",
            "url": "https://example.co.uk/economic-analysis",
            "source_name": "The Telegraph",
            "published_at": now - timedelta(hours=4),
            "description": "A detailed look at which sectors stand to gain or lose from the new economic measures."
        },
        {
            "title": "NHS Funding Boost Announced",
            "url": "https://example.co.uk/nhs-funding",
            "source_name": "BBC",
            "published_at": now - timedelta(hours=5),
            "description": "The government has announced a significant increase in NHS funding over the next five years."
        },
        {
            "title": "Healthcare Unions Welcome NHS Funding",
            "url": "https://example.co.uk/nhs-unions",
            "source_name": "The Guardian",
            "published_at": now - timedelta(hours=4),
            "description": "Healthcare unions have welcomed the funding boost but call for more focus on staff retention."
        },
        {
            "title": "Experts Question Long-term NHS Funding Plan",
            "url": "https://example.co.uk/nhs-experts",
            "source_name": "Daily Mail",
            "published_at": now - timedelta(hours=3),
            "description": "Health policy experts raise concerns about the sustainability of the NHS funding model."
        },
        {
            "title": "New Immigration Rules Take Effect",
            "url": "https://example.co.uk/immigration-rules",
            "source_name": "The Telegraph",
            "published_at": now - timedelta(hours=8),
            "description": "New points-based immigration rules have come into effect, changing who can work in the UK."
        },
        {
            "title": "Business Leaders Respond to Immigration Changes",
            "url": "https://example.co.uk/business-immigration",
            "source_name": "The Independent",
            "published_at": now - timedelta(hours=7),
            "description": "Industry leaders express mixed reactions to the new immigration system and its impact on recruitment."
        }
    ]
    
    ca_items = [
        {
            "title": "Federal Budget Prioritizes Healthcare and Housing",
            "url": "https://example.ca/federal-budget",
            "source_name": "CBC",
            "published_at": now - timedelta(hours=3),
            "description": "The new federal budget includes major investments in healthcare and affordable housing."
        },
        {
            "title": "Opposition Parties Criticize Budget Priorities",
            "url": "https://example.ca/budget-opposition",
            "source_name": "National Post",
            "published_at": now - timedelta(hours=2),
            "description": "Opposition leaders have criticized the federal budget for failing to address key economic concerns."
        },
        {
            "title": "Climate Action Plan Announced by Government",
            "url": "https://example.ca/climate-plan",
            "source_name": "CBC",
            "published_at": now - timedelta(hours=5),
            "description": "The government has unveiled a comprehensive climate action plan with new emissions targets."
        },
        {
            "title": "Energy Sector Reacts to Climate Initiatives",
            "url": "https://example.ca/energy-climate",
            "source_name": "Globe and Mail",
            "published_at": now - timedelta(hours=4),
            "description": "Canada's energy industry has expressed concerns about the economic impact of new climate regulations."
        },
        {
            "title": "Environmental Groups Welcome Climate Plan",
            "url": "https://example.ca/environmental-climate",
            "source_name": "Toronto Star",
            "published_at": now - timedelta(hours=3),
            "description": "Environmental organizations have praised the ambition of the new climate action plan."
        }
    ]
    
    au_items = [
        {
            "title": "Government Unveils Infrastructure Package",
            "url": "https://example.com.au/infrastructure",
            "source_name": "ABC News",
            "published_at": now - timedelta(hours=2),
            "description": "The federal government has announced a major infrastructure investment package."
        },
        {
            "title": "Opposition Questions Infrastructure Priorities",
            "url": "https://example.com.au/infrastructure-criticism",
            "source_name": "The Australian",
            "published_at": now - timedelta(hours=1),
            "description": "The opposition has questioned the regional distribution of infrastructure funding."
        },
        {
            "title": "New Climate Targets Announced",
            "url": "https://example.com.au/climate-targets",
            "source_name": "ABC News",
            "published_at": now - timedelta(hours=4),
            "description": "Australia announces new emissions reduction targets ahead of international summit."
        },
        {
            "title": "Industry Leaders Respond to Climate Goals",
            "url": "https://example.com.au/industry-climate",
            "source_name": "Sydney Morning Herald",
            "published_at": now - timedelta(hours=3),
            "description": "Major industry sectors have offered mixed reactions to the new climate targets."
        },
        {
            "title": "Environmental Groups: Climate Targets 'Not Enough'",
            "url": "https://example.com.au/environmental-climate",
            "source_name": "News.com.au",
            "published_at": now - timedelta(hours=2),
            "description": "Environmental organizations criticize the climate targets as insufficient to meet global goals."
        }
    ]
    
    country_map = {
        "US": us_items,
        "UK": uk_items,
        "CA": ca_items,
        "AU": au_items
    }
    
    return country_map.get(country_code, us_items)  # Default to US if country not found


def get_mock_news_items(country_code: str = "US") -> List[NewsItem]:
    """Convert raw mock data to NewsItem objects."""
    raw_items = get_mock_news_items_raw(country_code)
    news_items = []
    
    for item in raw_items:
        news_item = NewsItem(
            title=item["title"],
            url=item["url"],
            source_name=item["source_name"],
            published_at=item["published_at"],
            description=item.get("description"),
            content=item.get("content"),
            image_url=item.get("image_url")
        )
        news_items.append(news_item)
    
    return news_items


class MockNewsFetcher:
    """A mock version of the NewsFetcher that uses static data instead of RSS feeds."""
    
    def __init__(self):
        """Initialize the mock fetcher."""
        from .sources import SourceDatabase
        self.source_db = SourceDatabase()
    
    def fetch_from_source(self, source, max_items: int = 10) -> List[NewsItem]:
        """Fetch mock news from a specific source."""
        country_code = source.country_code
        all_items = get_mock_news_items(country_code)
        
        # Filter for this source
        source_items = [item for item in all_items if item.source_name == source.name]
        
        # If no items for this specific source, just return a subset of all items
        if not source_items:
            return all_items[:max_items]
        
        return source_items[:max_items]
    
    def fetch_by_country(self, country_code: str, max_per_source: int = 5) -> List[NewsItem]:
        """Fetch mock news from all sources in a specific country."""
        # Get all sources for this country
        sources = self.source_db.get_sources_by_country(country_code)
        all_items = []
        
        # Fetch news for each source
        for source in sources:
            items = self.fetch_from_source(source, max_per_source)
            all_items.extend(items)
        
        # If no items found (unlikely), use the default ones
        if not all_items:
            all_items = get_mock_news_items(country_code)
        
        return all_items
