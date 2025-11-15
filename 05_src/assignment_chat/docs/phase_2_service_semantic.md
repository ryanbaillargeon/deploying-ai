# Phase 2: Service 2 - Semantic Query Service

## Phase Overview

This phase implements Service 2, which enables semantic search over YouTube history using ChromaDB vector database. The service allows users to find videos by meaning, topics, opinions, and technologies rather than just keywords. It supports hybrid search combining semantic similarity with metadata filtering.

## Objectives

1. Create semantic service with ChromaDB integration
2. Implement query embedding and similarity search
3. Support hybrid search (semantic + metadata filtering)
4. Define function tool for semantic queries
5. Integrate with chat engine and Gradio interface
6. Create comprehensive test queries
7. Document search capabilities and limitations

## Requirements

### Functional Requirements

1. **Semantic Search**
   - Embed user queries using same model as data
   - Perform similarity search in ChromaDB
   - Return top-k most relevant videos
   - Support various query types:
     - Topic-based: "videos about machine learning"
     - Opinion-based: "videos discussing AI ethics"
     - Technology-based: "tutorials on React"
     - Concept-based: "videos explaining neural networks"

2. **Hybrid Search**
   - Combine semantic search with metadata filters:
     - Date ranges (date_from, date_to)
     - Channel filtering (channel_id, channel_name)
     - Duration filtering (min_duration, max_duration)
   - Apply filters after semantic search or during query

3. **Query Processing**
   - Handle natural language queries
   - Extract intent and parameters
   - Route to appropriate search function
   - Format results naturally

4. **Result Enrichment**
   - Enrich semantic search results with API data if needed
   - Include relevant metadata in responses
   - Provide context about why results are relevant

### Technical Requirements

- **Embedding Model**: Must match Phase 0 model (text-embedding-3-small)
- **ChromaDB**: Use existing collection from Phase 0
- **Performance**: Query time < 1 second for typical searches
- **Relevance**: Top results should be >80% relevant to query
- **Testing**: Comprehensive test suite with example queries

## Implementation Specifications

### Semantic Service

**File**: `src/services/semantic_service.py`

```python
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
from typing import List, Dict, Optional
import os

class SemanticService:
    """Service for semantic search over YouTube history"""
    
    def __init__(self, chroma_db_path: str, collection_name: str):
        self.client = PersistentClient(path=chroma_db_path)
        self.collection = self.client.get_collection(collection_name)
        self.openai_client = OpenAI()
        self.embedding_model = "text-embedding-3-small"
    
    def search_by_topic(self, query: str, n_results: int = 10, 
                       filters: Optional[Dict] = None) -> List[Dict]:
        """Perform semantic search by topic"""
        # 1. Embed query
        # 2. Query ChromaDB
        # 3. Apply metadata filters if provided
        # 4. Return results with metadata
    
    def search_by_opinion(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search for videos discussing opinions or viewpoints"""
    
    def search_by_technology(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search for videos about specific technologies"""
    
    def hybrid_search(self, query: str, n_results: int = 10,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     channel_id: Optional[str] = None,
                     min_duration: Optional[int] = None,
                     max_duration: Optional[int] = None) -> List[Dict]:
        """Perform hybrid semantic + metadata search"""
        # 1. Semantic search
        # 2. Filter by metadata
        # 3. Return filtered results
    
    def format_results(self, results: List[Dict]) -> str:
        """Format search results as natural language"""
```

### Query Embedding

```python
def embed_query(self, query: str) -> List[float]:
    """Embed user query using OpenAI"""
    response = self.openai_client.embeddings.create(
        model=self.embedding_model,
        input=query
    )
    return response.data[0].embedding
```

### ChromaDB Query

```python
def query_chromadb(self, query_text: str, n_results: int = 10,
                  where: Optional[Dict] = None) -> Dict:
    """Query ChromaDB collection"""
    # Use collection.query() with embedding function
    # Apply metadata filters using 'where' clause
    results = self.collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where  # Metadata filters
    )
    return results
```

### Hybrid Search Implementation

```python
def hybrid_search(self, query: str, n_results: int = 10, **filters) -> List[Dict]:
    """Hybrid search combining semantic and metadata filtering"""
    
    # Build where clause for metadata filters
    where_clause = {}
    if filters.get("channel_id"):
        where_clause["channel_id"] = filters["channel_id"]
    if filters.get("date_from"):
        # Note: ChromaDB where clauses may need date handling
        # May need to filter results after query
        pass
    
    # Perform semantic search
    results = self.collection.query(
        query_texts=[query],
        n_results=n_results * 2  # Get more results for filtering
    )
    
    # Apply post-query filters if ChromaDB doesn't support them
    filtered_results = self._apply_filters(results, filters)
    
    return filtered_results[:n_results]
```

### Function Tool Definition

**File**: `src/services/semantic_service.py` (continued)

```python
def get_semantic_tools() -> List[Dict]:
    """Get function tool definitions for semantic search"""
    return [
        {
            "type": "function",
            "name": "search_videos_by_topic",
            "description": "Search for videos by topic, subject, or theme using semantic search. Use this when the user asks about videos on a specific topic, wants to find videos about something, or asks 'what videos did I watch about X'. This finds videos by meaning, not just keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic or subject to search for (e.g., 'machine learning', 'Python tutorials', 'cooking recipes')"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Optional: Filter by start date (YYYY-MM-DD format)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Optional: Filter by end date (YYYY-MM-DD format)"
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Optional: Filter by channel ID"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "type": "function",
            "name": "find_similar_videos",
            "description": "Find videos similar to a specific video. Use this when the user asks for videos similar to one they mention, or wants recommendations based on a video they watched.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID to find similar videos for"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of similar videos to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["video_id"]
            }
        }
    ]

def execute_semantic_tool(tool_name: str, arguments: Dict) -> str:
    """Execute semantic tool and return natural language response"""
    semantic_service = SemanticService(
        chroma_db_path=os.getenv("CHROMA_DB_PATH"),
        collection_name=os.getenv("CHROMA_COLLECTION_NAME")
    )
    
    if tool_name == "search_videos_by_topic":
        results = semantic_service.hybrid_search(**arguments)
        return semantic_service.format_results(results)
    elif tool_name == "find_similar_videos":
        # Get video embedding, then find similar
        results = semantic_service.find_similar_videos(**arguments)
        return semantic_service.format_results(results)
    else:
        return f"Unknown tool: {tool_name}"
```

### Result Formatting

```python
def format_results(self, results: List[Dict]) -> str:
    """Format search results as natural language"""
    if not results:
        return "I couldn't find any videos matching your search."
    
    formatted = f"I found {len(results)} videos that match your search:\n\n"
    
    for i, result in enumerate(results, 1):
        video_id = result.get("video_id") or result.get("id")
        title = result.get("metadata", {}).get("title", "Unknown")
        channel = result.get("metadata", {}).get("channel_name", "Unknown")
        watched_at = result.get("metadata", {}).get("watched_at", "Unknown")
        distance = result.get("distance", 0)
        
        formatted += f"{i}. {title}\n"
        formatted += f"   Channel: {channel}\n"
        formatted += f"   Watched: {watched_at}\n"
        if distance:
            formatted += f"   Relevance: {1 - distance:.2f}\n"
        formatted += "\n"
    
    return formatted
```

## Query Types and Examples

### Topic-Based Queries
- "videos about machine learning"
- "tutorials on Python programming"
- "videos explaining neural networks"
- "content about data science"

### Opinion-Based Queries
- "videos discussing AI ethics"
- "opinions on climate change"
- "debates about technology"

### Technology-Based Queries
- "React tutorials"
- "Docker explanations"
- "Kubernetes guides"

### Metadata Queries (Hybrid)
- "videos about Python from last month"
- "machine learning tutorials longer than 30 minutes"
- "AI videos from Tech Educator channel"

## Validation Criteria

### Phase Completion Checklist

- [ ] Semantic service implemented
- [ ] ChromaDB queries work correctly
- [ ] Query embedding matches data embedding model
- [ ] Hybrid search combines semantic + metadata filters
- [ ] Function tools defined and callable
- [ ] Service integrated with chat engine
- [ ] Gradio interface can use semantic search
- [ ] Results are relevant (>80% relevance)
- [ ] Comprehensive test suite with example queries
- [ ] Documentation complete

### Test Cases

1. **Basic Semantic Search**
   - Test topic-based queries
   - Verify results are relevant
   - Test different query phrasings return similar results

2. **Hybrid Search**
   - Test semantic search + date filter
   - Test semantic search + channel filter
   - Test semantic search + duration filter
   - Test multiple filters combined

3. **Edge Cases**
   - Empty query results
   - Very specific queries
   - Very broad queries
   - Queries with no matches

4. **Performance**
   - Query time < 1 second
   - Handle large result sets
   - Efficient filtering

5. **Integration**
   - Test through chat interface
   - Verify LLM calls tools correctly
   - Test end-to-end flow

## Deliverables

1. **Code**
   - `src/services/semantic_service.py`: Semantic service implementation
   - Integration in `src/core/chat_engine.py`
   - Helper functions for query processing

2. **Tests**
   - Unit tests for semantic search
   - Unit tests for hybrid search
   - Integration tests
   - Test queries covering all query types

3. **Documentation**
   - Search capabilities documented
   - Query examples
   - Limitations and known issues
   - Usage examples in README

## Planning Questions (Before Implementation)

1. **Search Strategy**
   - How many results to return by default?
   - Should we use similarity threshold?
   - How to handle very similar results?

2. **Hybrid Search**
   - Filter before or after semantic search?
   - How to handle date filtering in ChromaDB?
   - Should we support complex filter combinations?

3. **Result Formatting**
   - How much detail to include?
   - Should we show similarity scores?
   - How to handle large result sets?

4. **Performance**
   - How to optimize query speed?
   - Should we cache frequent queries?
   - How to handle large databases?

## Example User Interactions

**User**: "What videos did I watch about machine learning?"
- **Tool Called**: `search_videos_by_topic(query="machine learning")`
- **Response**: "I found 15 videos about machine learning in your history. Here are some highlights:
  1. Introduction to Neural Networks - Tech Educator (watched 2 weeks ago)
  2. Deep Learning Tutorial - Data Science Channel (watched 1 month ago)..."

**User**: "Find me Python tutorials from last month"
- **Tool Called**: `search_videos_by_topic(query="Python tutorials", date_from="2024-12-01", date_to="2024-12-31")`
- **Response**: "I found 8 Python tutorials from December:
  1. Python Basics - Programming Channel (watched Dec 5)
  2. Advanced Python - Tech Educator (watched Dec 12)..."

**User**: "What videos are similar to [video_id]?"
- **Tool Called**: `find_similar_videos(video_id="...")`
- **Response**: "Here are 5 videos similar to 'Python Tutorial':
  1. Python Advanced Topics - Same channel
  2. Python for Data Science - Different channel..."

## Next Steps

After Phase 2 completion:
1. Review validation criteria
2. Verify all deliverables are complete
3. Test semantic search quality
4. Document any issues or decisions
5. Proceed to Phase 3: Service 3 - Function Calling Service

## Notes

- Semantic search quality is critical - test with various queries
- Ensure embedding model matches Phase 0
- Consider query expansion for better results
- Document limitations (e.g., can't search transcripts if not embedded)

---

**Phase Status**: Planning  
**Dependencies**: Phase 0 (Infrastructure), Phase 1 (API Service)  
**Estimated Effort**: Medium-High

