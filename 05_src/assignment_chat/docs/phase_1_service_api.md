# Phase 1: Service 1 - API Calls Integration

## Phase Overview

This phase implements Service 1, which calls the YouTube History API and transforms structured JSON responses into natural, conversational language summaries. The service will be integrated as a function tool that the LLM can call when users request API-based information.

## Objectives

1. Create API client wrapper for YouTube History API
2. Implement API service with transformation logic
3. Define function tool for LLM integration
4. Integrate service with Gradio chat interface
5. Add comprehensive error handling
6. Create unit tests and integration tests
7. Document API service capabilities

## Requirements

### Functional Requirements

1. **API Client Wrapper**
   - Wrap YouTube History API endpoints
   - Handle authentication (if needed)
   - Support pagination
   - Implement retry logic for failed requests
   - Handle rate limiting

2. **API Service**
   - Transform structured JSON responses to natural language
   - Support multiple endpoint types:
     - Video lists (`/api/v1/videos`)
     - Individual videos (`/api/v1/videos/{id}`)
     - Statistics (`/api/v1/stats`)
     - Channels (`/api/v1/channels`, `/api/v1/channels/{id}`)
     - Search results (`/api/v1/search`)
   - Generate contextually appropriate summaries
   - Maintain conversational tone

3. **Function Tool Definition**
   - Define OpenAI function tool schema
   - Accept natural language parameters
   - Return formatted text responses
   - Handle tool call errors gracefully

4. **Gradio Integration**
   - Integrate service into chat engine
   - Test service through chat interface
   - Verify natural language responses

### Technical Requirements

- **Transformation**: Responses must NOT be verbatim - must transform/rephrase
- **Error Handling**: User-friendly error messages
- **Performance**: Response time < 2 seconds for typical queries
- **Testing**: Unit tests with >80% coverage

## Implementation Specifications

### API Client Wrapper

**File**: `src/utils/api_client.py`

```python
import requests
from typing import Optional, Dict, List
from utils.logger import get_logger

class YouTubeHistoryAPIClient:
    """Client for YouTube History API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = get_logger(__name__)
    
    def get_videos(self, limit: int = 50, offset: int = 0, 
                   channel_id: Optional[str] = None) -> Dict:
        """Get paginated list of videos"""
        
    def get_video(self, video_id: str) -> Dict:
        """Get detailed video information"""
        
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        
    def get_channels(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of channels"""
        
    def get_channel(self, channel_id: str) -> Dict:
        """Get channel details"""
        
    def search_videos(self, query: str, **filters) -> Dict:
        """Search videos with filters"""
```

**Key Features**:
- Retry logic with exponential backoff
- Request timeout handling
- Error response parsing
- Pagination support

### API Service with Transformation

**File**: `src/services/api_service.py`

```python
from typing import Dict, List, Optional
from utils.api_client import YouTubeHistoryAPIClient

class APIService:
    """Service for API calls with natural language transformation"""
    
    def __init__(self, api_client: YouTubeHistoryAPIClient):
        self.api_client = api_client
    
    def get_recent_videos_summary(self, limit: int = 10) -> str:
        """Get summary of recent videos"""
        # Call API
        # Transform to natural language
        # Return formatted text
    
    def get_video_summary(self, video_id: str) -> str:
        """Get natural language summary of a video"""
    
    def get_statistics_summary(self) -> str:
        """Get natural language summary of statistics"""
    
    def get_channel_summary(self, channel_id: str) -> str:
        """Get natural language summary of a channel"""
    
    def transform_video_list(self, videos: List[Dict]) -> str:
        """Transform video list to natural language"""
        # Example: "You watched 15 videos last week, including 
        # 3 tutorials on Python from Tech Educator..."
    
    def transform_statistics(self, stats: Dict) -> str:
        """Transform statistics to natural language"""
        # Example: "Your watch history contains 1,250 videos 
        # across 150 channels. You've watched a total of 2,500 hours..."
```

### Transformation Examples

**Video List Transformation**:
```python
Input: [{"title": "Python Tutorial", "channel_name": "Tech", ...}, ...]
Output: "You watched 10 videos recently. Here are some highlights:
- Python Tutorial from Tech channel (watched 2 days ago)
- Machine Learning Basics from Data Science (watched 3 days ago)
..."
```

**Statistics Transformation**:
```python
Input: {"total_videos": 1250, "total_channels": 150, ...}
Output: "Your YouTube history is quite extensive! You've watched 
1,250 videos across 150 different channels. Your total watch time 
is approximately 2,500 hours..."
```

**Channel Transformation**:
```python
Input: {"name": "Tech Educator", "video_count": 50, ...}
Output: "Tech Educator is a channel you've watched frequently. 
You've viewed 50 videos from this channel, with your first watch 
dating back to January 2020..."
```

### Function Tool Definition

**File**: `src/services/api_service.py` (continued)

```python
def get_api_tools() -> List[Dict]:
    """Get function tool definitions for OpenAI"""
    return [
        {
            "type": "function",
            "name": "get_recent_videos",
            "description": "Get a summary of recently watched videos. Use this when the user asks about recent viewing history, what they watched lately, or videos from a specific time period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of videos to retrieve (default: 10)",
                        "default": 10
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Optional: Filter by channel ID"
                    }
                },
                "required": []
            }
        },
        {
            "type": "function",
            "name": "get_video_details",
            "description": "Get detailed information about a specific video. Use this when the user asks about a particular video or provides a video ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID (11 characters)"
                    }
                },
                "required": ["video_id"]
            }
        },
        {
            "type": "function",
            "name": "get_statistics",
            "description": "Get overall statistics about the watch history. Use this when the user asks about their viewing patterns, total videos watched, watch time, or general statistics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "type": "function",
            "name": "get_channel_info",
            "description": "Get information about a specific channel. Use this when the user asks about a channel, wants channel statistics, or asks about videos from a particular channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "YouTube channel ID"
                    },
                    "channel_name": {
                        "type": "string",
                        "description": "Channel name (alternative to channel_id)"
                    }
                },
                "required": []
            }
        }
    ]

def execute_api_tool(tool_name: str, arguments: Dict) -> str:
    """Execute API tool and return natural language response"""
    api_service = APIService(YouTubeHistoryAPIClient())
    
    if tool_name == "get_recent_videos":
        return api_service.get_recent_videos_summary(**arguments)
    elif tool_name == "get_video_details":
        return api_service.get_video_summary(arguments["video_id"])
    elif tool_name == "get_statistics":
        return api_service.get_statistics_summary()
    elif tool_name == "get_channel_info":
        return api_service.get_channel_summary(**arguments)
    else:
        return f"Unknown tool: {tool_name}"
```

### Integration with Chat Engine

**File**: `src/core/chat_engine.py` (partial)

```python
from services.api_service import get_api_tools, execute_api_tool

class ChatEngine:
    def __init__(self):
        self.tools = get_api_tools()  # Include API tools
        # ... other initialization
    
    def process_message(self, message: str, history: List[Dict]) -> str:
        # Make LLM call with tools
        # Handle function calls
        # Return response
```

## Validation Criteria

### Phase Completion Checklist

- [ ] API client wrapper implemented and tested
- [ ] API service transforms responses (not verbatim)
- [ ] Function tools defined and callable by LLM
- [ ] Service integrated with chat engine
- [ ] Gradio interface can use the service
- [ ] Error handling works correctly
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests pass
- [ ] Documentation complete
- [ ] Example transformations documented

### Test Cases

1. **API Client Tests**
   - Test successful API calls
   - Test pagination
   - Test error handling (404, 500, timeout)
   - Test retry logic

2. **Transformation Tests**
   - Verify responses are transformed (not verbatim)
   - Test different response types (video list, stats, channel)
   - Verify natural language quality
   - Test edge cases (empty results, missing fields)

3. **Function Tool Tests**
   - Test tool definitions are valid
   - Test tool execution
   - Test parameter validation
   - Test error handling

4. **Integration Tests**
   - Test service through chat interface
   - Test LLM can call tools correctly
   - Test end-to-end flow
   - Verify response quality

## Deliverables

1. **Code**
   - `src/utils/api_client.py`: API client implementation
   - `src/services/api_service.py`: API service with transformations
   - Integration in `src/core/chat_engine.py`

2. **Tests**
   - Unit tests for API client
   - Unit tests for transformations
   - Integration tests
   - Test fixtures/mocks

3. **Documentation**
   - API service capabilities documented
   - Transformation examples
   - Usage examples in README

## Planning Questions (Before Implementation)

1. **Transformation Style**
   - How detailed should summaries be?
   - Should we include specific numbers or general descriptions?
   - What tone should we use? (casual, formal, analytical)

2. **Tool Selection**
   - Which API endpoints should be exposed as tools?
   - How many tools should we create?
   - Should we combine multiple endpoints into single tools?

3. **Error Messages**
   - How should we handle API failures?
   - What level of detail in error messages?
   - Should we retry automatically or inform user?

4. **Performance**
   - What timeout values?
   - How many retries?
   - Should we cache responses?

## Example User Interactions

**User**: "What videos did I watch recently?"
- **Tool Called**: `get_recent_videos`
- **Response**: "You've watched 10 videos in the past week. Here are some highlights: Python Tutorial from Tech Educator (2 days ago), Machine Learning Basics from Data Science (3 days ago)..."

**User**: "Tell me about my watch history statistics"
- **Tool Called**: `get_statistics`
- **Response**: "Your YouTube history is quite extensive! You've watched 1,250 videos across 150 different channels. Your total watch time is approximately 2,500 hours, with an average video duration of 1 hour and 12 minutes..."

**User**: "What can you tell me about the Tech Educator channel?"
- **Tool Called**: `get_channel_info` (with channel_name="Tech Educator")
- **Response**: "Tech Educator is a channel you've watched frequently. You've viewed 50 videos from this channel, with your first watch dating back to January 2020 and your most recent watch just 2 days ago..."

## Next Steps

After Phase 1 completion:
1. Review validation criteria
2. Verify all deliverables are complete
3. Test service through Gradio interface
4. Document any issues or decisions
5. Proceed to Phase 2: Service 2 - Semantic Query Service

## Notes

- Focus on transformation quality - responses should feel natural
- Test with various API response formats
- Consider edge cases (empty results, missing fields)
- Document transformation patterns for consistency

---

**Phase Status**: Planning  
**Dependencies**: Phase 0 (Infrastructure)  
**Estimated Effort**: Medium

