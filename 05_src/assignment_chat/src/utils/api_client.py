"""YouTube History API Client"""

import os
import sys
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

# Add parent directory to path to import logger
# From src/utils/api_client.py, go up to 05_src level (utils -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../..'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


class YouTubeHistoryAPIClient:
    """Client for YouTube History API"""
    
    def __init__(self, base_url: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API (defaults to YOUTUBE_API_BASE_URL env var)
            api_version: API version (defaults to YOUTUBE_API_VERSION env var)
        """
        self.base_url = base_url or os.getenv('YOUTUBE_API_BASE_URL', 'http://localhost:8000')
        self.api_version = api_version or os.getenv('YOUTUBE_API_VERSION', 'v1')
        self.api_base = f"{self.base_url}/api/{self.api_version}"
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (without base path)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                # Don't log warnings for missing transcripts (expected behavior)
                if '/transcript' not in url:
                    logger.warning(f"Resource not found: {url}")
                raise
            logger.error(f"HTTP error for {url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """
        Get overall statistics about the watch history.
        
        Returns:
            Dictionary containing statistics
        """
        return self._make_request("stats")
    
    def get_all_videos(self, limit: int = 500, offset: int = 0) -> Dict:
        """
        Fetch all videos with pagination.
        
        Args:
            limit: Maximum number of results per page (1-500)
            offset: Number of results to skip
            
        Returns:
            Dictionary with 'results', 'total_count', 'has_more', etc.
        """
        params = {
            'limit': min(limit, 500),  # Enforce max limit
            'offset': max(offset, 0)   # Enforce min offset
        }
        return self._make_request("videos", params=params)
    
    def get_all_videos_paginated(self, limit: int = 500, max_videos: Optional[int] = None) -> List[Dict]:
        """
        Fetch all videos with automatic pagination.
        
        Args:
            limit: Number of results per page (1-500)
            max_videos: Maximum total videos to fetch (None for all)
            
        Returns:
            List of video dictionaries
        """
        all_videos = []
        offset = 0
        limit = min(limit, 500)
        
        # Try to get total count first for progress bar
        try:
            stats = self.get_statistics()
            total_count = stats.get('total_videos', None)
        except Exception:
            total_count = None
        
        # Create progress bar
        pbar = tqdm(desc="Fetching videos", unit="videos", total=total_count, disable=False)
        
        while True:
            response = self.get_all_videos(limit=limit, offset=offset)
            videos = response.get('results', [])
            all_videos.extend(videos)
            
            # Update progress bar
            pbar.update(len(videos))
            
            # Stop immediately if we got 0 videos (we've reached the end)
            if len(videos) == 0:
                break
            
            # Check if we should continue based on has_more flag
            if not response.get('has_more', False):
                break
            
            # Check if we've reached max_videos limit
            if max_videos and len(all_videos) >= max_videos:
                all_videos = all_videos[:max_videos]
                break
            
            # Optional: Check if we've fetched all available videos based on total_count
            total_count_response = response.get('total_count')
            if total_count_response is not None and len(all_videos) >= total_count_response:
                break
            
            offset += limit
        
        pbar.close()
        return all_videos
    
    def get_video_details(self, video_id: str) -> Dict:
        """
        Get detailed video information.
        
        Args:
            video_id: YouTube video ID (11 characters)
            
        Returns:
            Dictionary containing detailed video metadata
            
        Raises:
            requests.HTTPError: If video not found (404)
        """
        return self._make_request(f"videos/{video_id}")
    
    def get_video_transcript(self, video_id: str, language: str = 'en') -> Optional[Dict]:
        """
        Get transcript for a video.
        
        Args:
            video_id: YouTube video ID (11 characters)
            language: Language code (default: 'en')
            
        Returns:
            Dictionary containing transcript data, or None if not found
        """
        try:
            return self._make_request(f"videos/{video_id}/transcript", params={'language': language})
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                # Missing transcripts are expected, don't log warnings
                return None
            raise
    
    def get_channels(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get a paginated list of all channels.
        
        Args:
            limit: Maximum number of results per page (1-500)
            offset: Number of results to skip
            
        Returns:
            List of channel dictionaries
        """
        params = {
            'limit': min(limit, 500),
            'offset': max(offset, 0)
        }
        response = self._make_request("channels", params=params)
        # API returns a list directly, not wrapped in a dict
        if isinstance(response, list):
            return response
        return response.get('results', [])
    
    def get_channel(self, channel_id: str) -> Dict:
        """
        Get detailed information for a specific channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dictionary containing channel information
            
        Raises:
            requests.HTTPError: If channel not found (404)
        """
        return self._make_request(f"channels/{channel_id}")
    
    def search_channels_by_name(self, channel_name: str) -> Optional[Dict]:
        """
        Search for a channel by name. Gets all channels and filters by name.
        
        Args:
            channel_name: Channel name to search for
            
        Returns:
            Channel dictionary if found, None otherwise
        """
        # Get all channels and search for matching name
        channels = self.get_channels(limit=500)
        for channel in channels:
            if channel.get('name', '').lower() == channel_name.lower():
                return channel
        return None

