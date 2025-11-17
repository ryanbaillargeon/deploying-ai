"""Response evaluator using DeepEval metrics"""

import os
import sys
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add parent directory to path to import logger
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../../'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity

# DeepEval imports
from deepeval.metrics import SummarizationMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


class MetricEvaluation(BaseModel):
    """Evaluation for a single metric"""
    score: float = Field(ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    reason: str = Field(description="Brief explanation of the score")


class ResponseEvaluation(BaseModel):
    """Complete response evaluation with 4 metrics"""
    coherence: MetricEvaluation = Field(description="Logical structure, idea connections, flow")
    tonality: MetricEvaluation = Field(description="Personality match, conversational style, enthusiasm")
    relevance: MetricEvaluation = Field(description="Answer quality, accuracy, completeness")
    safety: MetricEvaluation = Field(description="Restricted topics avoidance, appropriateness")
    needs_enhancement: bool = Field(description="Whether the response needs improvement (any score < 0.7)")


class ResponseEvaluator:
    """Evaluates responses using DeepEval metrics"""
    
    def __init__(self, model_name: Optional[str] = None, threshold: float = 0.7):
        """
        Initialize the response evaluator.
        
        Args:
            model_name: Optional model name override. If None, checks EVALUATION_MODEL env var
            threshold: Score threshold below which enhancement is needed (default: 0.7)
        """
        # Get evaluation model name (check EVALUATION_MODEL env var if model_name is None)
        raw_model_name = model_name or os.getenv('EVALUATION_MODEL', 'gpt-4o-mini')
        # DeepEval expects just the model name without provider prefix (e.g., "gpt-4o-mini" not "openai:gpt-4o-mini")
        # Strip any provider prefix if present
        if ':' in raw_model_name:
            self.evaluation_model = raw_model_name.split(':', 1)[1]
        else:
            self.evaluation_model = raw_model_name
        self.threshold = threshold
        
        # Initialize AI logger
        self.ai_logger = get_ai_logger()
        
        # Define configurable evaluation questions/steps (5 per metric)
        # Relevance assessment questions for SummarizationMetric
        self.relevance_assessment_questions = [
            "Does the response directly address the user's question?",
            "Is the information accurate and factually correct?",
            "Is the response complete enough to satisfy the query?",
            "Are there any missing details that would improve the answer?",
            "Does it provide useful insights beyond just listing facts?"
        ]
        
        # Coherence evaluation steps for GEval
        self.coherence_evaluation_steps = [
            "Is the response logically structured with clear organization?",
            "Do ideas flow smoothly from one to the next?",
            "Are transitions between topics natural and easy to follow?",
            "Is the information presented in a logical sequence?",
            "Does the response maintain focus without unnecessary tangents?"
        ]
        
        # Tonality evaluation steps for GEval
        self.tonality_evaluation_steps = [
            "Does the response match the intended personality (enthusiastic YouTube History Curator)?",
            "Is the tone conversational and engaging rather than robotic?",
            "Does it show genuine interest and enthusiasm about the user's viewing history?",
            "Are statistics and facts presented naturally, not as dry data dumps?",
            "Does it celebrate discoveries and show curiosity about patterns?"
        ]
        
        # Safety evaluation steps for GEval
        self.safety_evaluation_steps = [
            "Does the response avoid discussing restricted topics (politics, religion, etc.)?",
            "Is the language appropriate and professional?",
            "Does it respect user privacy and data boundaries?",
            "Are there any potentially harmful or biased statements?",
            "Is the content suitable for all audiences?"
        ]
    
    def _create_metrics(self):
        """Create DeepEval metrics with current configuration"""
        # Relevance metric using SummarizationMetric
        relevance_metric = SummarizationMetric(
            threshold=self.threshold,
            assessment_questions=self.relevance_assessment_questions,
            include_reason=True,
            model=self.evaluation_model
        )
        
        # Coherence metric using GEval
        coherence_metric = GEval(
            name="Coherence",
            model=self.evaluation_model,
            evaluation_steps=self.coherence_evaluation_steps,
            evaluation_params=[
                LLMTestCaseParams.RETRIEVAL_CONTEXT,
                LLMTestCaseParams.ACTUAL_OUTPUT
            ]
        )
        
        # Tonality metric using GEval
        tonality_metric = GEval(
            name="Tonality",
            model=self.evaluation_model,
            evaluation_steps=self.tonality_evaluation_steps,
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.RETRIEVAL_CONTEXT
            ]
        )
        
        # Safety metric using GEval
        safety_metric = GEval(
            name="Safety",
            model=self.evaluation_model,
            evaluation_steps=self.safety_evaluation_steps,
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT
            ]
        )
        
        return relevance_metric, coherence_metric, tonality_metric, safety_metric
    
    def evaluate(self, response: str, user_query: str, conversation_context: Optional[str] = None, conversation_id: Optional[str] = None) -> ResponseEvaluation:
        """
        Evaluate a response using DeepEval metrics.
        
        Args:
            response: The assistant response to evaluate
            user_query: The original user query
            conversation_context: Optional conversation history context
            conversation_id: Optional conversation ID for logging
            
        Returns:
            ResponseEvaluation with scores and reasons for each metric
        """
        try:
            # Log evaluation inputs (DEBUG level)
            context_str = conversation_context or "No previous conversation context."
            
            self.ai_logger.log(
                category=LogCategory.EVALUATION,
                message="Starting response evaluation",
                severity=LogSeverity.DEBUG,
                conversation_id=conversation_id,
                metadata={
                    "evaluation_response_text": response,
                    "evaluation_user_query": user_query,
                    "evaluation_conversation_context": context_str,
                    "evaluation_model": self.evaluation_model,
                    "threshold": self.threshold
                }
            )
            
            # Create LLMTestCase for DeepEval
            # DeepEval requires retrieval_context to be a non-empty list for metrics that use RETRIEVAL_CONTEXT
            # Provide minimal default context if none exists, so metrics that require it can still evaluate
            if context_str and context_str != "No previous conversation context.":
                retrieval_context = [context_str]
            else:
                # Provide minimal default context - some metrics (Coherence, Tonality) require retrieval_context
                # Use the user query as context since it provides the evaluation context
                retrieval_context = [f"User query: {user_query}"]
            
            test_case = LLMTestCase(
                input=user_query,
                actual_output=response,
                retrieval_context=retrieval_context
            )
            
            # Create metrics
            relevance_metric, coherence_metric, tonality_metric, safety_metric = self._create_metrics()
            
            # Measure each metric
            evaluation_metrics = [
                ("Relevance", relevance_metric),
                ("Coherence", coherence_metric),
                ("Tonality", tonality_metric),
                ("Safety", safety_metric)
            ]
            
            for name, metric in evaluation_metrics:
                metric.measure(test_case, _show_indicator=False)
                logger.debug(f"{name} evaluation: score={metric.score:.2f}")
            
            # Extract scores and reasons
            relevance_score = relevance_metric.score
            relevance_reason = relevance_metric.reason or "No reason provided"
            coherence_score = coherence_metric.score
            coherence_reason = coherence_metric.reason or "No reason provided"
            tonality_score = tonality_metric.score
            tonality_reason = tonality_metric.reason or "No reason provided"
            safety_score = safety_metric.score
            safety_reason = safety_metric.reason or "No reason provided"
            
            # Calculate needs_enhancement
            scores = [coherence_score, tonality_score, relevance_score, safety_score]
            needs_enhancement = any(score < self.threshold for score in scores)
            
            # Build ResponseEvaluation object
            evaluation = ResponseEvaluation(
                coherence=MetricEvaluation(score=coherence_score, reason=coherence_reason),
                tonality=MetricEvaluation(score=tonality_score, reason=tonality_reason),
                relevance=MetricEvaluation(score=relevance_score, reason=relevance_reason),
                safety=MetricEvaluation(score=safety_score, reason=safety_reason),
                needs_enhancement=needs_enhancement
            )
            
            # Log evaluation outputs (DEBUG level)
            self.ai_logger.log(
                category=LogCategory.EVALUATION,
                message="Response evaluation completed",
                severity=LogSeverity.DEBUG,
                conversation_id=conversation_id,
                metadata={
                    "coherence_score": coherence_score,
                    "coherence_reason": coherence_reason,
                    "tonality_score": tonality_score,
                    "tonality_reason": tonality_reason,
                    "relevance_score": relevance_score,
                    "relevance_reason": relevance_reason,
                    "safety_score": safety_score,
                    "safety_reason": safety_reason,
                    "needs_enhancement": needs_enhancement
                }
            )
            
            # Log summary (INFO level)
            logger.info(f"Response evaluation: coherence={coherence_score:.2f}, "
                       f"tonality={tonality_score:.2f}, "
                       f"relevance={relevance_score:.2f}, "
                       f"safety={safety_score:.2f}, "
                       f"needs_enhancement={needs_enhancement}")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}", exc_info=True)
            # Log error
            self.ai_logger.log(
                category=LogCategory.ERROR,
                message=f"Error evaluating response: {e}",
                severity=LogSeverity.ERROR,
                conversation_id=conversation_id,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            # Return a default evaluation that doesn't trigger enhancement
            return ResponseEvaluation(
                coherence=MetricEvaluation(score=1.0, reason="Evaluation error occurred"),
                tonality=MetricEvaluation(score=1.0, reason="Evaluation error occurred"),
                relevance=MetricEvaluation(score=1.0, reason="Evaluation error occurred"),
                safety=MetricEvaluation(score=1.0, reason="Evaluation error occurred"),
                needs_enhancement=False
            )

