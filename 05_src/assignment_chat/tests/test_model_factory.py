"""Tests for model factory"""

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

from src.core.model_factory import get_chat_model


class TestModelFactory(unittest.TestCase):
    """Test model factory functionality"""
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'false',
        'OPENAI_API_KEY': 'test-key',
        'OPENAI_MODEL': 'gpt-4o'
    })
    @patch('src.core.model_factory.init_chat_model')
    def test_get_chat_model_online(self, mock_init):
        """Test online model initialization"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        model = get_chat_model()
        
        mock_init.assert_called_once()
        args, kwargs = mock_init.call_args
        self.assertEqual(args[0], 'openai:gpt-4o')
        self.assertEqual(kwargs['model_provider'], 'openai')
        self.assertIn('temperature', kwargs)
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'true',
        'LM_STUDIO_BASE_URL': 'http://127.0.0.1:1234/v1',
        'LOCAL_MODEL_NAME': 'test-model'
    })
    @patch('src.core.model_factory.init_chat_model')
    def test_get_chat_model_local(self, mock_init):
        """Test local model initialization"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        model = get_chat_model()
        
        mock_init.assert_called_once()
        args, kwargs = mock_init.call_args
        self.assertEqual(args[0], 'test-model')  # LM Studio uses model name directly, not "openai:model"
        self.assertEqual(kwargs['model_provider'], 'openai')
        self.assertEqual(kwargs['base_url'], 'http://127.0.0.1:1234/v1')
        self.assertEqual(kwargs['api_key'], 'not-needed')
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'false',
        'OPENAI_API_KEY': '',
        'OPENAI_MODEL': 'gpt-4o'
    })
    def test_get_chat_model_missing_api_key(self):
        """Test error when API key is missing for online model"""
        with self.assertRaises(ValueError) as context:
            get_chat_model()
        self.assertIn('OPENAI_API_KEY', str(context.exception))
    
    @patch.dict(os.environ, {
        'USE_LOCAL_LLM': 'false',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('src.core.model_factory.init_chat_model')
    def test_get_chat_model_custom_temperature(self, mock_init):
        """Test custom temperature parameter"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        model = get_chat_model(temperature=0.9)
        
        args, kwargs = mock_init.call_args
        self.assertEqual(kwargs['temperature'], 0.9)
    
    @patch('src.core.model_factory.init_chat_model')
    def test_get_chat_model_local_via_name(self, mock_init):
        """Test local model via model name"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            model = get_chat_model(model_name='local-model')
        
        args, kwargs = mock_init.call_args
        self.assertEqual(args[0], 'openai:local-model')
        self.assertIn('base_url', kwargs)


if __name__ == '__main__':
    unittest.main()

