"""Tests for Semantic Service and ChromaDB integration"""

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

from src.services.semantic_service import SemanticService


class TestSemanticService(unittest.TestCase):
    """Test Semantic Service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock ChromaDB client and collection
        self.mock_collection = Mock()
        self.mock_client = Mock()
        self.mock_client.get_collection.return_value = self.mock_collection
        
        # Patch PersistentClient to return our mock
        self.client_patcher = patch('src.services.semantic_service.PersistentClient')
        self.mock_persistent_client = self.client_patcher.start()
        self.mock_persistent_client.return_value = self.mock_client
    
    def tearDown(self):
        """Clean up after tests"""
        self.client_patcher.stop()
    
    def test_init_success(self):
        """Test successful initialization"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        self.assertEqual(service.chroma_db_path, './test_db')
        self.assertEqual(service.collection_name, 'test_collection')
        self.assertEqual(service.collection, self.mock_collection)
    
    def test_init_defaults(self):
        """Test initialization with default values"""
        with patch.dict(os.environ, {
            'CHROMA_DB_PATH': './default_db',
            'CHROMA_COLLECTION_NAME': 'default_collection'
        }):
            service = SemanticService()
            self.assertEqual(service.chroma_db_path, './default_db')
            self.assertEqual(service.collection_name, 'default_collection')
    
    def test_init_failure(self):
        """Test initialization failure"""
        self.mock_client.get_collection.side_effect = Exception("DB Error")
        
        with self.assertRaises(Exception):
            SemanticService()
    
    def test_search_by_topic_basic(self):
        """Test basic semantic search"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        # Mock ChromaDB query results
        mock_results = {
            'ids': [['video1', 'video2']],
            'metadatas': [[
                {
                    'title': 'Test Video 1',
                    'channel_id': 'UC123',
                    'channel_name': 'Test Channel',
                    'watched_at': '2025-01-15T10:00:00Z'
                },
                {
                    'title': 'Test Video 2',
                    'channel_id': 'UC456',
                    'channel_name': 'Another Channel',
                    'watched_at': '2025-01-14T10:00:00Z'
                }
            ]],
            'distances': [[0.1, 0.2]],
            'documents': [['doc1', 'doc2']]
        }
        
        self.mock_collection.query.return_value = mock_results
        
        results = service.search_by_topic('machine learning', n_results=10)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['video_id'], 'video1')
        self.assertEqual(results[0]['title'], 'Test Video 1')
        self.assertEqual(results[0]['distance'], 0.1)
        self.mock_collection.query.assert_called_once()
    
    def test_search_by_topic_empty_results(self):
        """Test semantic search with empty results"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        self.mock_collection.query.return_value = {
            'ids': [[]],
            'metadatas': [[]],
            'distances': [[]],
            'documents': [[]]
        }
        
        results = service.search_by_topic('nonexistent topic', n_results=10)
        self.assertEqual(len(results), 0)
    
    def test_search_by_topic_with_channel_filter(self):
        """Test semantic search with channel filter"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        mock_results = {
            'ids': [['video1']],
            'metadatas': [[{
                'title': 'Test Video',
                'channel_id': 'UC123',
                'channel_name': 'Test Channel',
                'watched_at': '2025-01-15T10:00:00Z'
            }]],
            'distances': [[0.1]],
            'documents': [['doc1']]
        }
        
        self.mock_collection.query.return_value = mock_results
        
        filters = {'channel_id': 'UC123'}
        results = service.search_by_topic('test', n_results=10, filters=filters)
        
        # Check that where clause was used
        call_args = self.mock_collection.query.call_args
        self.assertIsNotNone(call_args[1].get('where'))
        self.assertEqual(call_args[1]['where']['channel_id']['$eq'], 'UC123')
    
    def test_hybrid_search_with_date_filter(self):
        """Test hybrid search with date filtering"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        # Mock results with videos from different dates
        mock_results = {
            'ids': [['video1', 'video2', 'video3']],
            'metadatas': [[
                {
                    'title': 'Video 1',
                    'channel_name': 'Channel 1',
                    'watched_at': '2025-01-15T10:00:00Z'
                },
                {
                    'title': 'Video 2',
                    'channel_name': 'Channel 2',
                    'watched_at': '2025-01-10T10:00:00Z'
                },
                {
                    'title': 'Video 3',
                    'channel_name': 'Channel 3',
                    'watched_at': '2025-01-05T10:00:00Z'
                }
            ]],
            'distances': [[0.1, 0.2, 0.3]],
            'documents': [['doc1', 'doc2', 'doc3']]
        }
        
        self.mock_collection.query.return_value = mock_results
        
        # Search with date range filter
        results = service.hybrid_search(
            query='test',
            n_results=10,
            date_from='2025-01-10',
            date_to='2025-01-15'
        )
        
        # Should filter to only videos in date range
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['video_id'], 'video1')
        self.assertEqual(results[1]['video_id'], 'video2')
    
    def test_find_similar_videos_success(self):
        """Test finding similar videos"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        # Mock getting the video
        self.mock_collection.get.return_value = {
            'ids': [['video1']],
            'documents': [['Title: Test Video\nChannel: Test Channel']],
            'metadatas': [[{'title': 'Test Video'}]]
        }
        
        # Mock query for similar videos
        mock_results = {
            'ids': [['video2', 'video3']],
            'metadatas': [[
                {
                    'title': 'Similar Video 1',
                    'channel_name': 'Channel 1',
                    'watched_at': '2025-01-15T10:00:00Z'
                },
                {
                    'title': 'Similar Video 2',
                    'channel_name': 'Channel 2',
                    'watched_at': '2025-01-14T10:00:00Z'
                }
            ]],
            'distances': [[0.15, 0.25]],
            'documents': [['doc2', 'doc3']]
        }
        
        self.mock_collection.query.return_value = mock_results
        
        results = service.find_similar_videos('video1', n_results=5)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['video_id'], 'video2')
        self.assertEqual(results[1]['video_id'], 'video3')
        
        # Check that original video was excluded
        call_args = self.mock_collection.query.call_args
        self.assertIsNotNone(call_args[1].get('where'))
    
    def test_find_similar_videos_not_found(self):
        """Test finding similar videos when video doesn't exist"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        self.mock_collection.get.return_value = {
            'ids': [],
            'documents': [],
            'metadatas': []
        }
        
        results = service.find_similar_videos('nonexistent', n_results=5)
        self.assertEqual(len(results), 0)
    
    def test_format_results_empty(self):
        """Test formatting empty results"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        formatted = service.format_results([])
        self.assertIn("couldn't find", formatted.lower())
    
    def test_format_results_single(self):
        """Test formatting single result"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        results = [{
            'video_id': 'video1',
            'title': 'Test Video',
            'channel_name': 'Test Channel',
            'watched_at': '2025-01-15T10:00:00Z',
            'distance': 0.1
        }]
        
        formatted = service.format_results(results)
        self.assertIn('Test Video', formatted)
        self.assertIn('Test Channel', formatted)
        self.assertIn('1 video', formatted.lower())
    
    def test_format_results_multiple(self):
        """Test formatting multiple results"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        results = [
            {
                'video_id': f'video{i}',
                'title': f'Video {i}',
                'channel_name': f'Channel {i}',
                'watched_at': '2025-01-15T10:00:00Z',
                'distance': 0.1 * i
            }
            for i in range(1, 4)
        ]
        
        formatted = service.format_results(results)
        self.assertIn('3 videos', formatted.lower())
        self.assertIn('Video 1', formatted)
        self.assertIn('Video 2', formatted)
        self.assertIn('Video 3', formatted)
    
    def test_build_where_clause_channel_id(self):
        """Test building where clause with channel_id"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        filters = {'channel_id': 'UC123'}
        where_clause = service._build_where_clause(filters)
        
        self.assertIsNotNone(where_clause)
        self.assertEqual(where_clause['channel_id']['$eq'], 'UC123')
    
    def test_build_where_clause_channel_name(self):
        """Test building where clause with channel_name"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        filters = {'channel_name': 'Test Channel'}
        where_clause = service._build_where_clause(filters)
        
        self.assertIsNotNone(where_clause)
        self.assertEqual(where_clause['channel_name']['$eq'], 'Test Channel')
    
    def test_build_where_clause_empty(self):
        """Test building where clause with no filters"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        where_clause = service._build_where_clause(None)
        self.assertIsNone(where_clause)
    
    def test_process_chromadb_results(self):
        """Test processing ChromaDB results"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        chromadb_results = {
            'ids': [['video1', 'video2']],
            'metadatas': [[
                {
                    'title': 'Video 1',
                    'channel_id': 'UC123',
                    'channel_name': 'Channel 1',
                    'watched_at': '2025-01-15T10:00:00Z'
                },
                {
                    'title': 'Video 2',
                    'channel_id': 'UC456',
                    'channel_name': 'Channel 2',
                    'watched_at': '2025-01-14T10:00:00Z'
                }
            ]],
            'distances': [[0.1, 0.2]],
            'documents': [['doc1', 'doc2']]
        }
        
        processed = service._process_chromadb_results(chromadb_results)
        
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]['video_id'], 'video1')
        self.assertEqual(processed[0]['title'], 'Video 1')
        self.assertEqual(processed[0]['distance'], 0.1)
        self.assertEqual(processed[1]['video_id'], 'video2')
    
    def test_filter_by_date_range(self):
        """Test date range filtering"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        results = [
            {
                'video_id': 'video1',
                'watched_at': '2025-01-15T10:00:00Z'
            },
            {
                'video_id': 'video2',
                'watched_at': '2025-01-10T10:00:00Z'
            },
            {
                'video_id': 'video3',
                'watched_at': '2025-01-05T10:00:00Z'
            }
        ]
        
        filtered = service._filter_by_date_range(
            results,
            date_from='2025-01-10',
            date_to='2025-01-15'
        )
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['video_id'], 'video1')
        self.assertEqual(filtered[1]['video_id'], 'video2')
    
    def test_filter_by_duration(self):
        """Test duration filtering"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        results = [
            {
                'video_id': 'video1',
                'metadata': {'duration_seconds': 300}  # 5 minutes
            },
            {
                'video_id': 'video2',
                'metadata': {'duration_seconds': 600}  # 10 minutes
            },
            {
                'video_id': 'video3',
                'metadata': {'duration_seconds': 900}  # 15 minutes
            },
            {
                'video_id': 'video4',
                'metadata': {}  # No duration
            }
        ]
        
        filtered = service._filter_by_duration(
            results,
            min_duration=300,
            max_duration=900
        )
        
        # Should include videos 1, 2, 3 (within range) and 4 (no duration, so included)
        self.assertEqual(len(filtered), 4)
    
    def test_search_error_handling(self):
        """Test error handling in search"""
        service = SemanticService(
            chroma_db_path='./test_db',
            collection_name='test_collection'
        )
        
        self.mock_collection.query.side_effect = Exception("ChromaDB Error")
        
        with self.assertRaises(Exception):
            service.search_by_topic('test', n_results=10)


class TestSemanticTools(unittest.TestCase):
    """Test LangChain tool functions"""
    
    @patch('src.services.semantic_service.get_semantic_service')
    def test_search_videos_by_topic_tool(self, mock_get_service):
        """Test search_videos_by_topic tool"""
        from src.services.semantic_service import search_videos_by_topic
        
        mock_service = Mock()
        mock_service.hybrid_search.return_value = [
            {
                'video_id': 'video1',
                'title': 'Test Video',
                'channel_name': 'Test Channel',
                'watched_at': '2025-01-15T10:00:00Z',
                'distance': 0.1
            }
        ]
        mock_service.format_results.return_value = "I found 1 video..."
        mock_get_service.return_value = mock_service
        
        result = search_videos_by_topic('machine learning', n_results=10)
        
        self.assertIn('I found', result)
        mock_service.hybrid_search.assert_called_once()
        mock_service.format_results.assert_called_once()
    
    @patch('src.services.semantic_service.get_semantic_service')
    def test_search_videos_by_topic_tool_error(self, mock_get_service):
        """Test search_videos_by_topic tool error handling"""
        from src.services.semantic_service import search_videos_by_topic
        
        mock_service = Mock()
        mock_service.hybrid_search.side_effect = Exception("Error")
        mock_get_service.return_value = mock_service
        
        result = search_videos_by_topic('test', n_results=10)
        self.assertIn('issue', result.lower())
    
    @patch('src.services.semantic_service.get_semantic_service')
    def test_find_similar_videos_tool(self, mock_get_service):
        """Test find_similar_videos tool"""
        from src.services.semantic_service import find_similar_videos
        
        mock_service = Mock()
        mock_service.find_similar_videos.return_value = [
            {
                'video_id': 'video2',
                'title': 'Similar Video',
                'channel_name': 'Channel',
                'watched_at': '2025-01-15T10:00:00Z',
                'distance': 0.15
            }
        ]
        mock_service.format_results.return_value = "I found 1 similar video..."
        mock_get_service.return_value = mock_service
        
        result = find_similar_videos('video1', n_results=5)
        
        self.assertIn('I found', result)
        mock_service.find_similar_videos.assert_called_once_with(
            video_id='video1',
            n_results=5
        )
    
    def test_get_semantic_tools(self):
        """Test get_semantic_tools function"""
        from src.services.semantic_service import get_semantic_tools
        
        tools = get_semantic_tools()
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].name, 'search_videos_by_topic')
        self.assertEqual(tools[1].name, 'find_similar_videos')


if __name__ == '__main__':
    unittest.main()

