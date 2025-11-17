# Tool Calls and Model Interaction

This document describes the available API tools and how the LLM model interacts with them through LangChain's function calling mechanism.

## Overview

The chat system uses LangChain's tool calling feature to enable the LLM to dynamically call API functions when needed. The model decides when to use tools based on the user's query and generates natural language responses incorporating the tool results.

## Available Tools

API tools are defined in `src/services/api_service.py` and registered via the `get_api_tools()` function. Semantic tools are defined in `src/services/semantic_service.py` and registered via the `get_semantic_tools()` function. Both are combined in the chat engine.

### 1. `get_recent_videos`

**Purpose**: Retrieve a summary of recently watched videos.

**Parameters**:
- `limit` (int, optional): Number of videos to retrieve. Default: 10
- `channel_id` (str, optional): Filter videos by specific channel ID

**Returns**: 
- A natural language string summarizing recent videos
- Format: "You've watched {count} videos recently. Here are some highlights:\n1. Video Title from Channel Name (duration) - watched {time_ago}\n..."

**When the model uses it**:
- User asks about recent viewing history
- User asks "what did I watch lately?"
- User asks about videos from a specific time period
- User asks about videos from a specific channel

**Example**:
```python
# User: "What videos have I watched recently?"
# Model calls: get_recent_videos(limit=10)
# Returns: "You've watched 10 videos recently. Here are some highlights:\n1. Python Tutorial from Tech Channel (15:30) - watched 2 hours ago\n..."
```

---

### 2. `get_video_details`

**Purpose**: Get detailed information about a specific video.

**Parameters**:
- `video_id` (str, required): YouTube video ID (11 characters)

**Returns**:
- A natural language string with video details including title, channel, duration, watch count, and when it was watched

**When the model uses it**:
- User mentions a specific video
- User provides a video ID
- User asks "tell me about this video"
- User asks about details of a video they watched

**Example**:
```python
# User: "Tell me about video abc123xyz45"
# Model calls: get_video_details(video_id="abc123xyz45")
# Returns: "You watched 'Python Tutorial' from Tech Channel. It's 15 minutes long and you watched it 3 times, most recently 2 days ago..."
```

---

### 3. `get_statistics`

**Purpose**: Get overall statistics about watch history.

**Parameters**: None

**Returns**:
- A natural language string summarizing statistics including:
  - Total videos watched
  - Total channels watched
  - Total watch time
  - Average video duration
  - Oldest and newest watch dates

**When the model uses it**:
- User asks about viewing patterns
- User asks "how many videos have I watched?"
- User asks about total watch time
- User asks about general statistics
- User asks "what are my viewing habits?"

**Example**:
```python
# User: "What are my watch statistics?"
# Model calls: get_statistics()
# Returns: "You've watched 1,234 videos across 156 channels. Your total watch time is approximately 245 hours..."
```

---

### 4. `get_channel_info`

**Purpose**: Get information about a specific channel.

**Parameters**:
- `channel_id` (str, optional): YouTube channel ID
- `channel_name` (str, optional): Channel name (alternative to channel_id)

**Returns**:
- A natural language string with channel details including:
  - Channel name
  - Total videos watched from this channel
  - Total watch time
  - Most recent video watched
  - Average video duration

**When the model uses it**:
- User asks about a specific channel
- User asks "tell me about Channel X"
- User asks about videos from a particular channel
- User asks for channel statistics

**Example**:
```python
# User: "Tell me about Tech Channel"
# Model calls: get_channel_info(channel_name="Tech Channel")
# Returns: "You've watched 45 videos from Tech Channel. Your total watch time from this channel is about 12 hours..."
```

---

### 5. `search_videos_by_topic`

**Purpose**: Search for videos by topic, subject, or theme using semantic search. This finds videos by meaning, not just keywords.

**Parameters**:
- `query` (str, required): The topic or subject to search for (e.g., 'machine learning', 'Python tutorials', 'cooking recipes')
- `n_results` (int, optional): Number of results to return. Default: 10
- `date_from` (str, optional): Filter by start date (YYYY-MM-DD format)
- `date_to` (str, optional): Filter by end date (YYYY-MM-DD format)
- `channel_id` (str, optional): Filter by channel ID
- `channel_name` (str, optional): Filter by channel name

**Returns**: 
- A natural language string listing matching videos with titles, channels, watch times, and relevance scores
- Format: "I found {count} videos that match your search:\n1. Video Title from Channel Name (watched {time_ago}) [relevance: {score}]\n..."

**When the model uses it**:
- User asks about videos on a specific topic
- User asks "what videos did I watch about X?"
- User wants to find videos by meaning or concept
- User asks for videos with optional filters (date range, channel)

**Example**:
```python
# User: "What videos did I watch about machine learning?"
# Model calls: search_videos_by_topic(query="machine learning", n_results=10)
# Returns: "I found 15 videos that match your search:\n1. Introduction to Neural Networks from Tech Educator (watched 2 weeks ago) [relevance: 0.92]\n..."
```

---

### 6. `find_similar_videos`

**Purpose**: Find videos similar to a specific video based on semantic similarity.

**Parameters**:
- `video_id` (str, required): YouTube video ID to find similar videos for
- `n_results` (int, optional): Number of similar videos to return. Default: 5

**Returns**:
- A natural language string listing similar videos with titles, channels, watch times, and relevance scores

**When the model uses it**:
- User asks for videos similar to one they mention
- User wants recommendations based on a video they watched
- User asks "what other videos are like this one?"

**Example**:
```python
# User: "What videos are similar to abc123xyz45?"
# Model calls: find_similar_videos(video_id="abc123xyz45", n_results=5)
# Returns: "I found 5 videos that match your search:\n1. Python Advanced Topics from Same Channel (watched 1 week ago) [relevance: 0.89]\n..."
```

---

## How Model Interaction Works

### 1. Tool Registration

Tools are registered when the `ChatEngine` is initialized:

```python
# In ChatEngine.__init__()
api_tools = get_api_tools()  # Returns list of 4 API tools
semantic_tools = get_semantic_tools()  # Returns list of 2 semantic tools
self.tools = api_tools + semantic_tools  # Combined list of 6 tools
self.model_with_tools = self.model.bind_tools(self.tools)
```

The `bind_tools()` method converts each tool into a function calling schema that the LLM understands. Each tool's description and parameters are automatically extracted from the function signature and docstring.

### 2. System Prompt

The system prompt dynamically includes tool descriptions:

```python
# In get_system_prompt()
tools_description = get_tools_description(tools)
# Includes: "1. get_recent_videos: Get a summary of recently watched videos..."
```

The model receives:
- Tool names and descriptions
- When to use each tool
- Parameter requirements
- Current user query
- Conversation history

### 3. Tool Calling Flow

When a user sends a message, the following flow occurs:

```
1. User Query → ChatEngine.process_message()
   ↓
2. Build messages list:
   - SystemMessage (with tool descriptions)
   - Conversation history (HumanMessage/AIMessage)
   - Current HumanMessage
   ↓
3. Model decides: Use tool or respond directly?
   ↓
4a. If tool call needed:
   - Model returns AIMessage with tool_calls
   - ChatEngine._handle_tool_calls() executes tools
   - Tool results added as ToolMessage
   - Model generates final response with tool results
   ↓
4b. If no tool needed:
   - Model returns direct response
   ↓
5. Response evaluation and enhancement
   ↓
6. Return final response to user
```

### 4. Tool Execution

When the model decides to call a tool:

```python
# Model response contains tool_calls
response.tool_calls = [
    {
        'name': 'get_recent_videos',
        'args': {'limit': 10},
        'id': 'call_abc123'
    }
]

# ChatEngine executes:
for tool_call in response.tool_calls:
    tool_name = tool_call['name']
    tool_args = tool_call['args']
    result = tool_map[tool_name].invoke(tool_args)
    
    # Result added as ToolMessage
    tool_messages.append(
        ToolMessage(
            content=str(result),
            tool_call_id=tool_call['id']
        )
    )

# Tool results sent back to model
messages.extend(tool_messages)
final_response = self.model_with_tools.invoke(messages)
```

### 5. Multiple Tool Calls

The model can call multiple tools in a single turn:

```python
# User: "Tell me about my recent videos and overall statistics"
# Model may call:
# 1. get_recent_videos(limit=10)
# 2. get_statistics()
# Then combines results into a single response
```

### 6. Tool Result Processing

All tools return **natural language strings**, not structured data. This allows the model to:
- Understand the results immediately
- Incorporate them naturally into responses
- Avoid parsing complex data structures
- Provide conversational responses

Example tool result:
```
"You've watched 10 videos recently. Here are some highlights:
1. Python Tutorial from Tech Channel (15:30) - watched 2 hours ago
2. Cooking Basics from Food Channel (8:45) - watched yesterday
..."
```

The model receives this string and can directly use it in its response without additional parsing.

---

## Tool Design Principles

### 1. Natural Language Returns

All tools return human-readable strings, not JSON or structured data. This simplifies model interaction and ensures responses are conversational.

### 2. Self-Contained Descriptions

Each tool's docstring serves as its description to the model. The model uses these descriptions to decide when to call tools.

### 3. Error Handling

Tools handle errors gracefully and return user-friendly error messages:
- "I couldn't find any videos in your watch history."
- "I encountered an issue retrieving your recent videos. Please try again later."

### 4. Optional Parameters

Most parameters are optional with sensible defaults, allowing the model to call tools with minimal information.

---

## Logging and Observability

All tool interactions are logged via the AI observability system:

- **Tool calls**: Logged with tool name, arguments, and timestamp
- **Tool results**: Logged with success/failure status and latency
- **Conversation tracking**: Each request gets a unique conversation_id

Example log entries:
```
- tool_call: Tool called: get_recent_videos
  Tool: get_recent_videos
  Args: {"limit": 10}
  
- tool_result: Tool get_recent_videos succeeded
  Tool: get_recent_videos
  Latency: 125.5ms
  Result preview: "You've watched 10 videos recently..."
```

---

## Example Interactions

### Example 1: Simple Tool Call

**User**: "What videos have I watched recently?"

**Flow**:
1. Model analyzes query → decides to call `get_recent_videos`
2. Calls `get_recent_videos(limit=10)`
3. Receives: "You've watched 10 videos recently. Here are some highlights:\n1. Video A...\n2. Video B..."
4. Model generates response: "Here are your recent videos:\n\nYou've watched 10 videos recently. Here are some highlights:\n1. Video A...\n2. Video B..."

### Example 2: Multiple Tool Calls

**User**: "Tell me about my watch statistics and recent videos"

**Flow**:
1. Model decides to call both `get_statistics()` and `get_recent_videos(limit=10)`
2. Executes both tools in parallel
3. Receives two tool results
4. Model combines results: "Your watch statistics show... and here are your recent videos..."

### Example 3: Semantic Search Tool Call

**User**: "What videos did I watch about machine learning?"

**Flow**:
1. Model analyzes query → decides to call `search_videos_by_topic`
2. Calls `search_videos_by_topic(query="machine learning", n_results=10)`
3. Receives: "I found 15 videos that match your search:\n1. Introduction to Neural Networks from Tech Educator (watched 2 weeks ago) [relevance: 0.92]\n..."
4. Model generates response: "I found 15 videos about machine learning in your history. Here are some highlights:\n\n1. Introduction to Neural Networks from Tech Educator (watched 2 weeks ago) [relevance: 0.92]\n..."

### Example 4: Hybrid Search with Filters

**User**: "Find me Python tutorials from last month"

**Flow**:
1. Model analyzes query → decides to call `search_videos_by_topic` with date filters
2. Calls `search_videos_by_topic(query="Python tutorials", date_from="2024-12-01", date_to="2024-12-31", n_results=10)`
3. Receives: "I found 8 videos that match your search:\n1. Python Basics from Programming Channel (watched Dec 5) [relevance: 0.91]\n..."
4. Model generates response: "I found 8 Python tutorials from December:\n\n1. Python Basics from Programming Channel (watched Dec 5) [relevance: 0.91]\n..."

### Example 5: Find Similar Videos

**User**: "What videos are similar to [video_id]?"

**Flow**:
1. Model analyzes query → decides to call `find_similar_videos`
2. Calls `find_similar_videos(video_id="...", n_results=5)`
3. Receives: "I found 5 videos that match your search:\n1. Python Advanced Topics from Same Channel (watched 1 week ago) [relevance: 0.89]\n..."
4. Model generates response: "Here are 5 videos similar to 'Python Tutorial':\n\n1. Python Advanced Topics from Same Channel (watched 1 week ago) [relevance: 0.89]\n..."

### Example 6: No Tool Needed

**User**: "Thanks for the help!"

**Flow**:
1. Model analyzes query → no tool needed
2. Responds directly: "You're welcome! Feel free to ask if you need anything else about your YouTube history."

---

## Technical Details

### Tool Definition

Tools are defined using LangChain's `@tool` decorator:

```python
@tool
def get_recent_videos(limit: int = 10, channel_id: Optional[str] = None) -> str:
    """
    Get a summary of recently watched videos. Use this when the user asks about 
    recent viewing history, what they watched lately, or videos from a specific time period.
    
    Args:
        limit: Number of videos to retrieve (default: 10)
        channel_id: Optional channel ID to filter by
    """
    return _api_service.get_recent_videos_summary(limit=limit, channel_id=channel_id)
```

### Message Types

The system uses four LangChain message types:

1. **SystemMessage**: Contains system prompt with tool descriptions
2. **HumanMessage**: User input
3. **AIMessage**: Model responses (may contain tool_calls)
4. **ToolMessage**: Results from tool execution

### Tool Binding

```python
# Tools are bound to the model
self.model_with_tools = self.model.bind_tools(self.tools)

# This enables function calling
response = self.model_with_tools.invoke(messages)
# Response may contain: response.tool_calls
```

---

## Best Practices

1. **Tool descriptions matter**: Clear, descriptive docstrings help the model decide when to use tools
2. **Natural language returns**: Tools return strings the model can directly use
3. **Error handling**: Tools should return user-friendly error messages
4. **Logging**: All tool interactions are logged for observability
5. **Conversation context**: The model receives conversation history to make informed tool call decisions

---

## Future Enhancements

Potential improvements:
- Parallel tool execution optimization
- Tool result caching for repeated queries
- More sophisticated tool selection based on conversation context
- Tool chaining (one tool's result feeds into another)

