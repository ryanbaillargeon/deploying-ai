"""Model factory for initializing chat models with local/online switching support"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path to import logger
# From src/core/model_factory.py, go up to 05_src level (core -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../../'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger

from langchain.chat_models import init_chat_model

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


def get_chat_model(model_name: Optional[str] = None, 
                   temperature: float = 0.7,
                   **kwargs):
    """
    Initialize a chat model with support for local (LM Studio) and online models.
    
    Args:
        model_name: Model identifier (e.g., 'gpt-4o', 'local-model')
                   If None, reads from USE_LOCAL_LLM env var
        temperature: Model temperature
        **kwargs: Additional model parameters
        
    Returns:
        LangChain chat model instance
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set for online models
    """
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    if use_local or (model_name and "local" in model_name.lower()):
        # Local model via LM Studio
        base_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
        model_id = model_name or os.getenv("LOCAL_MODEL_NAME", "local-model")
        
        logger.info(f"Initializing local model: {model_id} at {base_url}")
        
        # For LM Studio, use just the model name without 'openai:' prefix
        # LM Studio expects the exact model name as shown in its interface
        return init_chat_model(
            model_id,  # Use model name directly, not "openai:model_id"
            model_provider="openai",
            base_url=base_url,
            api_key="not-needed",
            temperature=temperature,
            **kwargs
        )
    else:
        # Online model (OpenAI)
        model_id = model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Required for online models.")
        
        logger.info(f"Initializing online model: {model_id}")
        
        return init_chat_model(
            f"openai:{model_id}",
            model_provider="openai",
            temperature=temperature,
            **kwargs
        )

