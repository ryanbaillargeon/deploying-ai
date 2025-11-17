"""Integration tests for end-to-end chat flow"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.core.chat_engine import ChatEngine
from src.services.api_service import APIService, get_api_tools
from src.services.semantic_service import get_semantic_tools


class TestIntegration(unittest.TestCase):
    """Integration tests for chat flow"""
    
    @patch('src.core.chat_engine.get_chat_model')
    def setUp(self, mock_get_model):
        """Set up test fixtures"""
        self.mock_model = MagicMock()
        self.mock_model_with_tools = MagicMock()
        self.mock_model.bind_tools.return_value = self.mock_model_with_tools
        mock_get_model.return_value = self.mock_model
        
        self.engine = ChatEngine()
    
    def test_tool_definitions_valid(self):
        """Test that tool definitions are valid"""
        api_tools = get_api_tools()
        semantic_tools = get_semantic_tools()
        tools = api_tools + semantic_tools
        
        self.assertGreater(len(tools), 0)
        
        for tool in tools:
            self.assertIsNotNone(tool.name)
            self.assertIsNotNone(tool.description)
    
    def test_chat_engine_with_tools(self):
        """Test chat engine can process messages with tools"""
        # Mock response without tool calls
        mock_response = MagicMock()
        mock_response.content = "I can help you with your YouTube history."
        mock_response.tool_calls = None
        
        self.mock_model_with_tools.invoke.return_value = mock_response
        
        result = self.engine.process_message("Hello", [])
        
        self.assertIn("help", result.lower())
        self.mock_model_with_tools.invoke.assert_called_once()
    
    def test_tool_execution_flow(self):
        """Test complete tool execution flow"""
        # Mock tool call response
        mock_tool_response = MagicMock()
        mock_tool_response.tool_calls = [
            {
                'name': 'get_statistics',
                'args': {},
                'id': 'call_123'
            }
        ]
        
        # Mock final response
        mock_final_response = MagicMock()
        mock_final_response.content = "You have watched 100 videos."
        mock_final_response.tool_calls = None
        
        self.mock_model_with_tools.invoke.side_effect = [
            mock_tool_response,
            mock_final_response
        ]
        
        # Mock tool execution
        with patch.object(self.engine, '_handle_tool_calls') as mock_handle:
            mock_handle.return_value = "You have watched 100 videos."
            result = self.engine.process_message("What are my statistics?", [])
        
        self.assertIn("100", result)
    
    def test_conversation_history_preserved(self):
        """Test that conversation history is preserved"""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        
        self.mock_model_with_tools.invoke.return_value = mock_response
        
        history = [
            {'role': 'user', 'content': 'What videos did I watch?'},
            {'role': 'assistant', 'content': 'You watched 5 videos recently.'},
            {'role': 'user', 'content': 'Tell me more about the first one'}
        ]
        
        result = self.engine.process_message("What was it about?", history)
        
        # Verify history was included in the call
        call_args = self.mock_model_with_tools.invoke.call_args[0][0]
        # Should have: system + 3 history messages + 1 current = 5 messages
        self.assertGreaterEqual(len(call_args), 4)
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'false',
        'OPENAI_API_KEY': 'test-key',
        'OPENAI_MODEL': 'gpt-4o'
    })
    @patch('src.core.model_factory.init_chat_model')
    def test_online_model_configuration(self, mock_init):
        """Test online model configuration"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        engine = ChatEngine()
        
        self.assertIsNotNone(engine.model)
        mock_init.assert_called_once()
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'true',
        'LM_STUDIO_BASE_URL': 'http://127.0.0.1:1234/v1',
        'LOCAL_MODEL_NAME': 'test-model'
    })
    @patch('src.core.model_factory.init_chat_model')
    def test_local_model_configuration(self, mock_init):
        """Test local model configuration"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        engine = ChatEngine()
        
        self.assertIsNotNone(engine.model)
        args, kwargs = mock_init.call_args
        self.assertIn('base_url', kwargs)
        self.assertEqual(kwargs['base_url'], 'http://127.0.0.1:1234/v1')


class TestAPIServiceIntegration(unittest.TestCase):
    """Integration tests for API service"""
    
    def test_api_tools_available(self):
        """Test that API tools are available"""
        tools = get_api_tools()
        
        tool_names = [tool.name for tool in tools]
        self.assertIn('get_recent_videos', tool_names)
        self.assertIn('get_video_details', tool_names)
        self.assertIn('get_statistics', tool_names)
        self.assertIn('get_channel_info', tool_names)
    
    def test_api_service_initialization(self):
        """Test API service can be initialized"""
        service = APIService()
        self.assertIsNotNone(service.api_client)
    
    def test_transformation_not_verbatim(self):
        """Test that transformations are not verbatim copies"""
        service = APIService()
        
        # Test video list transformation
        videos = [{
            'title': 'Python Tutorial',
            'channel_name': 'Tech Educator',
            'watched_at': '2025-01-15T10:00:00Z',
            'duration_formatted': '1:00:00'
        }]
        
        result = service.transform_video_list(videos)
        
        # Should not be verbatim JSON
        self.assertNotIn('"title"', result)
        self.assertNotIn('"channel_name"', result)
        # Should contain natural language
        self.assertIn('Python Tutorial', result)
        self.assertIn('Tech Educator', result)
        self.assertIn('watched', result.lower())


class TestSemanticServiceIntegration(unittest.TestCase):
    """Integration tests for semantic service"""
    
    def test_semantic_tools_available(self):
        """Test that semantic tools are available"""
        tools = get_semantic_tools()
        
        tool_names = [tool.name for tool in tools]
        self.assertIn('search_videos_by_topic', tool_names)
        self.assertIn('find_similar_videos', tool_names)
    
    def test_semantic_tools_in_chat_engine(self):
        """Test that semantic tools are included in chat engine"""
        with patch('src.core.chat_engine.get_chat_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model_with_tools = MagicMock()
            mock_model.bind_tools.return_value = mock_model_with_tools
            mock_get_model.return_value = mock_model
            
            engine = ChatEngine()
            
            # Check that semantic tools are included
            tool_names = [tool.name for tool in engine.tools]
            self.assertIn('search_videos_by_topic', tool_names)
            self.assertIn('find_similar_videos', tool_names)
    
    @patch('src.core.chat_engine.get_chat_model')
    def test_semantic_tool_execution_flow(self, mock_get_model):
        """Test semantic tool execution through chat engine"""
        mock_model = MagicMock()
        mock_model_with_tools = MagicMock()
        mock_model.bind_tools.return_value = mock_model_with_tools
        mock_get_model.return_value = mock_model
        
        engine = ChatEngine()
        
        # Mock tool call response for semantic search
        mock_tool_response = MagicMock()
        mock_tool_response.tool_calls = [
            {
                'name': 'search_videos_by_topic',
                'args': {'query': 'machine learning', 'n_results': 10},
                'id': 'call_123'
            }
        ]
        
        # Mock final response
        mock_final_response = MagicMock()
        mock_final_response.content = "I found 5 videos about machine learning."
        mock_final_response.tool_calls = None
        
        mock_model_with_tools.invoke.side_effect = [
            mock_tool_response,
            mock_final_response
        ]
        
        # Mock tool execution
        with patch.object(engine, '_handle_tool_calls') as mock_handle:
            mock_handle.return_value = "I found 5 videos about machine learning."
            result = engine.process_message("What videos did I watch about machine learning?", [])
        
        self.assertIn("machine learning", result.lower())
    
    @patch('src.core.chat_engine.get_chat_model')
    def test_find_similar_videos_tool_execution(self, mock_get_model):
        """Test find_similar_videos tool execution"""
        mock_model = MagicMock()
        mock_model_with_tools = MagicMock()
        mock_model.bind_tools.return_value = mock_model_with_tools
        mock_get_model.return_value = mock_model
        
        engine = ChatEngine()
        
        # Mock tool call response
        mock_tool_response = MagicMock()
        mock_tool_response.tool_calls = [
            {
                'name': 'find_similar_videos',
                'args': {'video_id': 'abc123', 'n_results': 5},
                'id': 'call_456'
            }
        ]
        
        # Mock final response
        mock_final_response = MagicMock()
        mock_final_response.content = "Here are 3 similar videos."
        mock_final_response.tool_calls = None
        
        mock_model_with_tools.invoke.side_effect = [
            mock_tool_response,
            mock_final_response
        ]
        
        # Mock tool execution
        with patch.object(engine, '_handle_tool_calls') as mock_handle:
            mock_handle.return_value = "Here are 3 similar videos."
            result = engine.process_message("Find videos similar to abc123", [])
        
        self.assertIn("similar", result.lower())


if __name__ == '__main__':
    unittest.main()

