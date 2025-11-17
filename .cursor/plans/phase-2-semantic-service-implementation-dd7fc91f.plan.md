<!-- dd7fc91f-1de3-4a28-9923-e74f1bbf7648 a516ade7-5ee3-499e-8c94-95f427465e60 -->
# Phase 2: Semantic Query Service Implementation

## Overview

Implement semantic search service that enables users to find videos by meaning, topics, and concepts using ChromaDB vector similarity search. The service will integrate with the existing chat engine as LangChain tools, following the same observability patterns as the API service.

## Implementation Tasks

### 1. Create Semantic Service (`src/services/semantic_service.py`)

**Core Service Class:**

- `SemanticService` class that wraps ChromaDB operations
- Initialize with `PersistentClient` using `CHROMA_DB_PATH` from env
- Get existing collection using `CHROMA_COLLECTION_NAME` from env
- Use `OpenAIEmbeddingFunction` with `text-embedding-3-small` model (matching Phase 0)

**Key Methods:**

- `search_by_topic(query, n_results, filters)` - Main semantic search method
- `hybrid_search(query, n_results, **filters)` - Combine semantic + metadata filtering
- `find_similar_videos(video_id, n_results)` - Find videos similar to a given video
- `format_results(results)` - Format ChromaDB results as natural language strings

**ChromaDB Query Pattern:**

- Use `collection.query(query_texts=[query], n_results=n_results, where=where_clause)`
- Collection already has embedding function, so queries can use text directly
- Apply metadata filters using `where` clause (channel_id, date ranges if supported)
- Post-filter results for date ranges if ChromaDB doesn't support them natively

**Result Formatting:**

- Return natural language strings (matching API service pattern)
- Include: video title, channel name, watched_at timestamp, relevance score
- Handle empty results gracefully

### 2. Create LangChain Tools (`src/services/semantic_service.py`)

**Tool Definitions:**

- `search_videos_by_topic` - Main semantic search tool with optional filters
- Parameters: `query` (required), `n_results` (default: 10), `date_from`, `date_to`, `channel_id`
- Description: Clear docstring explaining when to use this tool
- `find_similar_videos` - Find similar videos tool
- Parameters: `video_id` (required), `n_results` (default: 5)
- Description: Use when user asks for similar videos or recommendations

**Tool Functions:**

- Use `@tool` decorator from LangChain
- Call `SemanticService` methods and return formatted strings
- Handle errors gracefully with user-friendly messages

**Export Function:**

- `get_semantic_tools()` - Returns list of semantic tools for chat engine

### 3. Integrate with Chat Engine (`src/core/chat_engine.py`)

**Tool Registration:**

- Import `get_semantic_tools` from semantic_service
- Combine with existing `get_api_tools()` in `ChatEngine.__init__()`
- Update `self.tools` to include both API and semantic tools
- Rebind tools to model: `self.model_with_tools = self.model.bind_tools(self.tools)`

**Observability:**

- Tool calls/results logging already handled by `_handle_tool_calls()` method
- No changes needed - semantic tools will automatically be logged via existing infrastructure

### 4. Add Internal Logging (`src/services/semantic_service.py`)

**Logging Points:**

- Log query text and parameters when search starts
- Log ChromaDB query performance (latency)
- Log result counts and relevance scores
- Log errors with context

**Use Standard Logger:**

- Import `get_logger` from `utils.logger` (same pattern as API service)
- Log at appropriate levels (INFO for queries, ERROR for failures)

### 5. Update System Prompts (`src/core/prompts.py`)

**Tool Descriptions:**

- System prompt already dynamically includes tool descriptions via `get_tools_description()`
- Ensure semantic tool docstrings are clear and descriptive
- No code changes needed if tool docstrings are well-written

### 6. Testing

**Unit Tests (`tests/test_semantic_service.py`):**

- Test `SemanticService` initialization
- Test `search_by_topic` with various queries
- Test `hybrid_search` with metadata filters
- Test `find_similar_videos` with valid video IDs
- Test result formatting
- Test error handling (empty results, invalid video IDs, ChromaDB errors)

**Integration Tests:**

- Test semantic tools through chat engine
- Test tool calling from LLM
- Test end-to-end flow: user query → tool call → formatted response

**Test Queries:**

- Topic-based: "videos about machine learning"
- Opinion-based: "videos discussing AI ethics"
- Technology-based: "React tutorials"
- Hybrid: "Python videos from last month"
- Similar videos: "videos similar to [video_id]"

### 7. Documentation Updates

**README.md:**

- Add Phase 2 section describing semantic search capabilities
- Document semantic tool usage
- Add example queries and responses

**TOOL_CALLS.md:**

- Add semantic tools documentation
- Document when to use each semantic tool
- Add example interactions

## Key Design Decisions

1. **Observability**: Semantic tools inherit observability from chat engine's `_handle_tool_calls()` - no additional logging needed in tool functions themselves
2. **Error Handling**: Return user-friendly error messages, log detailed errors internally
3. **Result Format**: Return natural language strings (not structured data) to match API service pattern
4. **ChromaDB Integration**: Use existing collection with embedding function - queries use text directly
5. **Metadata Filtering**: Use ChromaDB `where` clause when possible, post-filter for complex date ranges

## Files to Create/Modify

**New Files:**

- `src/services/semantic_service.py` - Semantic service implementation

**Modified Files:**

- `src/core/chat_engine.py` - Add semantic tools to tool list
- `tests/test_semantic_service.py` - Unit tests (new)
- `README.md` - Add Phase 2 documentation
- `docs/TOOL_CALLS.md` - Add semantic tools documentation

## Validation Criteria

- [ ] Semantic service implemented and tested
- [ ] ChromaDB queries return relevant results (>80% relevance)
- [ ] Hybrid search combines semantic + metadata filters correctly
- [ ] LangChain tools defined and callable
- [ ] Tools integrated with chat engine
- [ ] Observability logging works (tool calls/results logged automatically)
- [ ] Error handling graceful
- [ ] Test suite passes
- [ ] Documentation updated

## Dependencies

- Phase 0: ChromaDB collection must exist with embeddings
- Phase 1: Chat engine infrastructure for tool integration
- Environment variables: `CHROMA_DB_PATH`, `CHROMA_COLLECTION_NAME`, `OPENAI_API_KEY`

### To-dos

- [ ] Create src/services/semantic_service.py with SemanticService class, search methods, and result formatting
- [ ] Define LangChain tools (@tool decorator) for search_videos_by_topic and find_similar_videos in semantic_service.py
- [ ] Update chat_engine.py to import and include semantic tools alongside API tools
- [ ] Add logging to semantic_service.py for queries, performance, and errors using get_logger
- [ ] Create tests/test_semantic_service.py with comprehensive unit tests for all service methods
- [ ] Add integration tests for semantic tools through chat engine
- [ ] Update README.md and docs/TOOL_CALLS.md with semantic service documentation and examples