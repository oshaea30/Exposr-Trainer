"""Scraper module for collecting images from various sources."""
from .reddit_scraper import RedditScraper
from .fetcher_manager import FetcherManager
from .unsplash_fetcher import UnsplashFetcher
from .pexels_fetcher import PexelsFetcher
from .civitai_fetcher import CivitAIFetcher
from .base_fetcher import BaseFetcher

__all__ = ["RedditScraper", "FetcherManager", "UnsplashFetcher", "PexelsFetcher", "CivitAIFetcher", "BaseFetcher"]

