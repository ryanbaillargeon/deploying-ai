"""Chat engine using LangChain with tool support"""

import os
import sys
import uuid
import time

# Add parent directory to path to import logger FIRST, before any other imports
# From src/core/chat_engine.py, go up to 05_src level (core -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../../'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)

from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from src.core.model_factory import get_chat_model
from src.services.api_service import get_api_tools
from src.services.semantic_service import get_semantic_tools
from src.core.prompts import get_system_prompt
from src.core.response_evaluator import ResponseEvaluator
from src.core.response_enhancer import ResponseEnhancer

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
        # Initialize model (checks CHAT_MODEL env var if model_name is None)
        self.model = get_chat_model(model_name=model_name, purpose="chat")
        
        # Store model name for logging (check CHAT_MODEL first, then fall back)
        self.model_name = model_name or os.getenv('CHAT_MODEL') or os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        # Initialize AI logger
        self.ai_logger = get_ai_logger()
        
        # Get tools and bind to model (combine API and semantic tools)
        api_tools = get_api_tools()
        semantic_tools = get_semantic_tools()
        self.tools = api_tools + semantic_tools
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Initialize response evaluator and enhancer
        self.evaluator = ResponseEvaluator(model_name=model_name)
        self.enhancer = ResponseEnhancer(model_name=model_name)
    
    def process_message(self, message: str, history: List[Dict]) -> str:
        """
        Process a chat message with tool support.
        
        Args:
            message: User message
            history: Conversation history in format [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Assistant response text
        """
        # Generate conversation ID for this request
        conversation_id = str(uuid.uuid4())
        self.ai_logger.set_conversation_id(conversation_id)
        
        try:
            start_time = time.time()
            
            # Build dynamic system prompt with current context
            system_prompt = get_system_prompt(
                tools=self.tools,
                user_query=message,
                conversation_history=history
            )
            
            # Convert history to LangChain messages
            messages = [system_prompt]
            
            for msg in history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            
            # Add current user message
            messages.append(HumanMessage(content=message))
            
            # Log the prompt
            self.ai_logger.log_prompt(
                prompt_text=message,
                model_name=self.model_name,
                conversation_id=conversation_id,
                history_length=len(history)
            )
            
            # Get model response (may include tool calls)
            response = self.model_with_tools.invoke(messages)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token counts if available
            token_input = 0
            token_output = 0
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                token_input = usage.get('prompt_tokens', 0)
                token_output = usage.get('completion_tokens', 0)
            
            # Handle tool calls if present
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Log response before tool handling
                self.ai_logger.log_response(
                    response_text=response.content if hasattr(response, 'content') else str(response),
                    model_name=self.model_name,
                    token_count_input=token_input,
                    token_count_output=token_output,
                    latency_ms=latency_ms,
                    conversation_id=conversation_id,
                    has_tool_calls=True,
                    tool_call_count=len(response.tool_calls)
                )
                final_response = self._handle_tool_calls(response, messages, conversation_id, message, history)
            else:
                # No tool calls - get response text
                final_response = response.content if hasattr(response, 'content') else str(response)
                
                # Log response
                self.ai_logger.log_response(
                    response_text=final_response,
                    model_name=self.model_name,
                    token_count_input=token_input,
                    token_count_output=token_output,
                    latency_ms=latency_ms,
                    conversation_id=conversation_id
                )
            
            # Evaluate and enhance response
            return self._evaluate_and_enhance(final_response, message, history, conversation_id)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.ai_logger.log(
                category=LogCategory.ERROR,
                message=f"Error processing message: {e}",
                severity=LogSeverity.ERROR,
                conversation_id=conversation_id,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return f"I encountered an error while processing your message. Please try again."
        finally:
            self.ai_logger.clear_conversation_id()
    
    def _evaluate_and_enhance(self, response_text: str, user_query: str, 
                             history: List[Dict], conversation_id: str) -> str:
        """
        Evaluate response and enhance if needed.
        
        Args:
            response_text: The response text to evaluate
            user_query: Original user query
            history: Conversation history
            conversation_id: Conversation ID for logging
            
        Returns:
            Enhanced response text (or original if no enhancement needed)
        """
        # Check if evaluation and enhancement should be skipped
        skip_flag = os.getenv('SKIP_EVALUATION_ENHANCEMENT', 'false').lower() == 'true'
        if skip_flag:
            logger.debug("Skipping evaluation and enhancement (SKIP_EVALUATION_ENHANCEMENT=true)")
            return response_text
        
        try:
            # Format conversation context for evaluation
            context_parts = []
            if history:
                recent = history[-3:] if len(history) > 3 else history
                for msg in recent:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    context_parts.append(f"{role}: {content[:100]}")
            conversation_context = "\n".join(context_parts) if context_parts else None
            
            # Evaluate response
            evaluation = self.evaluator.evaluate(
                response=response_text,
                user_query=user_query,
                conversation_context=conversation_context,
                conversation_id=conversation_id
            )
            
            # Log evaluation summary (INFO level) with reasoning in metadata
            self.ai_logger.log(
                category=LogCategory.EVALUATION,
                message=f"Response evaluation: coherence={evaluation.coherence.score:.2f}, "
                       f"tonality={evaluation.tonality.score:.2f}, "
                       f"relevance={evaluation.relevance.score:.2f}, "
                       f"safety={evaluation.safety.score:.2f}, "
                       f"needs_enhancement={evaluation.needs_enhancement}",
                severity=LogSeverity.INFO,
                conversation_id=conversation_id,
                metadata={
                    "coherence_score": evaluation.coherence.score,
                    "coherence_reason": evaluation.coherence.reason,
                    "tonality_score": evaluation.tonality.score,
                    "tonality_reason": evaluation.tonality.reason,
                    "relevance_score": evaluation.relevance.score,
                    "relevance_reason": evaluation.relevance.reason,
                    "safety_score": evaluation.safety.score,
                    "safety_reason": evaluation.safety.reason,
                    "needs_enhancement": evaluation.needs_enhancement
                }
            )
            
            # Enhance if needed
            if evaluation.needs_enhancement:
                logger.info(f"Enhancing response due to low scores")
                enhanced_response = self.enhancer.enhance(
                    response=response_text,
                    evaluation=evaluation,
                    user_query=user_query,
                    conversation_context=conversation_context
                )
                
                # Log enhancement
                self.ai_logger.log(
                    category=LogCategory.EVALUATION,
                    message=f"Response enhanced. Original length: {len(response_text)}, "
                           f"Enhanced length: {len(enhanced_response)}",
                    severity=LogSeverity.INFO,
                    conversation_id=conversation_id,
                    metadata={"enhancement": True, "original_length": len(response_text), "enhanced_length": len(enhanced_response)}
                )
                
                return enhanced_response
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in evaluation/enhancement: {e}")
            # Return original response if evaluation/enhancement fails
            return response_text
    
    def _handle_tool_calls(self, response, messages: List, conversation_id: str, 
                           user_query: str, history: List[Dict]) -> str:
        """
        Handle tool calls and return final response.
        
        Args:
            response: Model response with tool calls
            messages: Current message history
            conversation_id: Conversation ID for logging
            
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
            
            # Log tool call
            self.ai_logger.log_tool_call(
                tool_name=tool_name,
                tool_args=tool_args if isinstance(tool_args, dict) else {},
                conversation_id=conversation_id
            )
            
            # Find and execute tool
            if tool_name in tool_map:
                try:
                    tool_start_time = time.time()
                    result = tool_map[tool_name].invoke(tool_args)
                    tool_latency_ms = (time.time() - tool_start_time) * 1000
                    
                    # Log successful tool result
                    self.ai_logger.log_tool_result(
                        tool_name=tool_name,
                        success=True,
                        latency_ms=tool_latency_ms,
                        conversation_id=conversation_id,
                        result_preview=str(result)[:200] if result else None
                    )
                    
                    tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call_id
                        )
                    )
                except Exception as e:
                    logger.error(f"Tool execution error for {tool_name}: {e}")
                    
                    # Log failed tool result
                    self.ai_logger.log_tool_result(
                        tool_name=tool_name,
                        success=False,
                        conversation_id=conversation_id,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                    )
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                
                # Log unknown tool
                self.ai_logger.log_tool_result(
                    tool_name=tool_name,
                    success=False,
                    conversation_id=conversation_id,
                    error="Unknown tool"
                )
                
                tool_call_id = tool_call.get('id') or tool_call.get('function', {}).get('id', '')
                tool_messages.append(
                    ToolMessage(
                        content=f"Unknown tool: {tool_name}",
                        tool_call_id=tool_call_id
                    )
                )
        
        # Add tool results and get final response
        messages.extend(tool_messages)
        final_start_time = time.time()
        final_response = self.model_with_tools.invoke(messages)
        final_latency_ms = (time.time() - final_start_time) * 1000
        
        # Extract token counts for final response
        final_token_input = 0
        final_token_output = 0
        if hasattr(final_response, 'response_metadata'):
            usage = final_response.response_metadata.get('token_usage', {})
            final_token_input = usage.get('prompt_tokens', 0)
            final_token_output = usage.get('completion_tokens', 0)
        
        # Log final response
        self.ai_logger.log_response(
            response_text=final_response.content if hasattr(final_response, 'content') else str(final_response),
            model_name=self.model_name,
            token_count_input=final_token_input,
            token_count_output=final_token_output,
            latency_ms=final_latency_ms,
            conversation_id=conversation_id,
            is_final_response=True
        )
        
        # Handle potential additional tool calls (recursive)
        if hasattr(final_response, 'tool_calls') and final_response.tool_calls:
            return self._handle_tool_calls(final_response, messages, conversation_id, user_query, history)
        
        response_text = final_response.content if hasattr(final_response, 'content') else str(final_response)
        
        # Evaluate and enhance final response
        return self._evaluate_and_enhance(response_text, user_query, history, conversation_id)

