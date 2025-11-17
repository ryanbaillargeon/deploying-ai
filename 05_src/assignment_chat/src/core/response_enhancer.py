"""Response enhancer that improves responses based on evaluation feedback"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path to import logger
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../../'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger

# Add src directory to path for model factory and evaluator
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.core.model_factory import get_chat_model
from src.core.response_evaluator import ResponseEvaluation
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


class ResponseEnhancer:
    """Enhances responses based on evaluation feedback"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the response enhancer.
        
        Args:
            model_name: Optional model name override. If None, checks ENHANCEMENT_MODEL env var
        """
        # Get enhancement model name and strip any provider prefix if present
        raw_model_name = model_name or os.getenv('ENHANCEMENT_MODEL', 'gpt-4o')
        # Strip any provider prefix (e.g., "openai:gpt-4o" -> "gpt-4o")
        if ':' in raw_model_name:
            clean_model_name = raw_model_name.split(':', 1)[1]
        else:
            clean_model_name = raw_model_name
        
        # get_chat_model will check ENHANCEMENT_MODEL env var if model_name is None
        self.model = get_chat_model(model_name=clean_model_name, purpose="enhancement")
    
    def enhance(self, response: str, evaluation: ResponseEvaluation, 
                user_query: str, conversation_context: Optional[str] = None) -> str:
        """
        Enhance a response based on evaluation feedback.
        
        Args:
            response: The original response to enhance
            evaluation: The evaluation results
            user_query: The original user query
            conversation_context: Optional conversation history context
            
        Returns:
            Enhanced response string, or original if no enhancement needed
        """
        if not evaluation.needs_enhancement:
            logger.debug("Response does not need enhancement")
            return response
        
        try:
            # Build enhancement prompt based on low-scoring metrics
            prompt = self._build_enhancement_prompt(
                response, evaluation, user_query, conversation_context
            )
            
            messages = [
                SystemMessage(content="You are an expert at improving AI assistant responses. "
                                    "Enhance the response based on the evaluation feedback while "
                                    "maintaining accuracy and the intended personality."),
                HumanMessage(content=prompt)
            ]
            
            enhanced_response = self.model.invoke(messages)
            
            if hasattr(enhanced_response, 'content'):
                enhanced_text = enhanced_response.content
            else:
                enhanced_text = str(enhanced_response)
            
            logger.info(f"Response enhanced. Original length: {len(response)}, "
                       f"Enhanced length: {len(enhanced_text)}")
            
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            # Return original response if enhancement fails
            return response
    
    def _build_enhancement_prompt(self, response: str, evaluation: ResponseEvaluation,
                                  user_query: str, conversation_context: Optional[str]) -> str:
        """
        Build a targeted enhancement prompt based on low-scoring metrics.
        
        Args:
            response: Original response
            evaluation: Evaluation results
            user_query: Original user query
            conversation_context: Optional conversation context
            
        Returns:
            Enhancement prompt string
        """
        issues = []
        improvements = []
        
        # Identify low-scoring metrics and build targeted feedback
        if evaluation.coherence.score < 0.7:
            issues.append(f"COHERENCE (score: {evaluation.coherence.score:.2f}): {evaluation.coherence.reason}")
            improvements.append("- Improve logical structure and flow")
            improvements.append("- Add better transitions between ideas")
            improvements.append("- Organize information more clearly")
        
        if evaluation.tonality.score < 0.7:
            issues.append(f"TONALITY (score: {evaluation.tonality.score:.2f}): {evaluation.tonality.reason}")
            improvements.append("- Match the enthusiastic YouTube History Curator personality")
            improvements.append("- Make the tone more conversational and engaging")
            improvements.append("- Show genuine interest and enthusiasm")
            improvements.append("- Present statistics naturally, not as dry data dumps")
            improvements.append("- Celebrate discoveries and show curiosity")
        
        if evaluation.relevance.score < 0.7:
            issues.append(f"RELEVANCE (score: {evaluation.relevance.score:.2f}): {evaluation.relevance.reason}")
            improvements.append("- Ensure the response directly addresses the user's question")
            improvements.append("- Add missing details that would improve completeness")
            improvements.append("- Provide useful insights beyond just listing facts")
        
        if evaluation.safety.score < 0.7:
            issues.append(f"SAFETY (score: {evaluation.safety.score:.2f}): {evaluation.safety.reason}")
            improvements.append("- Ensure language is appropriate and professional")
            improvements.append("- Avoid any potentially problematic content")
        
        context_str = conversation_context or "No previous conversation context."
        
        prompt = f"""You need to improve the following AI assistant response based on evaluation feedback.

ORIGINAL RESPONSE:
{response}

USER QUERY:
{user_query}

CONVERSATION CONTEXT:
{context_str}

EVALUATION ISSUES:
{chr(10).join(issues)}

IMPROVEMENTS NEEDED:
{chr(10).join(improvements)}

INSTRUCTIONS:
- Improve the response to address the issues identified above
- Maintain all factual accuracy - do not change or add facts
- Keep the same core information and structure
- Enhance the response according to the improvement suggestions
- Ensure the enhanced response maintains the YouTube History Curator personality
- Return ONLY the improved response text, without any meta-commentary

ENHANCED RESPONSE:"""
        
        return prompt

