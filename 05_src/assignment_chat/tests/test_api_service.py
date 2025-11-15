"""Tests for API service and transformations"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.services.api_service import APIService
from src.utils.api_client import YouTubeHistoryAPIClient


class TestAPIService(unittest.TestCase):
    """Test API service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=YouTubeHistoryAPIClient)
        self.service = APIService(api_client=self.mock_client)
    
    def test_transform_video_list_empty(self):
        """Test transformation of empty video list"""
        result = self.service.transform_video_list([])
        self.assertIn("haven't watched", result.lower())
    
    def test_transform_video_list_single(self):
        """Test transformation of single video"""
        videos = [{
            'title': 'Test Video',
            'channel_name': 'Test Channel',
            'watched_at': '2025-01-15T10:00:00Z',
            'duration_formatted': '10:00'
        }]
        result = self.service.transform_video_list(videos)
        self.assertIn('Test Video', result)
        self.assertIn('Test Channel', result)
        self.assertIn('1 video', result.lower())
    
    def test_transform_video_list_multiple(self):
        """Test transformation of multiple videos"""
        videos = [
            {
                'title': f'Video {i}',
                'channel_name': f'Channel {i}',
                'watched_at': '2025-01-15T10:00:00Z',
                'duration_formatted': '10:00'
            }
            for i in range(3)
        ]
        result = self.service.transform_video_list(videos)
        self.assertIn('3 videos', result.lower())
        self.assertIn('Video 1', result)
        self.assertIn('Video 2', result)
    
    def test_transform_statistics_basic(self):
        """Test statistics transformation"""
        stats = {
            'total_videos': 100,
            'total_channels': 10,
            'total_watch_events': 150,
            'total_watch_time_hours': 50.5
        }
        result = self.service.transform_statistics(stats)
        self.assertIn('100', result)
        self.assertIn('10', result)
        self.assertIn('50.5', result)
    
    def test_transform_statistics_empty(self):
        """Test statistics transformation with empty history"""
        stats = {'total_videos': 0}
        result = self.service.transform_statistics(stats)
        self.assertIn('empty', result.lower())
    
    def test_transform_statistics_large_numbers(self):
        """Test statistics transformation with large numbers"""
        stats = {
            'total_videos': 1250,
            'total_channels': 150,
            'total_watch_time_hours': 2500.0,
            'average_video_duration_seconds': 4320.0
        }
        result = self.service.transform_statistics(stats)
        self.assertIn('1,250', result)
        self.assertIn('150', result)
        self.assertIn('2,500', result)
    
    def test_transform_video_details(self):
        """Test video details transformation"""
        video = {
            'title': 'Test Video',
            'channel_name': 'Test Channel',
            'description': 'Test description',
            'duration_formatted': '1:00:00',
            'published_at': '2024-01-15T10:00:00Z',
            'view_count': 50000,
            'like_count': 1200
        }
        result = self.service.transform_video_details(video)
        self.assertIn('Test Video', result)
        self.assertIn('Test Channel', result)
        self.assertIn('50,000', result)
        self.assertIn('1,200', result)
    
    def test_transform_channel_details(self):
        """Test channel details transformation"""
        channel = {
            'name': 'Test Channel',
            'video_count': 50,
            'subscriber_count': 100000,
            'description': 'Test description'
        }
        result = self.service.transform_channel_details(channel)
        self.assertIn('Test Channel', result)
        self.assertIn('50', result)
        self.assertIn('100', result)  # Should mention subscribers
    
    def test_get_recent_videos_summary_success(self):
        """Test getting recent videos summary"""
        self.mock_client.get_all_videos.return_value = {
            'results': [
                {
                    'title': 'Test Video',
                    'channel_name': 'Test Channel',
                    'watched_at': '2025-01-15T10:00:00Z',
                    'duration_formatted': '10:00'
                }
            ]
        }
        
        result = self.service.get_recent_videos_summary(limit=10)
        self.assertIn('Test Video', result)
        self.mock_client.get_all_videos.assert_called_once()
    
    def test_get_recent_videos_summary_empty(self):
        """Test getting recent videos summary with empty results"""
        self.mock_client.get_all_videos.return_value = {'results': []}
        
        result = self.service.get_recent_videos_summary()
        self.assertIn("couldn't find", result.lower())
    
    def test_get_recent_videos_summary_error(self):
        """Test error handling in get_recent_videos_summary"""
        self.mock_client.get_all_videos.side_effect = Exception("API Error")
        
        result = self.service.get_recent_videos_summary()
        self.assertIn('issue', result.lower())
    
    def test_get_video_summary_success(self):
        """Test getting video summary"""
        self.mock_client.get_video_details.return_value = {
            'title': 'Test Video',
            'channel_name': 'Test Channel',
            'description': 'Test description',
            'duration_formatted': '10:00'
        }
        
        result = self.service.get_video_summary('test123')
        self.assertIn('Test Video', result)
        self.mock_client.get_video_details.assert_called_once_with('test123')
    
    def test_get_video_summary_not_found(self):
        """Test video summary with 404 error"""
        from requests.exceptions import HTTPError
        mock_response = Mock()
        mock_response.status_code = 404
        error = HTTPError()
        error.response = mock_response
        
        self.mock_client.get_video_details.side_effect = error
        
        result = self.service.get_video_summary('invalid')
        self.assertIn("couldn't find", result.lower())
    
    def test_get_statistics_summary_success(self):
        """Test getting statistics summary"""
        self.mock_client.get_statistics.return_value = {
            'total_videos': 100,
            'total_channels': 10,
            'total_watch_time_hours': 50.0
        }
        
        result = self.service.get_statistics_summary()
        self.assertIn('100', result)
        self.mock_client.get_statistics.assert_called_once()
    
    def test_get_channel_summary_by_id(self):
        """Test getting channel summary by ID"""
        self.mock_client.get_channel.return_value = {
            'name': 'Test Channel',
            'video_count': 50,
            'subscriber_count': 100000
        }
        
        result = self.service.get_channel_summary(channel_id='UC123')
        self.assertIn('Test Channel', result)
        self.mock_client.get_channel.assert_called_once_with('UC123')
    
    def test_get_channel_summary_by_name(self):
        """Test getting channel summary by name"""
        self.mock_client.search_channels_by_name.return_value = {
            'channel_id': 'UC123',
            'name': 'Test Channel'
        }
        self.mock_client.get_channel.return_value = {
            'name': 'Test Channel',
            'video_count': 50
        }
        
        result = self.service.get_channel_summary(channel_name='Test Channel')
        self.assertIn('Test Channel', result)
        self.mock_client.search_channels_by_name.assert_called_once_with('Test Channel')
    
    def test_get_channel_summary_not_found(self):
        """Test channel summary when channel not found"""
        self.mock_client.search_channels_by_name.return_value = None
        
        result = self.service.get_channel_summary(channel_name='Nonexistent')
        self.assertIn("couldn't find", result.lower())


if __name__ == '__main__':
    unittest.main()

