"""Trend service: scraping and analysis of trends from TikTok, YouTube, Google Trends, Reddit."""
from .main import router
from .trend_scraper import scrape_all, TrendSignal
from .trend_analyzer import analyze_signals

__all__ = ["router", "scrape_all", "TrendSignal", "analyze_signals"]
