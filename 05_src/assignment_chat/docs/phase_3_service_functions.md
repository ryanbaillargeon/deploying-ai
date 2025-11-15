# Phase 3: Service 3 - Function Calling Service

## Phase Overview

This phase implements Service 3, which provides advanced function calling capabilities for complex multi-parameter queries. This service enables queries that combine semantic search with metadata analysis, statistical aggregations, and multi-step reasoning. Examples include "channels that post most about AI" and "most watched videos last month".

## Objectives

1. Create function service with multiple function tools
2. Implement query routing and execution logic
3. Support multi-step queries (semantic search + aggregation)
4. Integrate with API and semantic services
5. Create comprehensive test cases
6. Document all available functions
7. Integrate with chat engine and Gradio interface

## Requirements

### Functional Requirements

1. **Function Tools**
   - Multiple function tools for different query types
   - Support complex parameter combinations
   - Handle multi-step query execution
   - Return formatted natural language responses

2. **Query Types**
   - **Channel Analytics**: Aggregate statistics by channel with topic filtering
     - Example: "channels that post most about AI"
   - **Watch Statistics**: Time-based statistics with optional topic filtering
     - Example: "most watched videos last month"
   - **Topic Analysis**: Analyze viewing patterns by topic
     - Example: "what topics do I watch most?"
   - **Similar Video Discovery**: Find similar videos based on content
   - **Trend Analysis**: Identify viewing trends over time

3. **Multi-Parameter Support**
   - Combine semantic search with metadata filters
   - Aggregate results across multiple dimensions
   - Support date ranges, channel filters, topic filters
   - Handle complex filter combinations

4. **Integration**
   - Integrate with API service (Service 1)
   - Integrate with semantic service (Service 2)
   - Coordinate multi-step queries
   - Return unified responses

### Technical Requirements

- **Function Calling**: Use OpenAI function calling API
- **Performance**: Complex queries should complete in < 3 seconds
- **Error Handling**: Graceful handling of invalid inputs
- **Testing**: Comprehensive test suite covering all functions

## Implementation Specifications

### Function Service

**File**: `src/services/function_service.py`

```python
from typing import Dict, List, Optional
from services.api_service import APIService
from services.semantic_service import SemanticService
from utils.api_client import YouTubeHistoryAPIClient

class FunctionService:
    """Service for complex function calling queries"""
    
    def __init__(self):
        self.api_service = APIService(YouTubeHistoryAPIClient())
        self.semantic_service = SemanticService(...)
    
    def get_channel_analytics(self, topic: Optional[str] = None,
                             date_from: Optional[str] = None,
                             date_to: Optional[str] = None,
                             limit: int = 10) -> str:
        """Get channel statistics filtered by topic and date range"""
        # 1. If topic provided, perform semantic search
        # 2. Filter by date if provided
        # 3. Aggregate by channel
        # 4. Return formatted results
    
    def get_watch_statistics(self, topic: Optional[str] = None,
                            date_from: Optional[str] = None,
                            date_to: Optional[str] = None) -> str:
        """Get watch statistics with optional topic filtering"""
        # 1. Get base statistics from API
        # 2. If topic provided, filter using semantic search
        # 3. Calculate statistics
        # 4. Return formatted results
    
    def analyze_topics(self, date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      limit: int = 10) -> str:
        """Analyze most watched topics"""
        # 1. Get videos in date range
        # 2. Group by semantic similarity or keywords
        # 3. Return top topics
    
    def find_similar_content(self, video_id: str, n_results: int = 5) -> str:
        """Find videos similar to a given video"""
        # Use semantic service
        # Return formatted results
```

### Function Tool Definitions

**File**: `src/services/function_service.py` (continued)

```python
def get_function_tools() -> List[Dict]:
    """Get function tool definitions for complex queries"""
    return [
        {
            "type": "function",
            "name": "get_channel_analytics",
            "description": "Get statistics about channels, optionally filtered by topic and date range. Use this when the user asks about channels, wants to know which channels post about a topic, asks 'channels that post most about X', or wants channel statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Optional: Filter channels by topic (e.g., 'AI', 'machine learning', 'Python')"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Optional: Start date for filtering (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Optional: End date for filtering (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top channels to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "type": "function",
            "name": "get_watch_statistics",
            "description": "Get watch statistics with optional topic and date filtering. Use this when the user asks about their viewing patterns, wants statistics about their watch history, asks 'most watched videos in X period', or wants to analyze their viewing habits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Optional: Filter statistics by topic"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Optional: Start date (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Optional: End date (YYYY-MM-DD)"
                    }
                },
                "required": []
            }
        },
        {
            "type": "function",
            "name": "analyze_topics",
            "description": "Analyze the most watched topics in viewing history. Use this when the user asks about their viewing interests, wants to know what topics they watch most, or asks 'what do I watch most?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Optional: Start date for analysis (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Optional: End date for analysis (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of topics to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "type": "function",
            "name": "get_trending_topics",
            "description": "Identify trending topics over time. Use this when the user asks about viewing trends, wants to see how their interests changed, or asks 'what topics did I watch more of recently?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period to analyze (e.g., 'last_month', 'last_3_months', 'last_year')",
                        "enum": ["last_week", "last_month", "last_3_months", "last_6_months", "last_year"]
                    }
                },
                "required": ["period"]
            }
        }
    ]

def execute_function_tool(tool_name: str, arguments: Dict) -> str:
    """Execute function tool and return natural language response"""
    function_service = FunctionService()
    
    if tool_name == "get_channel_analytics":
        return function_service.get_channel_analytics(**arguments)
    elif tool_name == "get_watch_statistics":
        return function_service.get_watch_statistics(**arguments)
    elif tool_name == "analyze_topics":
        return function_service.analyze_topics(**arguments)
    elif tool_name == "get_trending_topics":
        return function_service.get_trending_topics(**arguments)
    else:
        return f"Unknown function: {tool_name}"
```

### Multi-Step Query Implementation

**Example: "channels that post most about AI"**

```python
def get_channel_analytics(self, topic: Optional[str] = None, **kwargs) -> str:
    """Get channel statistics filtered by topic"""
    
    if topic:
        # Step 1: Semantic search for topic
        semantic_results = self.semantic_service.search_by_topic(
            query=topic,
            n_results=100  # Get more results for aggregation
        )
        
        # Step 2: Extract video IDs and get channel info
        video_ids = [r.get("id") for r in semantic_results]
        
        # Step 3: Get channel information for these videos
        channels = {}
        for video_id in video_ids:
            video = self.api_service.get_video_details(video_id)
            channel_id = video.get("channel_id")
            if channel_id not in channels:
                channels[channel_id] = {
                    "name": video.get("channel_name"),
                    "count": 0,
                    "videos": []
                }
            channels[channel_id]["count"] += 1
            channels[channel_id]["videos"].append(video_id)
        
        # Step 4: Sort by count and format
        sorted_channels = sorted(
            channels.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:kwargs.get("limit", 10)]
        
        # Step 5: Format response
        return self._format_channel_analytics(sorted_channels, topic)
    
    else:
        # No topic filter - use API statistics
        return self.api_service.get_channel_statistics(**kwargs)
```

### Query Routing Logic

```python
class QueryRouter:
    """Route queries to appropriate functions"""
    
    def route_query(self, user_query: str) -> Dict:
        """Determine which function(s) to call"""
        # Analyze user query
        # Determine intent
        # Return function name and parameters
        pass
```

## Query Examples and Use Cases

### Channel Analytics Queries
- "Which channels post most about AI?"
- "What channels do I watch for Python content?"
- "Show me channels about machine learning"

### Watch Statistics Queries
- "What were my most watched videos last month?"
- "How many videos did I watch about Python in November?"
- "Show me statistics for my AI-related viewing"

### Topic Analysis Queries
- "What topics do I watch most?"
- "What are my main viewing interests?"
- "Analyze my viewing patterns by topic"

### Trend Analysis Queries
- "What topics did I watch more of recently?"
- "How have my viewing interests changed?"
- "Show me trending topics in my watch history"

## Validation Criteria

### Phase Completion Checklist

- [ ] Function service implemented
- [ ] All function tools defined
- [ ] Multi-step queries work correctly
- [ ] Integration with API and semantic services
- [ ] Query routing logic implemented
- [ ] Service integrated with chat engine
- [ ] Gradio interface can use functions
- [ ] Complex queries execute correctly
- [ ] Error handling works for invalid inputs
- [ ] Comprehensive test suite
- [ ] Documentation complete

### Test Cases

1. **Channel Analytics**
   - Test with topic filter
   - Test with date range
   - Test with both filters
   - Test without filters

2. **Watch Statistics**
   - Test basic statistics
   - Test with topic filter
   - Test with date range
   - Test complex combinations

3. **Topic Analysis**
   - Test topic extraction
   - Test with date ranges
   - Verify accuracy

4. **Multi-Step Queries**
   - Test "channels that post most about X"
   - Test "most watched videos about X in period Y"
   - Verify all steps execute correctly

5. **Error Handling**
   - Invalid parameters
   - Missing data
   - API failures
   - Empty results

6. **Integration**
   - Test through chat interface
   - Verify LLM calls functions correctly
   - Test end-to-end flow

## Deliverables

1. **Code**
   - `src/services/function_service.py`: Function service implementation
   - Query routing logic
   - Integration in `src/core/chat_engine.py`

2. **Tests**
   - Unit tests for each function
   - Integration tests for multi-step queries
   - Error handling tests
   - End-to-end tests

3. **Documentation**
   - All functions documented
   - Usage examples
   - Query examples
   - Limitations documented

## Planning Questions (Before Implementation)

1. **Function Design**
   - How many functions should we create?
   - Should functions be specialized or general?
   - How to handle function parameter validation?

2. **Multi-Step Queries**
   - How to coordinate multiple service calls?
   - Should we cache intermediate results?
   - How to handle partial failures?

3. **Aggregation Logic**
   - How to aggregate semantic search results?
   - How to group videos by topic?
   - How to calculate statistics?

4. **Performance**
   - How to optimize multi-step queries?
   - Should we parallelize service calls?
   - How to handle timeouts?

## Example User Interactions

**User**: "Which channels post most about AI?"
- **Tool Called**: `get_channel_analytics(topic="AI", limit=10)`
- **Process**:
  1. Semantic search for "AI" → get video IDs
  2. Get channel info for each video
  3. Aggregate by channel
  4. Sort by count
- **Response**: "Based on your viewing history, here are the channels that post most about AI:
  1. Tech Educator - 25 videos about AI
  2. AI Research Channel - 18 videos
  3. Machine Learning Hub - 15 videos..."

**User**: "What were my most watched videos last month?"
- **Tool Called**: `get_watch_statistics(date_from="2024-12-01", date_to="2024-12-31")`
- **Process**:
  1. Get videos from date range via API
  2. Sort by watch count or frequency
  3. Format results
- **Response**: "In December, your most watched videos were:
  1. Python Tutorial Series - watched 5 times
  2. Machine Learning Basics - watched 4 times..."

**User**: "What topics do I watch most?"
- **Tool Called**: `analyze_topics(limit=10)`
- **Process**:
  1. Get all videos
  2. Group by topic (using semantic similarity or keywords)
  3. Count videos per topic
  4. Return top topics
- **Response**: "Based on your viewing history, your top interests are:
  1. Python Programming - 150 videos
  2. Machine Learning - 120 videos
  3. Data Science - 95 videos..."

## Next Steps

After Phase 3 completion:
1. Review validation criteria
2. Verify all deliverables are complete
3. Test all function types
4. Document any issues or decisions
5. Proceed to Phase 4: Final Integration & Polish

## Notes

- Focus on making complex queries work smoothly
- Ensure functions integrate well with other services
- Test with various query combinations
- Document function capabilities and limitations clearly

---

**Phase Status**: Planning  
**Dependencies**: Phase 0 (Infrastructure), Phase 1 (API Service), Phase 2 (Semantic Service)  
**Estimated Effort**: High

