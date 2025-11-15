"""Tests for data preparation and embedding generation"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from utils.logger import get_logger

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.utils.api_client import YouTubeHistoryAPIClient
from src.data.embeddings.generate_embeddings import (
    prepare_text_for_embedding,
    estimate_data_size
)


class TestTextPreparation(unittest.TestCase):
    """Test text preparation for embeddings"""
    
    def test_prepare_text_with_title_only(self):
        """Test text preparation with only title"""
        video = {'title': 'Test Video'}
        text = prepare_text_for_embedding(video)
        self.assertIn('Test Video', text)
        self.assertIn('Title:', text)
    
    def test_prepare_text_with_all_fields(self):
        """Test text preparation with all fields"""
        video = {
            'title': 'Test Video',
            'channel_name': 'Test Channel',
            'description': 'Test Description'
        }
        transcript = 'Test transcript text here'
        text = prepare_text_for_embedding(video, transcript)
        self.assertIn('Test Video', text)
        self.assertIn('Test Channel', text)
        self.assertIn('Test Description', text)
        self.assertIn('Test transcript text here', text)
    
    def test_prepare_text_with_missing_fields(self):
        """Test text preparation handles missing fields gracefully"""
        video = {'title': 'Test Video'}
        text = prepare_text_for_embedding(video)
        # Should not raise exception
        self.assertIsInstance(text, str)
        self.assertIn('Test Video', text)


class TestDataSizeEstimation(unittest.TestCase):
    """Test data size estimation"""
    
    def test_estimate_size_small(self):
        """Test size estimation for small dataset"""
        size = estimate_data_size(100)
        self.assertGreater(size, 0)
        self.assertLess(size, 1)  # Should be less than 1MB for 100 videos
    
    def test_estimate_size_large(self):
        """Test size estimation for large dataset"""
        size = estimate_data_size(10000)
        self.assertGreater(size, 0)
        # Should be reasonable estimate
        self.assertLess(size, 100)  # Should be less than 100MB for 10k videos


class TestAPIClient(unittest.TestCase):
    """Test YouTube History API Client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = YouTubeHistoryAPIClient(base_url='http://localhost:8000')
    
    @patch('requests.get')
    def test_get_statistics_success(self, mock_get):
        """Test successful statistics retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'total_videos': 1000,
            'total_channels': 50
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        stats = self.client.get_statistics()
        self.assertEqual(stats['total_videos'], 1000)
        self.assertEqual(stats['total_channels'], 50)
    
    @patch('requests.get')
    def test_get_all_videos_pagination(self, mock_get):
        """Test video pagination"""
        # First page
        mock_response_1 = Mock()
        mock_response_1.json.return_value = {
            'results': [{'video_id': f'vid_{i}'} for i in range(10)],
            'has_more': True,
            'total_count': 20
        }
        mock_response_1.raise_for_status = Mock()
        
        # Second page
        mock_response_2 = Mock()
        mock_response_2.json.return_value = {
            'results': [{'video_id': f'vid_{i}'} for i in range(10, 20)],
            'has_more': False,
            'total_count': 20
        }
        mock_response_2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_1, mock_response_2]
        
        videos = self.client.get_all_videos_paginated(limit=10)
        self.assertEqual(len(videos), 20)
    
    @patch('requests.get')
    def test_get_video_transcript_not_found(self, mock_get):
        """Test transcript retrieval when not found"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        transcript = self.client.get_video_transcript('test_video_id')
        self.assertIsNone(transcript)
    
    @patch('requests.get')
    def test_get_video_transcript_success(self, mock_get):
        """Test successful transcript retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'video_id': 'test_video_id',
            'transcript_text': 'Test transcript',
            'language_code': 'en'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        transcript = self.client.get_video_transcript('test_video_id')
        self.assertIsNotNone(transcript)
        self.assertEqual(transcript['transcript_text'], 'Test transcript')


class TestChromaDBIntegration(unittest.TestCase):
    """Test ChromaDB integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    @patch('chromadb.PersistentClient')
    def test_chromadb_collection_creation(self, mock_client_class):
        """Test ChromaDB collection creation"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.create_collection.return_value = mock_collection
        mock_client.get_collection.side_effect = Exception("Not found")
        mock_client_class.return_value = mock_client
        
        from chromadb import PersistentClient
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        
        client = PersistentClient(path=self.temp_dir)
        collection = client.create_collection(
            name='test_collection',
            embedding_function=OpenAIEmbeddingFunction(
                api_key='test_key',
                model_name='text-embedding-3-small'
            )
        )
        
        self.assertIsNotNone(collection)
        mock_client.create_collection.assert_called_once()


if __name__ == '__main__':
    unittest.main()

