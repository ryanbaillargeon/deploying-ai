"""AI Observability Package - Reusable logging and monitoring system for AI/LLM applications"""

from .storage import LogStorage

# UI components are imported lazily to avoid module loading warnings
# Use get_ui_components() to access them when needed
_AILogViewer = None
_launch_ui = None
_ui_imported = False


def _import_ui_components():
    """Lazy import of UI components to avoid module loading warnings"""
    global _AILogViewer, _launch_ui, _ui_imported
    if not _ui_imported:
        try:
            from .ui import AILogViewer, launch_ui
            _AILogViewer = AILogViewer
            _launch_ui = launch_ui
        except ImportError:
            # Gradio not available, UI features disabled
            _AILogViewer = None
            _launch_ui = None
        finally:
            _ui_imported = True
    return _AILogViewer, _launch_ui


def get_ui_components():
    """
    Get UI components (lazy import).
    
    Returns:
        tuple: (AILogViewer, launch_ui) or (None, None) if gradio not available
    """
    return _import_ui_components()


def __getattr__(name):
    """Lazy attribute access for UI components to avoid module loading warnings"""
    if name == 'AILogViewer':
        AILogViewer, _ = _import_ui_components()
        return AILogViewer
    elif name == 'launch_ui':
        _, launch_ui = _import_ui_components()
        return launch_ui
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Import logger components from utils
import sys
import os
from pathlib import Path

# Add utils to path if not already there
_utils_path = Path(__file__).parent.parent / "utils"
if str(_utils_path) not in sys.path:
    sys.path.insert(0, str(_utils_path))

try:
    from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity, AILogger
except ImportError:
    # If utils is not in path, provide fallback
    AILogger = None
    LogCategory = None
    LogSeverity = None
    get_ai_logger = None

__all__ = [
    'LogStorage',
    'AILogViewer',
    'launch_ui',
    'AILogger',
    'LogCategory',
    'LogSeverity',
    'get_ai_logger',
]

