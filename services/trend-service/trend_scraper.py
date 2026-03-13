"""
Trend scraper: collects signals from TikTok, YouTube Shorts, Google Trends, Reddit.
Production implementation would use official APIs or headless browsers; here we simulate.
"""
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrendSignal:
    """Raw trend signal from a source."""
    source: str
    keyword: str
    hashtags: list[str]
    raw_signals: dict[str, Any]
    scraped_at: datetime


def scrape_tiktok_hashtags(hashtags: list[str] | None = None) -> list[TrendSignal]:
    """
    Simulate scraping TikTok hashtag trends.
    In production: use TikTok Research API or third-party trend APIs.
    """
    default_hashtags = [
        "#viral", "#fyp", "#trending", "#foryou", "#explore",
        "#lifehack", "#motivation", "#comedy", "#dance", "#recipe",
    ]
    tags = hashtags or default_hashtags
    signals = []
    for tag in tags[:20]:
        signals.append(TrendSignal(
            source="tiktok",
            keyword=tag.strip("#"),
            hashtags=[tag],
            raw_signals={
                "view_count": random.randint(10_000, 50_000_000),
                "video_count": random.randint(100, 500_000),
                "growth_7d": random.uniform(0.1, 3.0),
            },
            scraped_at=datetime.utcnow(),
        ))
    logger.info("TikTok scrape: %d signals", len(signals))
    return signals


def scrape_youtube_shorts(keywords: list[str] | None = None) -> list[TrendSignal]:
    """
    Simulate scraping YouTube Shorts trends.
    In production: use YouTube Data API v3 with Shorts filters.
    """
    default = ["shorts", "quick tips", "viral short", "life hack", "motivation"]
    kw = keywords or default
    signals = []
    for k in kw[:15]:
        signals.append(TrendSignal(
            source="youtube",
            keyword=k,
            hashtags=[f"#{k.replace(' ', '')}"],
            raw_signals={
                "shorts_views": random.randint(50_000, 20_000_000),
                "upload_count_24h": random.randint(10, 5000),
                "avg_retention": random.uniform(0.3, 0.9),
            },
            scraped_at=datetime.utcnow(),
        ))
    logger.info("YouTube Shorts scrape: %d signals", len(signals))
    return signals


def scrape_google_trends(regions: list[str] | None = None) -> list[TrendSignal]:
    """
    Simulate Google Trends data.
    In production: use pytrends or official Trends API.
    """
    default_queries = [
        "how to", "best", "vs", "recipe", "workout",
        "morning routine", "productivity", "mindset",
    ]
    signals = []
    for q in default_queries[:10]:
        signals.append(TrendSignal(
            source="google_trends",
            keyword=q,
            hashtags=[],
            raw_signals={
                "interest_score": random.randint(20, 100),
                "rising": random.choice([True, False]),
                "growth_7d": random.uniform(-0.2, 2.0),
            },
            scraped_at=datetime.utcnow(),
        ))
    logger.info("Google Trends scrape: %d signals", len(signals))
    return signals


def scrape_reddit(subreddits: list[str] | None = None) -> list[TrendSignal]:
    """
    Simulate Reddit trend signals.
    In production: use Reddit API (PRAW) for hot/rising posts.
    """
    default_subs = ["LifeProTips", "todayilearned", "GetMotivated", "food", "Fitness"]
    subs = subreddits or default_subs
    signals = []
    for sub in subs[:10]:
        signals.append(TrendSignal(
            source="reddit",
            keyword=sub,
            hashtags=[],
            raw_signals={
                "hot_score": random.randint(100, 50000),
                "posts_24h": random.randint(5, 500),
                "avg_comments": random.randint(10, 500),
            },
            scraped_at=datetime.utcnow(),
        ))
    logger.info("Reddit scrape: %d signals", len(signals))
    return signals


def scrape_all(
    tiktok_hashtags: list[str] | None = None,
    youtube_keywords: list[str] | None = None,
    reddit_subs: list[str] | None = None,
) -> list[TrendSignal]:
    """Run all scrapers and return combined signals."""
    all_signals = []
    all_signals.extend(scrape_tiktok_hashtags(tiktok_hashtags))
    all_signals.extend(scrape_youtube_shorts(youtube_keywords))
    all_signals.extend(scrape_google_trends())
    all_signals.extend(scrape_reddit(reddit_subs))
    return all_signals
