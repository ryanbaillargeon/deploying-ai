"""API Service for YouTube History with natural language transformations"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Add parent directory to path to import logger
# From src/services/api_service.py, go up to 05_src level (services -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../..'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger

# Add src directory to path for API client
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.utils.api_client import YouTubeHistoryAPIClient
from langchain.tools import tool

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


# Pydantic models for structured outputs
class VideoSummaryItem(BaseModel):
    """Individual video summary item"""
    title: str
    channel_name: str
    video_id: Optional[str] = None
    duration_formatted: Optional[str] = None
    watched_at: Optional[str] = None
    watched_time_ago: Optional[str] = None


class VideoListSummary(BaseModel):
    """Complete video list summary with tone tracking"""
    videos: List[VideoSummaryItem]
    total_count: int
    displayed_count: int
    tone: str = Field(default="conversational", description="Tone of the response: 'conversational' or 'analytical'")
    summary_text: str = Field(description="Natural language summary of the video list")


class StatisticsSummary(BaseModel):
    """Statistics summary with tone tracking"""
    total_videos: int
    total_channels: int
    total_watch_events: int
    total_watch_time_hours: float
    average_video_duration_seconds: float
    oldest_watch: Optional[str] = None
    newest_watch: Optional[str] = None
    tone: str = Field(default="analytical", description="Tone of the response: 'conversational' or 'analytical'")
    summary_text: str = Field(description="Natural language summary of the statistics")


class VideoDetailsSummary(BaseModel):
    """Video details summary"""
    title: str
    channel_name: str
    video_id: str
    description: Optional[str] = None
    duration_formatted: Optional[str] = None
    published_at: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    tone: str = Field(default="conversational", description="Tone of the response: 'conversational' or 'analytical'")
    summary_text: str = Field(description="Natural language summary of the video details")


class ChannelDetailsSummary(BaseModel):
    """Channel details summary"""
    name: str
    channel_id: Optional[str] = None
    video_count: int
    subscriber_count: Optional[int] = None
    description: Optional[str] = None
    tone: str = Field(default="conversational", description="Tone of the response: 'conversational' or 'analytical'")
    summary_text: str = Field(description="Natural language summary of the channel details")


class APIService:
    """Service for API calls with natural language transformation"""
    
    def __init__(self, api_client: Optional[YouTubeHistoryAPIClient] = None):
        """
        Initialize the API service.
        
        Args:
            api_client: Optional API client instance (creates new one if not provided)
        """
        self.api_client = api_client or YouTubeHistoryAPIClient()
    
    def get_recent_videos_summary(self, limit: int = 10, channel_id: Optional[str] = None) -> str:
        """
        Get summary of recent videos in natural language.
        
        Args:
            limit: Number of videos to retrieve
            channel_id: Optional channel ID to filter by
            
        Returns:
            Natural language summary string
        """
        try:
            # Get videos (most recent first based on watched_at)
            response = self.api_client.get_all_videos(limit=limit, offset=0)
            videos = response.get('results', [])
            
            if not videos:
                return "I couldn't find any videos in your watch history."
            
            # Filter by channel if specified
            if channel_id:
                videos = [v for v in videos if v.get('channel_id') == channel_id]
                if not videos:
                    return f"I couldn't find any videos from that channel in your recent history."
            
            summary = self.transform_video_list(videos)
            return summary.summary_text
            
        except Exception as e:
            logger.error(f"Error getting recent videos: {e}")
            return f"I encountered an issue retrieving your recent videos. Please try again later."
    
    def get_video_summary(self, video_id: str) -> str:
        """
        Get natural language summary of a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Natural language summary string
        """
        try:
            video = self.api_client.get_video_details(video_id)
            summary = self.transform_video_details(video)
            return summary.summary_text
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 404:
                return f"I couldn't find a video with ID {video_id} in your watch history."
            return f"I encountered an issue retrieving information about that video. Please try again later."
    
    def get_statistics_summary(self) -> str:
        """
        Get natural language summary of statistics.
        
        Returns:
            Natural language summary string
        """
        try:
            stats = self.api_client.get_statistics()
            summary = self.transform_statistics(stats)
            return summary.summary_text
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return f"I encountered an issue retrieving your watch history statistics. Please try again later."
    
    def get_channel_summary(self, channel_id: Optional[str] = None, 
                           channel_name: Optional[str] = None) -> str:
        """
        Get natural language summary of a channel.
        
        Args:
            channel_id: YouTube channel ID
            channel_name: Channel name (alternative to channel_id)
            
        Returns:
            Natural language summary string
        """
        try:
            channel = None
            
            if channel_id:
                channel = self.api_client.get_channel(channel_id)
            elif channel_name:
                channel = self.api_client.search_channels_by_name(channel_name)
                if channel:
                    channel_id = channel.get('channel_id')
                    # Get full channel details
                    channel = self.api_client.get_channel(channel_id)
            else:
                return "Please provide either a channel ID or channel name."
            
            if not channel:
                name_or_id = channel_name or channel_id or "that channel"
                return f"I couldn't find {name_or_id} in your watch history."
            
            summary = self.transform_channel_details(channel)
            return summary.summary_text
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 404:
                name_or_id = channel_name or channel_id or "that channel"
                return f"I couldn't find {name_or_id} in your watch history."
            return f"I encountered an issue retrieving channel information. Please try again later."
    
    def transform_video_list(self, videos: List[Dict]) -> VideoListSummary:
        """
        Transform video list to structured output with natural language summary.
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            VideoListSummary with structured data and natural language summary
        """
        if not videos:
            return VideoListSummary(
                videos=[],
                total_count=0,
                displayed_count=0,
                tone="conversational",
                summary_text="You haven't watched any videos recently."
            )
        
        count = len(videos)
        summary_parts = []
        
        # Opening statement
        if count == 1:
            summary_parts.append("You watched 1 video recently:")
        else:
            summary_parts.append(f"You've watched {count} videos recently. Here are some highlights:")
        
        # Build video items
        video_items = []
        display_count = count  # Show all videos without limit
        
        for i, video in enumerate(videos[:display_count], 1):
            title = video.get('title', 'Unknown Video')
            channel = video.get('channel_name', 'Unknown Channel')
            video_id = video.get('video_id')
            watched_at = video.get('watched_at', '')
            duration = video.get('duration_formatted', '')
            
            # Format watched time
            time_str = ""
            if watched_at:
                try:
                    watched_dt = datetime.fromisoformat(watched_at.replace('Z', '+00:00'))
                    now = datetime.now(watched_dt.tzinfo)
                    diff = now - watched_dt
                    
                    if diff.days == 0:
                        hours = diff.seconds // 3600
                        if hours == 0:
                            minutes = diff.seconds // 60
                            time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                        else:
                            time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
                    elif diff.days == 1:
                        time_str = "yesterday"
                    elif diff.days < 7:
                        time_str = f"{diff.days} days ago"
                    elif diff.days < 30:
                        weeks = diff.days // 7
                        time_str = f"{weeks} week{'s' if weeks != 1 else ''} ago"
                    else:
                        months = diff.days // 30
                        time_str = f"{months} month{'s' if months != 1 else ''} ago"
                except Exception:
                    time_str = ""
            
            video_items.append(VideoSummaryItem(
                title=title,
                channel_name=channel,
                video_id=video_id,
                duration_formatted=duration,
                watched_at=watched_at,
                watched_time_ago=time_str if time_str else None
            ))
            
            duration_str = f" ({duration})" if duration else ""
            time_str_formatted = f" - watched {time_str}" if time_str else ""
            
            summary_parts.append(f"{i}. {title} from {channel}{duration_str}{time_str_formatted}")
        
        if count > display_count:
            summary_parts.append(f"... and {count - display_count} more video{'s' if count - display_count != 1 else ''}")
        
        return VideoListSummary(
            videos=video_items,
            total_count=count,
            displayed_count=display_count,
            tone="conversational",
            summary_text="\n".join(summary_parts)
        )
    
    def transform_statistics(self, stats: Dict) -> StatisticsSummary:
        """
        Transform statistics to structured output with natural language summary.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            StatisticsSummary with structured data and natural language summary
        """
        total_videos = stats.get('total_videos', 0)
        total_channels = stats.get('total_channels', 0)
        total_watch_events = stats.get('total_watch_events', 0)
        total_hours = stats.get('total_watch_time_hours', 0.0)
        avg_duration = stats.get('average_video_duration_seconds', 0.0)
        oldest = stats.get('oldest_watch')
        newest = stats.get('newest_watch')
        
        summary_parts = []
        
        # Opening
        if total_videos == 0:
            return StatisticsSummary(
                total_videos=0,
                total_channels=0,
                total_watch_events=0,
                total_watch_time_hours=0.0,
                average_video_duration_seconds=0.0,
                oldest_watch=oldest,
                newest_watch=newest,
                tone="analytical",
                summary_text="Your YouTube watch history appears to be empty."
            )
        
        if total_videos >= 1000:
            summary_parts.append(f"Your YouTube history is quite extensive! You've watched {total_videos:,} unique videos")
        else:
            summary_parts.append(f"You've watched {total_videos:,} unique video{'s' if total_videos != 1 else ''}")
        
        # Channels
        if total_channels > 0:
            summary_parts.append(f"across {total_channels:,} different channel{'s' if total_channels != 1 else ''}")
        
        # Watch time
        if total_hours > 0:
            if total_hours >= 1000:
                summary_parts.append(f"Your total watch time is approximately {total_hours:,.0f} hours")
            elif total_hours >= 1:
                summary_parts.append(f"Your total watch time is approximately {total_hours:.1f} hours")
            else:
                minutes = total_hours * 60
                summary_parts.append(f"Your total watch time is approximately {minutes:.0f} minutes")
        
        # Average duration
        if avg_duration > 0:
            avg_minutes = avg_duration / 60
            if avg_minutes >= 60:
                avg_hours = avg_minutes / 60
                summary_parts.append(f"with an average video duration of {avg_hours:.1f} hours")
            else:
                summary_parts.append(f"with an average video duration of {avg_minutes:.0f} minutes")
        
        # Watch events
        if total_watch_events > total_videos:
            summary_parts.append(f"You've watched videos a total of {total_watch_events:,} time{'s' if total_watch_events != 1 else ''}")
        
        # Date range
        if oldest and newest:
            try:
                oldest_dt = datetime.fromisoformat(oldest.replace('Z', '+00:00'))
                newest_dt = datetime.fromisoformat(newest.replace('Z', '+00:00'))
                summary_parts.append(f"Your viewing history spans from {oldest_dt.strftime('%B %Y')} to {newest_dt.strftime('%B %Y')}")
            except Exception:
                pass
        
        return StatisticsSummary(
            total_videos=total_videos,
            total_channels=total_channels,
            total_watch_events=total_watch_events,
            total_watch_time_hours=total_hours,
            average_video_duration_seconds=avg_duration,
            oldest_watch=oldest,
            newest_watch=newest,
            tone="analytical",
            summary_text=". ".join(summary_parts) + "."
        )
    
    def transform_video_details(self, video: Dict) -> VideoDetailsSummary:
        """
        Transform video details to structured output with natural language summary.
        
        Args:
            video: Video dictionary
            
        Returns:
            VideoDetailsSummary with structured data and natural language summary
        """
        title = video.get('title', 'Unknown Video')
        channel = video.get('channel_name', 'Unknown Channel')
        video_id = video.get('video_id', '')
        description = video.get('description', '')
        duration = video.get('duration_formatted', '')
        published_at = video.get('published_at', '')
        view_count = video.get('view_count')
        like_count = video.get('like_count')
        
        summary_parts = [f"{title} is a video from {channel}"]
        
        if duration:
            summary_parts.append(f"with a duration of {duration}")
        
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                summary_parts.append(f"published in {pub_dt.strftime('%B %Y')}")
            except Exception:
                pass
        
        if description:
            # Truncate description if too long
            desc = description[:200] + "..." if len(description) > 200 else description
            summary_parts.append(f"Description: {desc}")
        
        if view_count:
            summary_parts.append(f"It has {view_count:,} views")
            if like_count:
                summary_parts.append(f"and {like_count:,} likes")
        
        return VideoDetailsSummary(
            title=title,
            channel_name=channel,
            video_id=video_id,
            description=description if description else None,
            duration_formatted=duration if duration else None,
            published_at=published_at if published_at else None,
            view_count=view_count,
            like_count=like_count,
            tone="conversational",
            summary_text=". ".join(summary_parts) + "."
        )
    
    def transform_channel_details(self, channel: Dict) -> ChannelDetailsSummary:
        """
        Transform channel details to structured output with natural language summary.
        
        Args:
            channel: Channel dictionary
            
        Returns:
            ChannelDetailsSummary with structured data and natural language summary
        """
        name = channel.get('name', 'Unknown Channel')
        channel_id = channel.get('channel_id')
        video_count = channel.get('video_count', 0)
        subscriber_count = channel.get('subscriber_count')
        description = channel.get('description', '')
        
        summary_parts = [f"{name} is a channel"]
        
        if description:
            desc = description[:150] + "..." if len(description) > 150 else description
            summary_parts.append(f"focused on {desc.lower()}")
        
        if video_count > 0:
            summary_parts.append(f"You've watched {video_count} video{'s' if video_count != 1 else ''} from this channel")
        
        if subscriber_count:
            if subscriber_count >= 1000000:
                subs = subscriber_count / 1000000
                summary_parts.append(f"which has {subs:.1f} million subscribers")
            elif subscriber_count >= 1000:
                subs = subscriber_count / 1000
                summary_parts.append(f"which has {subs:.1f} thousand subscribers")
            else:
                summary_parts.append(f"which has {subscriber_count:,} subscribers")
        
        return ChannelDetailsSummary(
            name=name,
            channel_id=channel_id,
            video_count=video_count,
            subscriber_count=subscriber_count,
            description=description if description else None,
            tone="conversational",
            summary_text=". ".join(summary_parts) + "."
        )


# Initialize service instance for tools
_api_service = APIService()


@tool
def get_recent_videos(limit: int = 10, channel_id: Optional[str] = None) -> str:
    """
    Get a summary of recently watched videos. Use this when the user asks about 
    recent viewing history, what they watched lately, or videos from a specific time period.
    
    Args:
        limit: Number of videos to retrieve (default: 10)
        channel_id: Optional channel ID to filter by
    """
    return _api_service.get_recent_videos_summary(limit=limit, channel_id=channel_id)


@tool
def get_video_details(video_id: str) -> str:
    """
    Get detailed information about a specific video. Use this when the user asks 
    about a particular video or provides a video ID.
    
    Args:
        video_id: YouTube video ID (11 characters)
    """
    return _api_service.get_video_summary(video_id)


@tool
def get_statistics() -> str:
    """
    Get overall statistics about the watch history. Use this when the user asks 
    about their viewing patterns, total videos watched, watch time, or general statistics.
    """
    return _api_service.get_statistics_summary()


@tool
def get_channel_info(channel_id: Optional[str] = None, 
                     channel_name: Optional[str] = None) -> str:
    """
    Get information about a specific channel. Use this when the user asks about 
    a channel, wants channel statistics, or asks about videos from a particular channel.
    
    Args:
        channel_id: YouTube channel ID
        channel_name: Channel name (alternative to channel_id)
    """
    return _api_service.get_channel_summary(
        channel_id=channel_id, 
        channel_name=channel_name
    )


def get_api_tools():
    """Get list of API tools for LangChain"""
    return [
        get_recent_videos,
        get_video_details,
        get_statistics,
        get_channel_info
    ]

