"""Reddit scraper for collecting images."""
import os
import praw
import requests
import hashlib
from datetime import datetime
from typing import List, Tuple, Optional
import logging
from uuid import uuid4

from scraper.image_cleaner import is_valid_image
from utils.config_loader import load_sources_config

logger = logging.getLogger(__name__)


class RedditScraper:
    """Reddit scraper for collecting images from subreddits."""
    
    def __init__(self, config: dict):
        """Initialize Reddit scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.sources_config = load_sources_config()
        
        # Initialize PRAW - Read-only mode with just client credentials
        # Note: Modern Reddit API for script apps only needs client_id and client_secret
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", config.get("reddit", {}).get("user_agent", "Exposr-Trainer/1.0"))
        )
        
        logger.info("Reddit scraper initialized")
    
    async def fetch_images(self, limit: Optional[int] = None) -> List[Tuple[bytes, dict]]:
        """Fetch images from Reddit.
        
        Args:
            limit: Maximum number of images to fetch per subreddit
            
        Returns:
            List of (image_bytes, metadata) tuples
        """
        samples = []
        subreddits = self.sources_config["reddit"]["subreddits"]
        min_score = self.sources_config["reddit"]["min_score"]
        max_age_days = self.sources_config["reddit"]["max_age_days"]
        limit = limit or 25
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                logger.info(f"Fetching from r/{subreddit_name}")
                
                for submission in subreddit.hot(limit=limit):
                    # Check minimum score
                    if submission.score < min_score:
                        continue
                    
                    # Check age
                    age_days = (datetime.utcnow().timestamp() - submission.created_utc) / 86400
                    if age_days > max_age_days:
                        continue
                    
                    # Check if it's an image
                    image_url = self._get_image_url(submission)
                    if not image_url:
                        continue
                    
                    # Download image
                    image_bytes = self._download_image(image_url)
                    if not image_bytes:
                        continue
                    
                    # Validate image
                    if not is_valid_image(image_bytes):
                        logger.debug(f"Skipping invalid image: {submission.url}")
                        continue
                    
                    # Create metadata
                    metadata = self._create_metadata(submission, image_url, image_bytes)
                    samples.append((image_bytes, metadata))
                
            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"Fetched {len(samples)} images from Reddit")
        return samples
    
    def _get_image_url(self, submission: praw.models.Submission) -> Optional[str]:
        """Extract image URL from submission.
        
        Args:
            submission: Reddit submission
            
        Returns:
            Image URL or None
        """
        url = submission.url
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        
        if any(url.lower().endswith(ext) for ext in extensions):
            return url
        
        # Check for i.redd.it and i.imgur.com
        if 'i.redd.it' in url or 'i.imgur.com' in url or url.endswith('.gifv'):
            return url
        
        return None
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL.
        
        Args:
            url: Image URL
            
        Returns:
            Image bytes or None
        """
        try:
            headers = {
                'User-Agent': os.getenv("REDDIT_USER_AGENT", "Exposr-Trainer/1.0")
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.debug(f"Error downloading image from {url}: {e}")
            return None
    
    def _create_metadata(self, submission: praw.models.Submission, image_url: str, image_bytes: bytes) -> dict:
        """Create metadata dictionary for submission.
        
        Args:
            submission: Reddit submission
            image_url: Image URL
            image_bytes: Image data
            
        Returns:
            Metadata dictionary
        """
        # Compute hash
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        return {
            "id": str(uuid4()),
            "image_url": image_url,
            "source": "reddit",
            "post_id": submission.id,
            "subreddit": submission.subreddit.display_name,
            "title": submission.title,
            "author": str(submission.author) if submission.author else None,
            "created_utc": submission.created_utc,
            "score": submission.score,
            "hash": image_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "label": None,
            "confidence": None
        }

