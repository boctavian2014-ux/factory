"""
Trend analyzer: computes trend_score, growth_rate, engagement_velocity from raw signals.
"""
import logging
from typing import Any

from .trend_scraper import TrendSignal

logger = logging.getLogger(__name__)


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def analyze_tiktok(signal: TrendSignal) -> tuple[float, float, float]:
    """Extract trend_score, growth_rate, engagement_velocity from TikTok raw_signals."""
    r = signal.raw_signals
    view_count = r.get("view_count", 0) or 0
    video_count = r.get("video_count", 0) or 1
    growth_7d = r.get("growth_7d", 0) or 0
    trend_score = _normalize(view_count, 10_000, 50_000_000) * 0.6 + _normalize(video_count, 100, 500_000) * 0.4
    growth_rate = _normalize(growth_7d, 0, 3.0)
    engagement_velocity = trend_score * (1 + growth_rate)
    return round(trend_score, 4), round(growth_rate, 4), round(engagement_velocity, 4)


def analyze_youtube(signal: TrendSignal) -> tuple[float, float, float]:
    """Extract metrics from YouTube Shorts raw_signals."""
    r = signal.raw_signals
    views = r.get("shorts_views", 0) or 0
    uploads = r.get("upload_count_24h", 0) or 1
    retention = r.get("avg_retention", 0) or 0
    trend_score = _normalize(views, 50_000, 20_000_000) * 0.5 + _normalize(retention, 0.3, 0.9) * 0.5
    growth_rate = _normalize(uploads, 10, 5000)
    engagement_velocity = trend_score * (1 + retention)
    return round(trend_score, 4), round(growth_rate, 4), round(engagement_velocity, 4)


def analyze_google_trends(signal: TrendSignal) -> tuple[float, float, float]:
    """Extract metrics from Google Trends raw_signals."""
    r = signal.raw_signals
    interest = r.get("interest_score", 0) or 0
    growth = r.get("growth_7d", 0) or 0
    trend_score = _normalize(interest, 20, 100)
    growth_rate = _normalize(growth + 0.2, 0, 2.2)
    engagement_velocity = trend_score * (1 + max(0, growth_rate))
    return round(trend_score, 4), round(growth_rate, 4), round(engagement_velocity, 4)


def analyze_reddit(signal: TrendSignal) -> tuple[float, float, float]:
    """Extract metrics from Reddit raw_signals."""
    r = signal.raw_signals
    hot = r.get("hot_score", 0) or 0
    posts = r.get("posts_24h", 0) or 1
    comments = r.get("avg_comments", 0) or 0
    trend_score = _normalize(hot, 100, 50000) * 0.5 + _normalize(comments, 10, 500) * 0.5
    growth_rate = _normalize(posts, 5, 500)
    engagement_velocity = trend_score * (1 + growth_rate * 0.5)
    return round(trend_score, 4), round(growth_rate, 4), round(engagement_velocity, 4)


ANALYZERS: dict[str, callable] = {
    "tiktok": analyze_tiktok,
    "youtube": analyze_youtube,
    "google_trends": analyze_google_trends,
    "reddit": analyze_reddit,
}


def analyze_signal(signal: TrendSignal) -> dict[str, Any]:
    """
    Analyze a single TrendSignal and return dict with trend_score, growth_rate, engagement_velocity.
    """
    analyzer = ANALYZERS.get(signal.source, lambda s: (0.5, 0.2, 0.5))
    trend_score, growth_rate, engagement_velocity = analyzer(signal)
    return {
        "source": signal.source,
        "keyword": signal.keyword,
        "hashtags": signal.hashtags,
        "trend_score": trend_score,
        "growth_rate": growth_rate,
        "engagement_velocity": engagement_velocity,
        "raw_signals": signal.raw_signals,
    }


def analyze_signals(signals: list[TrendSignal]) -> list[dict[str, Any]]:
    """Analyze all signals and return list of trend dicts for storage."""
    return [analyze_signal(s) for s in signals]
