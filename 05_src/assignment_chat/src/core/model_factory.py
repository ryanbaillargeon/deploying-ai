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
                   purpose: Optional[str] = None,
                   **kwargs):
    """
    Initialize a chat model with support for local (LM Studio) and online models.
    
    Args:
        model_name: Model identifier (e.g., 'gpt-4o', 'local-model')
                   If None, checks purpose-specific env var (e.g., CHAT_MODEL, EVALUATION_MODEL)
                   then falls back to OPENAI_MODEL or LOCAL_MODEL_NAME
        temperature: Model temperature
        purpose: Optional description of what this model is used for (e.g., "chat", "evaluation", "enhancement")
                 Used to check purpose-specific environment variables
        **kwargs: Additional model parameters
        
    Returns:
        LangChain chat model instance
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set for online models
    """
    # Check for purpose-specific model name first
    if model_name is None and purpose:
        purpose_env_var = f"{purpose.upper()}_MODEL"  # e.g., "CHAT_MODEL", "EVALUATION_MODEL"
        purpose_model = os.getenv(purpose_env_var)
        if purpose_model:
            model_name = purpose_model
    
    # Known OpenAI model names (these will use online mode unless forced to local)
    known_openai_models = {
        "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo",
        "gpt-4o-2024-08-06", "gpt-4-turbo-2024-04-09", "gpt-3.5-turbo-0125"
    }
    
    # Check if model name is a known OpenAI model
    is_known_openai_model = model_name and model_name.lower() in {m.lower() for m in known_openai_models}
    
    # Check for purpose-specific local flag first (e.g., USE_LOCAL_CHAT, USE_LOCAL_EVALUATION)
    purpose_local_override = None
    if purpose:
        purpose_local_flag = f"USE_LOCAL_{purpose.upper()}"  # e.g., "USE_LOCAL_CHAT"
        purpose_local = os.getenv(purpose_local_flag)
        if purpose_local:
            purpose_local_override = purpose_local.lower() == "true"
    
    # Determine if this should be local or online
    # Priority: 1) purpose-specific flag, 2) model name contains "local", 3) known OpenAI model = online, 4) global USE_LOCAL_LLM
    if purpose_local_override is not None:
        # Purpose-specific flag explicitly set
        use_local = purpose_local_override
    elif model_name and "local" in model_name.lower():
        # Model name explicitly indicates local
        use_local = True
    elif is_known_openai_model:
        # Known OpenAI model - use online unless forced
        use_local = False
    else:
        # Fall back to global USE_LOCAL_LLM setting
        use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    if use_local:
        # Local model via LM Studio
        base_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
        model_id = model_name or os.getenv("LOCAL_MODEL_NAME", "local-model")
        
        purpose_str = f" ({purpose})" if purpose else ""
        logger.info(f"Initializing local model{purpose_str}: {model_id} at {base_url}")
        
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
        # If model_name is still None, fall back to OPENAI_MODEL
        # (purpose-specific check already happened above)
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # Strip any provider prefix if present (e.g., "openai:gpt-4o" -> "gpt-4o")
        # LangChain's init_chat_model with model_provider="openai" expects just the model name
        if ':' in model_name:
            model_id = model_name.split(':', 1)[1]
        else:
            model_id = model_name
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Required for online models.")
        
        purpose_str = f" ({purpose})" if purpose else ""
        logger.info(f"Initializing online model{purpose_str}: {model_id}")
        
        # When using model_provider="openai", pass just the model name, not "openai:model_name"
        return init_chat_model(
            model_id,
            model_provider="openai",
            temperature=temperature,
            **kwargs
        )

