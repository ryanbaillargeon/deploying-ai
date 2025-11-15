"""Tests for chat engine"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.core.chat_engine import ChatEngine


class TestChatEngine(unittest.TestCase):
    """Test chat engine functionality"""
    
    @patch('src.core.chat_engine.get_chat_model')
    @patch('src.core.chat_engine.get_api_tools')
    def setUp(self, mock_get_tools, mock_get_model):
        """Set up test fixtures"""
        self.mock_model = MagicMock()
        self.mock_model_with_tools = MagicMock()
        self.mock_model.bind_tools.return_value = self.mock_model_with_tools
        mock_get_model.return_value = self.mock_model
        
        self.mock_tools = [MagicMock(name='tool1'), MagicMock(name='tool2')]
        for tool in self.mock_tools:
            tool.name = 'test_tool'
        mock_get_tools.return_value = self.mock_tools
        
        self.engine = ChatEngine()
    
    def test_init(self):
        """Test chat engine initialization"""
        self.assertIsNotNone(self.engine.model)
        self.assertIsNotNone(self.engine.tools)
        self.assertIsNotNone(self.engine.model_with_tools)
        self.assertIsNotNone(self.engine.system_prompt)
    
    def test_process_message_no_tools(self):
        """Test processing message without tool calls"""
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.tool_calls = None
        self.mock_model_with_tools.invoke.return_value = mock_response
        
        result = self.engine.process_message("Hello", [])
        
        self.assertEqual(result, "Test response")
        self.mock_model_with_tools.invoke.assert_called_once()
    
    def test_process_message_with_tools(self):
        """Test processing message with tool calls"""
        # First response with tool call
        mock_tool_response = MagicMock()
        mock_tool_response.tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'},
                'id': 'call_123'
            }
        ]
        
        # Final response after tool execution
        mock_final_response = MagicMock()
        mock_final_response.content = "Final response"
        mock_final_response.tool_calls = None
        
        # Setup tool map
        tool_map = {'test_tool': self.mock_tools[0]}
        self.mock_tools[0].invoke.return_value = "Tool result"
        self.mock_tools[0].name = 'test_tool'
        
        # Mock the invoke calls
        self.mock_model_with_tools.invoke.side_effect = [
            mock_tool_response,
            mock_final_response
        ]
        
        # Patch tool_map creation
        with patch.object(self.engine, '_handle_tool_calls') as mock_handle:
            mock_handle.return_value = "Final response"
            result = self.engine.process_message("Get videos", [])
        
        self.assertEqual(result, "Final response")
    
    def test_process_message_with_history(self):
        """Test processing message with conversation history"""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        self.mock_model_with_tools.invoke.return_value = mock_response
        
        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'}
        ]
        
        result = self.engine.process_message("How are you?", history)
        
        self.assertEqual(result, "Response")
        # Verify history was included
        call_args = self.mock_model_with_tools.invoke.call_args[0][0]
        self.assertEqual(len(call_args), 4)  # system + 2 history + 1 current
    
    def test_handle_tool_calls(self):
        """Test tool call handling"""
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'},
                'id': 'call_123'
            }
        ]
        
        # Setup tool
        self.mock_tools[0].name = 'test_tool'
        self.mock_tools[0].invoke.return_value = "Tool result"
        
        # Final response
        mock_final_response = MagicMock()
        mock_final_response.content = "Final response"
        mock_final_response.tool_calls = None
        
        self.mock_model_with_tools.invoke.return_value = mock_final_response
        
        messages = []
        result = self.engine._handle_tool_calls(mock_response, messages)
        
        self.assertEqual(result, "Final response")
        self.assertEqual(len(messages), 2)  # tool response + final response
    
    def test_handle_tool_calls_error(self):
        """Test tool call error handling"""
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'},
                'id': 'call_123'
            }
        ]
        
        # Setup tool to raise error
        self.mock_tools[0].name = 'test_tool'
        self.mock_tools[0].invoke.side_effect = Exception("Tool error")
        
        mock_final_response = MagicMock()
        mock_final_response.content = "Final response"
        mock_final_response.tool_calls = None
        
        self.mock_model_with_tools.invoke.return_value = mock_final_response
        
        messages = []
        result = self.engine._handle_tool_calls(mock_response, messages)
        
        # Should still return final response despite tool error
        self.assertEqual(result, "Final response")
    
    def test_process_message_error(self):
        """Test error handling in process_message"""
        self.mock_model_with_tools.invoke.side_effect = Exception("Model error")
        
        result = self.engine.process_message("Hello", [])
        
        self.assertIn('error', result.lower())


if __name__ == '__main__':
    unittest.main()

