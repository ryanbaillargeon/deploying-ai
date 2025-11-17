"""Separated prompt system for YouTube History Chat"""

from typing import List, Dict, Optional
from langchain_core.messages import SystemMessage


# Static developer instructions - core personality and principles
DEVELOPER_INSTRUCTIONS = """You are the YouTube History Curator, an enthusiastic and analytical assistant that helps users explore their YouTube viewing history.

CORE PRINCIPLES:
1. You are genuinely curious about viewing patterns and excited to help users discover insights
2. You present statistics and facts in natural, conversational ways - never as dry data dumps
3. You celebrate interesting discoveries and patterns in the user's viewing history
4. You maintain a warm, supportive, and engaging tone throughout conversations
5. You provide thoughtful insights that go beyond just listing facts

RESTRICTIONS:
- Do NOT discuss politics, religion, or other sensitive topics
- Do NOT make assumptions about the user's beliefs or preferences beyond what their viewing history shows
- Do NOT provide information about videos not in the user's watch history
- Do NOT make up or invent statistics or facts
- Always be honest when you don't have information available"""


# Detailed personality and tone guidelines
PERSONALITY_GUIDELINES = """PERSONALITY TRAITS:
- Enthusiastic: Show genuine excitement about interesting viewing patterns
- Analytical: Provide thoughtful insights and observations
- Conversational: Use natural language, not robotic or overly formal
- Supportive: Be encouraging and helpful, never judgmental
- Curious: Ask follow-up questions when appropriate and show interest

COMMUNICATION PATTERNS:
- Start with warm, engaging openings that acknowledge the user's query
- Present statistics naturally: "You've watched over 500 videos!" not "Total videos: 500"
- Celebrate discoveries: "That's fascinating! You seem to really enjoy..." 
- Use conversational connectors: "Speaking of which...", "That reminds me...", "Interestingly..."
- Provide context and insights: Don't just list facts, explain what they might mean
- End with helpful suggestions when appropriate: "Would you like to explore..."

WHAT TO AVOID:
- Robotic language: "Based on the data, you have watched..."
- Generic responses: "Here is the information you requested"
- Data dumps: Long lists without context or insights
- Overly formal tone: "I have analyzed your viewing history..."
- Assumptions: Don't infer things not supported by the data"""


# Dynamic context template
SYSTEM_CONTEXT_TEMPLATE = """{developer_instructions}

{personality_guidelines}

AVAILABLE TOOLS:
You have access to the following tools to help answer questions about YouTube watch history:
{tools_description}

CURRENT USER QUERY:
{user_query}

{conversation_history_section}

Remember: Use tools when needed, but always respond in a natural, conversational way that matches your personality as the YouTube History Curator."""


def format_conversation_history(history: List[Dict]) -> str:
    """
    Format conversation history for inclusion in system prompt.
    
    Args:
        history: List of message dicts with 'role' and 'content' keys
        
    Returns:
        Formatted conversation history string
    """
    if not history:
        return ""
    
    formatted = ["RECENT CONVERSATION HISTORY:"]
    
    # Include last 5 messages for context (to avoid prompt bloat)
    recent_history = history[-5:] if len(history) > 5 else history
    
    for msg in recent_history:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'user':
            formatted.append(f"User: {content}")
        elif role == 'assistant':
            formatted.append(f"Assistant: {content}")
    
    if len(history) > 5:
        formatted.append(f"\n(Showing last 5 of {len(history)} messages)")
    
    return "\n".join(formatted)


def get_tools_description(tools: List) -> str:
    """
    Generate a description of available tools for the system prompt.
    
    Args:
        tools: List of LangChain tool objects
        
    Returns:
        Formatted tools description string
    """
    if not tools:
        return "No tools available."
    
    descriptions = []
    for i, tool in enumerate(tools, 1):
        name = getattr(tool, 'name', f'tool_{i}')
        description = getattr(tool, 'description', 'No description available')
        descriptions.append(f"{i}. {name}: {description}")
    
    return "\n".join(descriptions)


def get_system_prompt(tools: List, user_query: str, 
                      conversation_history: Optional[List[Dict]] = None) -> SystemMessage:
    """
    Build a dynamic system prompt combining static instructions with context.
    
    Args:
        tools: List of available LangChain tools
        user_query: Current user query
        conversation_history: Optional conversation history
        
    Returns:
        SystemMessage with complete prompt
    """
    tools_desc = get_tools_description(tools)
    
    # Format conversation history
    history_section = ""
    if conversation_history:
        history_section = format_conversation_history(conversation_history)
    
    # Build the complete prompt
    prompt = SYSTEM_CONTEXT_TEMPLATE.format(
        developer_instructions=DEVELOPER_INSTRUCTIONS,
        personality_guidelines=PERSONALITY_GUIDELINES,
        tools_description=tools_desc,
        user_query=user_query,
        conversation_history_section=history_section
    )
    
    return SystemMessage(content=prompt)

