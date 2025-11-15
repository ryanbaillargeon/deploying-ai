"""Chat engine using LangChain with tool support"""

import os
import sys

# Add parent directory to path to import logger FIRST, before any other imports
# From src/core/chat_engine.py, go up to 05_src level (core -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../../'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)

from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.logger import get_logger

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from src.core.model_factory import get_chat_model
from src.services.api_service import get_api_tools

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


class ChatEngine:
    """Chat engine using LangChain with tool support"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize chat engine with model and tools.
        
        Args:
            model_name: Optional model name override
        """
        # Initialize model
        self.model = get_chat_model(model_name=model_name)
        
        # Get tools and bind to model
        self.tools = get_api_tools()
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # System prompt
        self.system_prompt = SystemMessage(
            content="You are a helpful assistant that can answer questions about "
                   "YouTube watch history. Use the available tools to fetch information "
                   "when needed. Provide natural, conversational responses based on the "
                   "information retrieved from the tools."
        )
    
    def process_message(self, message: str, history: List[Dict]) -> str:
        """
        Process a chat message with tool support.
        
        Args:
            message: User message
            history: Conversation history in format [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Assistant response text
        """
        try:
            # Convert history to LangChain messages
            messages = [self.system_prompt]
            
            for msg in history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            
            # Add current user message
            messages.append(HumanMessage(content=message))
            
            # Get model response (may include tool calls)
            response = self.model_with_tools.invoke(messages)
            
            # Handle tool calls if present
            if hasattr(response, 'tool_calls') and response.tool_calls:
                return self._handle_tool_calls(response, messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your message. Please try again."
    
    def _handle_tool_calls(self, response, messages: List) -> str:
        """
        Handle tool calls and return final response.
        
        Args:
            response: Model response with tool calls
            messages: Current message history
            
        Returns:
            Final response text after tool execution
        """
        # Add assistant message with tool calls
        messages.append(response)
        
        # Execute tools
        tool_messages = []
        tool_map = {tool.name: tool for tool in self.tools}
        
        for tool_call in response.tool_calls:
            tool_name = tool_call.get('name') or tool_call.get('function', {}).get('name')
            tool_args = tool_call.get('args') or tool_call.get('function', {}).get('arguments', {})
            
            # Handle string arguments (JSON parsing)
            if isinstance(tool_args, str):
                import json
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse tool arguments as JSON: {tool_args}")
                    tool_args = {}
            
            # Find and execute tool
            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                    tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call_id
                        )
                    )
                except Exception as e:
                    logger.error(f"Tool execution error for {tool_name}: {e}")
                    tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                    )
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                tool_messages.append(
                    ToolMessage(
                        content=f"Unknown tool: {tool_name}",
                        tool_call_id=tool_call_id
                    )
                )
        
        # Add tool results and get final response
        messages.extend(tool_messages)
        final_response = self.model_with_tools.invoke(messages)
        
        # Handle potential additional tool calls (recursive)
        if hasattr(final_response, 'tool_calls') and final_response.tool_calls:
            return self._handle_tool_calls(final_response, messages)
        
        return final_response.content

