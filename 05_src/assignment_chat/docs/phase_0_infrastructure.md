# Phase 0: Project Infrastructure / Data Preparation

## Phase Overview

This phase establishes the foundation for the entire project by setting up the project structure, creating the data pipeline for embeddings, and populating ChromaDB with YouTube history data.

## Objectives

1. Create complete project directory structure
2. Set up configuration management system
3. Extract YouTube history data from API
4. Generate embeddings for semantic search fields
5. Load embeddings into ChromaDB with file persistence
6. Document the embedding process

## Requirements

### Functional Requirements

1. **Project Structure**
   - Create all necessary directories and files
   - Set up Python package structure with `__init__.py` files
   - Organize code into logical modules (services, core, utils, data)

2. **Configuration Management**
   - Environment variable management (API URLs, keys)
   - Configuration file for non-sensitive settings
   - Support for different environments (development, production)

3. **Data Extraction**
   - Connect to YouTube History API
   - Extract video data including:
     - Video IDs, titles, descriptions
     - Channel IDs and names
     - Watch timestamps
     - Video metadata (duration, tags, etc.)
   - Handle pagination for large datasets
   - Store extracted data in a format suitable for embedding generation

4. **Embedding Generation**
   - Generate embeddings for searchable fields:
     - Video titles
     - Video descriptions (if available)
     - Channel names
     - Video transcripts (if available)
   - Use OpenAI `text-embedding-3-small` model
   - Batch process embeddings efficiently
   - Store embeddings with associated metadata

5. **ChromaDB Setup**
   - Initialize ChromaDB with file persistence
   - Create collection with OpenAI embedding function
   - Load embeddings with metadata
   - Ensure data size stays under 40MB limit

6. **Documentation**
   - Document embedding generation process
   - Explain data preparation steps
   - Document any assumptions or limitations

### Technical Requirements

- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **ChromaDB**: PersistentClient with local file storage
- **Data Format**: Store video_id, channel_id, watched_at, and other metadata
- **Size Limit**: Total embeddings + metadata must be under 40MB
- **Error Handling**: Graceful handling of API failures, missing data

## Implementation Specifications

### Directory Structure

```
05_src/assignment_chat/
├── docs/
├── src/
│   ├── services/
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── data/
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── generate_embeddings.py
│   │   └── chroma_db/          # ChromaDB will create files here
│   └── utils/
│       ├── __init__.py
│       └── api_client.py
├── tests/
│   └── test_data_preparation.py
├── .env.example
└── README.md
```

### Configuration Setup

**File**: `.env` or `.secrets` (use existing pattern from course)
```python
# YouTube History API
YOUTUBE_API_BASE_URL=http://localhost:8000
YOUTUBE_API_VERSION=v1

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o  # or gpt-4
EMBEDDING_MODEL=text-embedding-3-small

# ChromaDB
CHROMA_DB_PATH=./src/data/chroma_db
CHROMA_COLLECTION_NAME=youtube_history
```

### Data Extraction Process

**File**: `src/utils/api_client.py`

```python
class YouTubeHistoryAPIClient:
    """Client for YouTube History API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def get_all_videos(self, limit: int = 500, offset: int = 0):
        """Fetch all videos with pagination"""
        
    def get_video_details(self, video_id: str):
        """Get detailed video information"""
        
    def get_statistics(self):
        """Get overall statistics"""
```

**Process**:
1. Call `/api/v1/stats` to get total video count
2. Paginate through `/api/v1/videos` to get all videos
3. Optionally fetch detailed information for each video
4. Store data in structured format (list of dicts or DataFrame)

### Embedding Generation

**File**: `src/data/embeddings/generate_embeddings.py`

**Process**:
1. Load extracted video data
2. Prepare text fields for embedding:
   - Combine title + description (if available)
   - Include channel name as context
   - Handle missing fields gracefully
3. Batch generate embeddings using OpenAI API
4. Store embeddings with metadata:
   - `video_id`: Unique identifier
   - `channel_id`: Channel identifier
   - `watched_at`: Timestamp
   - `text`: Original text that was embedded
   - `embedding`: Vector embedding

**Key Considerations**:
- Batch size: Process in batches of 100-1000 to optimize API calls
- Rate limiting: Handle API rate limits
- Error handling: Retry failed embeddings
- Size monitoring: Track total data size

### ChromaDB Setup

**File**: `src/data/embeddings/generate_embeddings.py`

```python
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Initialize ChromaDB with file persistence
client = PersistentClient(path="./src/data/chroma_db")

# Create collection with OpenAI embedding function
collection = client.create_collection(
    name="youtube_history",
    embedding_function=OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
)

# Add documents with metadata
collection.add(
    documents=[video["text"] for video in videos],
    ids=[video["video_id"] for video in videos],
    metadatas=[
        {
            "channel_id": video["channel_id"],
            "channel_name": video["channel_name"],
            "watched_at": video["watched_at"],
            "title": video["title"]
        }
        for video in videos
    ]
)
```

### Data Size Management

**Strategies to stay under 40MB**:
1. Monitor embedding size: 1536 dimensions × 4 bytes = ~6KB per embedding
2. Limit number of videos if needed (e.g., most recent 5000-10000 videos)
3. Optimize metadata storage (remove unnecessary fields)
4. Use compression if available in ChromaDB

## Validation Criteria

### Phase Completion Checklist

- [ ] Project directory structure created
- [ ] Configuration system set up and tested
- [ ] API client successfully connects to YouTube History API
- [ ] Video data extracted and stored
- [ ] Embeddings generated for all videos
- [ ] ChromaDB collection created and populated
- [ ] Data size verified to be under 40MB
- [ ] Embedding process documented in README
- [ ] Test queries return expected results from ChromaDB
- [ ] Error handling tested (API failures, missing data)

### Test Cases

1. **API Connection Test**
   - Verify connection to YouTube History API
   - Test pagination works correctly
   - Handle API errors gracefully

2. **Embedding Generation Test**
   - Generate embeddings for sample videos
   - Verify embedding dimensions (1536)
   - Test batch processing

3. **ChromaDB Test**
   - Create collection successfully
   - Add embeddings with metadata
   - Query collection and verify results
   - Test persistence (restart and verify data still exists)

4. **Data Size Test**
   - Calculate total size of embeddings + metadata
   - Verify under 40MB limit
   - If over limit, implement reduction strategy

## Deliverables

1. **Code**
   - `src/utils/api_client.py`: API client implementation
   - `src/data/embeddings/generate_embeddings.py`: Embedding generation script
   - Configuration files (`.env.example`)

2. **Data**
   - ChromaDB database populated with embeddings
   - Documentation of data structure

3. **Documentation**
   - README section on embedding process
   - Data preparation notes
   - Any assumptions or limitations

4. **Tests**
   - Unit tests for API client
   - Integration tests for embedding generation
   - Tests for ChromaDB operations

## Planning Questions (Before Implementation)

1. **Data Scope**
   - How many videos should we include? (All vs. recent subset)
   - Should we include transcripts if available?
   - What date range should we cover?

2. **Embedding Strategy**
   - Combine title + description, or embed separately?
   - Include channel name in embedding or as metadata only?
   - How to handle videos with missing descriptions?

3. **Performance**
   - What batch size for embedding generation?
   - How to handle rate limiting?
   - Should we cache intermediate results?

4. **Storage**
   - Exact path for ChromaDB storage?
   - Should we version the database?
   - Backup strategy?

## Next Steps

After Phase 0 completion:
1. Review validation criteria
2. Verify all deliverables are complete
3. Document any issues or decisions
4. Proceed to Phase 1: Service 1 - API Calls Integration

## Notes

- The embedding generation script should be runnable independently
- Consider creating a script to verify ChromaDB contents
- Document any manual steps required (e.g., starting API server)
- Include example queries to test ChromaDB setup

---

**Phase Status**: Planning  
**Dependencies**: None  
**Estimated Effort**: Medium

