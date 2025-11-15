"""Gradio chat interface for YouTube History Chat Application"""

import os
import sys

# Add parent directory to path to access utils.logger FIRST, before any other imports
# From src/app.py, go up to 05_src level (app.py -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../..'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)

from dotenv import load_dotenv
import gradio as gr

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.core.chat_engine import ChatEngine

load_dotenv()
load_dotenv('.secrets')

# Initialize chat engine
chat_engine = ChatEngine()


def chat_interface(message: str, history: list[dict]) -> str:
    """
    Gradio chat interface function.
    
    Args:
        message: User message
        history: Conversation history in Gradio format
        
    Returns:
        Assistant response
    """
    return chat_engine.process_message(message, history)


if __name__ == "__main__":
    gr.ChatInterface(
        fn=chat_interface,
        type="messages",
        title="YouTube History Chat",
        description="Ask questions about your YouTube watch history"
    ).launch()

