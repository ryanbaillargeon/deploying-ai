# Assignment Chat - YouTube History Chat Application

This project provides a chat interface for querying YouTube watch history using semantic search powered by embeddings and ChromaDB.

## Phase 0: Infrastructure / Data Preparation

Phase 0 establishes the foundation by setting up the project structure, creating the data pipeline for embeddings, and populating ChromaDB with YouTube history data.

## Phase 1: Service 1 - API Calls Integration

Phase 1 implements a chat interface that calls the YouTube History API and transforms structured JSON responses into natural, conversational language summaries. The service uses LangChain for LLM integration and supports both local models (via LM Studio) and online models (OpenAI).

## Project Structure

```
05_src/assignment_chat/
├── docs/                          # Project documentation
├── src/
│   ├── services/                  # Service layer
│   │   └── api_service.py        # API service with transformations
│   ├── core/                      # Core functionality
│   │   ├── model_factory.py      # Model initialization with switching
│   │   └── chat_engine.py        # LangChain-based chat engine
│   ├── data/
│   │   ├── embeddings/
│   │   │   └── generate_embeddings.py  # Embedding generation script
│   │   └── chroma_db/            # ChromaDB persistent storage
│   ├── utils/
│   │   └── api_client.py         # YouTube History API client
│   └── app.py                    # Gradio chat interface
├── tests/
│   ├── test_data_preparation.py  # Phase 0 tests
│   ├── test_model_factory.py     # Model factory tests
│   ├── test_api_service.py      # API service tests
│   ├── test_chat_engine.py       # Chat engine tests
│   └── test_integration.py      # Integration tests
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

## Setup

### Prerequisites

- Python 3.8+
- YouTube History API running (default: http://localhost:8000)
- OpenAI API key (for online models) OR LM Studio running (for local models)
- LangChain and Gradio installed (see Installation)

### Installation

1. Install dependencies:
```bash
pip install chromadb openai requests python-dotenv langchain langchain-openai gradio
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Or create a `.secrets` file (following course pattern):
```bash
OPENAI_API_KEY=your_key_here
```

### Configuration

The `.env.example` file contains the following configuration options:

```bash
# YouTube History API
YOUTUBE_API_BASE_URL=http://localhost:8000
YOUTUBE_API_VERSION=v1

# Model Configuration
USE_LOCAL_LLM=false  # Set to 'true' to use LM Studio
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o

# Local Model (LM Studio) Configuration
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LOCAL_MODEL_NAME=local-model  # Model name in LM Studio

# Embeddings (for future phases)
EMBEDDING_MODEL=text-embedding-3-small

# ChromaDB
CHROMA_DB_PATH=./src/data/chroma_db
CHROMA_COLLECTION_NAME=youtube_history
```

### Model Switching

The application supports switching between local models (via LM Studio) and online models (OpenAI):

**Using Online Models (OpenAI):**
1. Set `USE_LOCAL_LLM=false` in your `.env` file
2. Set `OPENAI_API_KEY` with your API key
3. Optionally set `OPENAI_MODEL` (default: `gpt-4o`)

**Using Local Models (LM Studio):**
1. Install and start LM Studio
2. Load your model (e.g., OSS-120B)
3. Start the local server (default: `http://127.0.0.1:1234/v1`)
4. Set `USE_LOCAL_LLM=true` in your `.env` file
5. Optionally set `LM_STUDIO_BASE_URL` and `LOCAL_MODEL_NAME`

The model switching is transparent - the rest of the application works the same way regardless of which model you use.

## Usage

### Running the Chat Interface

Start the Gradio chat interface:

```bash
python src/app.py
```

The interface will launch in your browser. You can ask questions about your YouTube watch history, such as:

- "What videos did I watch recently?"
- "Tell me about my watch history statistics"
- "What can you tell me about the Tech Educator channel?"
- "Get details about video [video_id]"

The chat engine will automatically use the appropriate tools to fetch information from the YouTube History API and provide natural language responses.

### Generating Embeddings

Run the embedding generation script to fetch videos from the YouTube History API, generate embeddings, and store them in ChromaDB:

```bash
# Basic usage (processes all videos)
python src/data/embeddings/generate_embeddings.py

# Include transcripts in embeddings (slower, requires additional API calls)
python src/data/embeddings/generate_embeddings.py --include-transcripts

# Limit number of videos processed
python src/data/embeddings/generate_embeddings.py --max-videos 1000

# Custom batch size for embedding generation
python src/data/embeddings/generate_embeddings.py --batch-size 50

# Custom ChromaDB path and collection name
python src/data/embeddings/generate_embeddings.py \
    --chroma-db-path ./custom/path \
    --collection-name custom_collection
```

### Command-Line Options

- `--batch-size`: Batch size for embedding generation (default: 100)
- `--include-transcripts`: Include video transcripts in embeddings (default: False)
- `--max-videos`: Maximum number of videos to process (default: all)
- `--limit-per-page`: Number of videos per API page (default: 500)
- `--chroma-db-path`: Path to ChromaDB storage (default: from .env)
- `--collection-name`: ChromaDB collection name (default: from .env)

### Example Workflow

1. **Start YouTube History API** (if not already running):
   ```bash
   # Assuming API is running on localhost:8000
   ```

2. **Generate embeddings without transcripts** (faster):
   ```bash
   python src/data/embeddings/generate_embeddings.py
   ```

3. **Generate embeddings with transcripts** (more comprehensive, slower):
   ```bash
   python src/data/embeddings/generate_embeddings.py --include-transcripts
   ```

4. **Verify ChromaDB contents**:
   The ChromaDB database will be created at `./src/data/chroma_db/` (or your configured path).

## Embedding Process

### Text Preparation

For each video, the script prepares text for embedding by combining:

1. **Title**: Video title
2. **Channel Name**: Channel name as context
3. **Description**: Video description (if available)
4. **Transcript**: Video transcript (if `--include-transcripts` flag is used and transcript is available)

The text is formatted as:
```
Title: [Video Title]

Channel: [Channel Name]

Description: [Video Description]

Transcript: [Transcript Text]
```

### Embedding Generation

- **Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Batch Processing**: Videos are processed in batches (default: 100) to optimize API calls
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Failed batches are logged and skipped, allowing processing to continue

### ChromaDB Storage

Each video is stored in ChromaDB with:

- **Document**: Combined text (title + description + transcript)
- **ID**: Video ID (YouTube video ID)
- **Metadata**:
  - `video_id`: YouTube video ID
  - `channel_id`: Channel ID
  - `channel_name`: Channel name
  - `watched_at`: Watch timestamp
  - `title`: Video title
  - `has_transcript`: Whether transcript was included (true/false)

### Data Size Management

The script estimates data size and warns if it exceeds 40MB:

- **Embedding size**: ~6KB per video (1536 dimensions × 4 bytes)
- **Metadata**: ~500 bytes per video
- **Text**: Variable based on description/transcript length

If estimated size exceeds 40MB, the script will prompt before continuing.

## API Service

The `APIService` provides natural language transformations of YouTube History API data. It's integrated as LangChain tools that the chat engine can use:

```python
from src.services.api_service import APIService

service = APIService()

# Get natural language summary of recent videos
summary = service.get_recent_videos_summary(limit=10)

# Get video summary
video_summary = service.get_video_summary('video_id')

# Get statistics summary
stats_summary = service.get_statistics_summary()

# Get channel summary
channel_summary = service.get_channel_summary(channel_name='Tech Educator')
```

### API Tools

The following LangChain tools are available:

- `get_recent_videos`: Get summary of recently watched videos
- `get_video_details`: Get detailed information about a specific video
- `get_statistics`: Get overall watch history statistics
- `get_channel_info`: Get information about a specific channel

## API Client

The `YouTubeHistoryAPIClient` provides methods for interacting with the YouTube History API:

```python
from src.utils.api_client import YouTubeHistoryAPIClient

client = YouTubeHistoryAPIClient()

# Get statistics
stats = client.get_statistics()

# Get all videos (with pagination)
videos = client.get_all_videos_paginated(limit=500, max_videos=1000)

# Get video details
details = client.get_video_details('video_id')

# Get video transcript
transcript = client.get_video_transcript('video_id', language='en')

# Get channels
channels = client.get_channels(limit=50)

# Get channel details
channel = client.get_channel('channel_id')

# Search channel by name
channel = client.search_channels_by_name('Channel Name')
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test files
python -m unittest tests.test_model_factory -v
python -m unittest tests.test_api_service -v
python -m unittest tests.test_chat_engine -v
python -m unittest tests.test_integration -v
python -m unittest tests.test_data_preparation -v
```

Or using pytest:

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### API Connection Issues

If you encounter connection errors:

1. Verify the YouTube History API is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check your `YOUTUBE_API_BASE_URL` in `.env` or `.secrets`

### OpenAI API Issues

If embedding generation fails:

1. Verify your API key is set correctly:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. Check API rate limits and quota

3. Review logs in `./logs/` directory

### ChromaDB Issues

If ChromaDB operations fail:

1. Ensure write permissions for the ChromaDB path
2. Check disk space availability
3. Verify the collection name doesn't conflict with existing collections

### Transcript Issues

If transcripts are not being fetched:

1. Not all videos have transcripts available
2. The API returns 404 for videos without transcripts (this is handled gracefully)
3. Use `--include-transcripts` flag to attempt transcript fetching

## Data Structure

### Video Data Format

Videos fetched from the API include:

```python
{
    'video_id': 'dQw4w9WgXcQ',
    'title': 'Video Title',
    'channel_id': 'UC1234567890',
    'channel_name': 'Channel Name',
    'watched_at': '2025-11-02T14:30:00Z',
    'duration_seconds': 3600,
    'description': 'Video description...',  # May be None
    # ... other fields
}
```

### ChromaDB Collection

The ChromaDB collection stores:

- **Documents**: Combined text for semantic search
- **IDs**: Video IDs for retrieval
- **Embeddings**: 1536-dimensional vectors (generated automatically by ChromaDB)
- **Metadata**: Video metadata for filtering and display

## Example Usage

### Chat Interface Examples

**Getting Recent Videos:**
```
User: "What videos did I watch recently?"
Assistant: "You've watched 10 videos recently. Here are some highlights:
1. Python Tutorial from Tech Educator (1:00:00) - watched 2 days ago
2. Machine Learning Basics from Data Science (45:30) - watched 3 days ago
..."
```

**Getting Statistics:**
```
User: "Tell me about my watch history statistics"
Assistant: "Your YouTube history is quite extensive! You've watched 1,250 videos 
across 150 different channels. Your total watch time is approximately 2,500 hours 
with an average video duration of 1 hour and 12 minutes..."
```

**Channel Information:**
```
User: "What can you tell me about the Tech Educator channel?"
Assistant: "Tech Educator is a channel focused on educational technology content. 
You've watched 50 videos from this channel, which has 100.0 thousand subscribers."
```

## Next Steps

After completing Phase 1:

1. Verify the chat interface works correctly
2. Test tool calling with both local and online models
3. Verify natural language transformations are working
4. Proceed to Phase 2: Service 2 - Semantic Query Service

## Notes

- The embedding generation script should be runnable independently
- ChromaDB data persists between runs (stored in `./src/data/chroma_db/`)
- If you need to regenerate embeddings, you may want to delete the ChromaDB directory first
- Transcript fetching significantly increases processing time but improves search quality

## License

See LICENSE file in project root.

