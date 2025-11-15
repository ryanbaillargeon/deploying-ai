# YouTube History API Reference

## Overview

The YouTube History API is a read-only REST API that provides access to YouTube watch history data imported from Google Takeout exports. The API allows you to search, browse, and retrieve statistics about your YouTube viewing history.

**API Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Protocol:** HTTP/HTTPS  
**Format:** JSON

### Key Features

- Full-text search across video titles and metadata
- Pagination support for large result sets
- Filtering by channel, date range, duration, and more
- Statistics and analytics endpoints
- Collection management for organizing videos
- Video transcript retrieval

### Interactive Documentation

The API includes interactive Swagger documentation available at `/docs` and ReDoc documentation at `/redoc` when the server is running.

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible. This is suitable for local network deployments or when the API is protected by network-level security.

---

## Base URL Structure

All API endpoints are prefixed with `/api/v1`. The full URL structure is:

```
http://localhost:8000/api/v1/{endpoint}
```

Example:
```
GET http://localhost:8000/api/v1/videos
```

---

## Common Response Formats

### Success Response

All successful responses return HTTP status `200 OK` (or `201 Created` for POST endpoints) with JSON body containing the requested data.

### Pagination Response

Endpoints that support pagination return responses in the following format:

```json
{
  "results": [...],
  "total_count": 1000,
  "query": "search query",
  "limit": 50,
  "offset": 0,
  "has_more": true,
  "execution_time_ms": 12.5
}
```

**Fields:**
- `results`: Array of result objects
- `total_count`: Total number of matching items
- `query`: The search query used (may be empty for list endpoints)
- `limit`: Maximum number of results per page
- `offset`: Number of results skipped
- `has_more`: Boolean indicating if more results are available
- `execution_time_ms`: Query execution time in milliseconds

### Pagination Usage

To paginate through results:

1. Start with `offset=0` and your desired `limit`
2. Check `has_more` to determine if more results exist
3. For the next page, set `offset` to `offset + limit`
4. Repeat until `has_more` is `false`

Example:
```bash
# First page
GET /api/v1/videos?limit=50&offset=0

# Second page
GET /api/v1/videos?limit=50&offset=50

# Third page
GET /api/v1/videos?limit=50&offset=100
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_type": "ErrorType"
}
```

### HTTP Status Codes

| Status Code | Description |
|------------|-------------|
| `200 OK` | Request successful |
| `400 Bad Request` | Invalid request parameters |
| `404 Not Found` | Resource not found |
| `422 Unprocessable Entity` | Validation error (e.g., invalid date format) |
| `500 Internal Server Error` | Server error |

### Error Types

- **DatabaseError**: Database connection or query error
- **SearchError**: Search query or filter error
- **ValidationError**: Request parameter validation error

### Example Error Responses

**404 Not Found:**
```json
{
  "detail": "Video dQw4w9WgXcQ not found",
  "error_type": null
}
```

**422 Validation Error:**
```json
{
  "detail": "Invalid date_from format: 2024-13-45. Use ISO format (YYYY-MM-DD)",
  "error_type": "ValidationError"
}
```

**500 Server Error:**
```json
{
  "detail": "Database connection failed: Failed to open database at /data/youtube_history.db: [Errno 2] No such file or directory",
  "error_type": "DatabaseError"
}
```

---

## Date and Time Formats

All datetime fields use **ISO 8601** format with timezone information:

- Format: `YYYY-MM-DDTHH:MM:SS+00:00` or `YYYY-MM-DDTHH:MM:SSZ`
- Examples:
  - `2025-11-02T14:30:00Z`
  - `2025-11-02T14:30:00+00:00`
  - `2025-11-02T14:30:00-05:00`

For date-only filters (like `date_from` and `date_to` in search), use `YYYY-MM-DD` format:
- Example: `2025-11-02`

---

## Endpoints

### Root & Health

#### GET `/`

Get API information and metadata.

**Response:** `200 OK`

```json
{
  "name": "YouTube History API",
  "version": "1.0.0",
  "description": "Read-only REST API for YouTube watch history data",
  "docs": "/docs",
  "health": "/health"
}
```

---

#### GET `/health`

Health check endpoint to verify API and database connectivity.

**Response:** `200 OK`

**Response Model:** `HealthResponse`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database_connected": true
}
```

**Status Values:**
- `healthy`: API and database are operational
- `degraded`: API is running but database is unavailable

---

### Videos

#### GET `/api/v1/videos`

Get a paginated list of videos from watch history, ordered by most recently watched.

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `channel_id` | string | No | `null` | - | Filter videos by channel ID |
| `limit` | integer | No | `50` | `1-500` | Maximum number of results |
| `offset` | integer | No | `0` | `>= 0` | Number of results to skip |
| `sort` | string | No | `recent` | `recent` or `oldest` | Sort order (currently both use recent) |

**Response:** `200 OK`

**Response Model:** `SearchResponse`

**Example Request:**
```bash
GET /api/v1/videos?limit=20&offset=0&sort=recent
```

**Example Response:**
```json
{
  "results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Python Tutorial: Machine Learning Basics",
      "channel_id": "UC1234567890",
      "channel_name": "Tech Educator",
      "watched_at": "2025-11-02T14:30:00Z",
      "duration_seconds": 3600,
      "duration_formatted": "1:00:00",
      "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
      "is_deleted": false,
      "relevance_score": null,
      "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  ],
  "total_count": 1250,
  "query": "",
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "execution_time_ms": 5.2
}
```

---

#### GET `/api/v1/videos/{video_id}`

Get detailed metadata for a specific video by its YouTube video ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID (11 characters) |

**Response:** `200 OK`

**Response Model:** `VideoResponse`

**Example Request:**
```bash
GET /api/v1/videos/dQw4w9WgXcQ
```

**Example Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Python Tutorial: Machine Learning Basics",
  "channel_id": "UC1234567890",
  "channel_name": "Tech Educator",
  "description": "Learn the basics of machine learning with Python...",
  "duration_seconds": 3600,
  "duration_formatted": "1:00:00",
  "published_at": "2024-01-15T10:00:00Z",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
  "is_deleted": false,
  "deleted_at": null,
  "view_count": 50000,
  "like_count": 1200,
  "comment_count": 150,
  "category_id": "27",
  "tags": "python,machine learning,tutorial",
  "has_captions": true,
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "created_at": "2025-11-02T14:30:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Video with the specified ID does not exist

---

### Channels

#### GET `/api/v1/channels`

Get a paginated list of all channels, ordered alphabetically by name.

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `limit` | integer | No | `50` | `1-500` | Maximum number of results |
| `offset` | integer | No | `0` | `>= 0` | Number of results to skip |

**Response:** `200 OK`

**Response Model:** `List[ChannelResponse]`

**Example Request:**
```bash
GET /api/v1/channels?limit=25&offset=0
```

**Example Response:**
```json
[
  {
    "channel_id": "UC1234567890",
    "name": "Tech Educator",
    "description": "Educational technology content",
    "subscriber_count": 100000,
    "video_count": 500,
    "view_count": 5000000,
    "channel_url": "https://www.youtube.com/channel/UC1234567890",
    "created_at": "2025-11-02T14:30:00Z",
    "updated_at": "2025-11-02T14:30:00Z"
  }
]
```

---

#### GET `/api/v1/channels/{channel_id}`

Get detailed information for a specific channel by its channel ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID |

**Response:** `200 OK`

**Response Model:** `ChannelResponse`

**Example Request:**
```bash
GET /api/v1/channels/UC1234567890
```

**Example Response:**
```json
{
  "channel_id": "UC1234567890",
  "name": "Tech Educator",
  "description": "Educational technology content",
  "subscriber_count": 100000,
  "video_count": 500,
  "view_count": 5000000,
  "channel_url": "https://www.youtube.com/channel/UC1234567890",
  "created_at": "2025-11-02T14:30:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Channel with the specified ID does not exist

---

### Search

#### GET `/api/v1/search`

Search videos by keyword with advanced filtering options. Supports full-text search using SQLite FTS5 syntax.

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `q` | string | Yes | - | - | Search query string (required) |
| `channel` | string | No | `null` | - | Filter by channel name (exact match) |
| `channel_id` | string | No | `null` | - | Filter by channel ID |
| `date_from` | string | No | `null` | `YYYY-MM-DD` | Start date (ISO format) |
| `date_to` | string | No | `null` | `YYYY-MM-DD` | End date (ISO format) |
| `min_duration` | integer | No | `null` | `>= 0` | Minimum duration in seconds |
| `max_duration` | integer | No | `null` | `>= 0` | Maximum duration in seconds |
| `include_deleted` | boolean | No | `false` | - | Include deleted videos in results |
| `limit` | integer | No | `50` | `1-500` | Maximum number of results |
| `offset` | integer | No | `0` | `>= 0` | Number of results to skip |

**Response:** `200 OK`

**Response Model:** `SearchResponse`

**Example Request:**
```bash
GET /api/v1/search?q=python+tutorial&channel_id=UC1234567890&date_from=2025-01-01&min_duration=300&limit=20
```

**Example Response:**
```json
{
  "results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Python Tutorial: Machine Learning Basics",
      "channel_id": "UC1234567890",
      "channel_name": "Tech Educator",
      "watched_at": "2025-11-02T14:30:00Z",
      "duration_seconds": 3600,
      "duration_formatted": "1:00:00",
      "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
      "is_deleted": false,
      "relevance_score": 0.95,
      "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  ],
  "total_count": 15,
  "query": "python tutorial",
  "limit": 20,
  "offset": 0,
  "has_more": false,
  "execution_time_ms": 8.3
}
```

**Search Query Syntax:**

The search query (`q` parameter) supports SQLite FTS5 syntax:

- **Simple terms**: `python tutorial`
- **Phrase search**: `"machine learning"`
- **Boolean operators**: `python AND tutorial`, `python OR javascript`
- **Exclusion**: `python -javascript` (videos with "python" but not "javascript")
- **Prefix matching**: `pyth*` (matches "python", "pythonic", etc.)

**Error Responses:**
- `422 Unprocessable Entity`: Invalid date format or other validation error

**Example Error:**
```json
{
  "detail": "Invalid date_from format: 2024-13-45. Use ISO format (YYYY-MM-DD)"
}
```

---

### Statistics

#### GET `/api/v1/stats`

Get comprehensive statistics about the watch history database.

**Response:** `200 OK`

**Response Model:** `WatchStatisticsResponse`

**Example Request:**
```bash
GET /api/v1/stats
```

**Example Response:**
```json
{
  "total_videos": 1250,
  "total_channels": 150,
  "total_watch_events": 5000,
  "oldest_watch": "2020-01-15T08:00:00Z",
  "newest_watch": "2025-11-02T14:30:00Z",
  "videos_with_duration": 1000,
  "videos_needing_enrichment": 250,
  "videos_with_transcripts": 500,
  "total_watch_time_hours": 2500.5,
  "average_video_duration_seconds": 1800.0,
  "total_collections": 10,
  "top_channels": [
    {
      "channel_id": "UC1234567890",
      "channel_name": "Tech Educator",
      "video_count": 50,
      "total_watch_events": 200,
      "first_watched": "2020-01-15T08:00:00Z",
      "last_watched": "2025-11-02T14:30:00Z"
    }
  ],
  "collections_info": [
    {
      "name": "Python Tutorials",
      "video_count": 25,
      "total_hours": 50.5,
      "top_keywords": ["python", "tutorial", "programming"]
    }
  ]
}
```

---

#### GET `/api/v1/stats/channels`

Get top channels ranked by number of videos watched.

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `limit` | integer | No | `20` | `1-100` | Maximum number of channels |

**Response:** `200 OK`

**Response Model:** `List[ChannelStatsResponse]`

**Example Request:**
```bash
GET /api/v1/stats/channels?limit=10
```

**Example Response:**
```json
[
  {
    "channel_id": "UC1234567890",
    "channel_name": "Tech Educator",
    "video_count": 50,
    "total_watch_events": 200,
    "first_watched": "2020-01-15T08:00:00Z",
    "last_watched": "2025-11-02T14:30:00Z"
  }
]
```

---

### Collections

#### GET `/api/v1/collections`

Get a list of all video collections.

**Response:** `200 OK`

**Response Model:** `List[CollectionResponse]`

**Example Request:**
```bash
GET /api/v1/collections
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Python Tutorials",
    "description": "Collection of Python programming tutorials",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-11-02T14:30:00Z"
  }
]
```

---

#### GET `/api/v1/collections/{collection_id}`

Get detailed information for a specific collection.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | integer | Yes | Collection ID |

**Response:** `200 OK`

**Response Model:** `CollectionResponse`

**Example Request:**
```bash
GET /api/v1/collections/1
```

**Example Response:**
```json
{
  "id": 1,
  "name": "Python Tutorials",
  "description": "Collection of Python programming tutorials",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Collection with the specified ID does not exist

---

#### GET `/api/v1/collections/{collection_id}/videos`

Get videos in a specific collection with pagination.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | integer | Yes | Collection ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `limit` | integer | No | `50` | `1-500` | Maximum number of results |
| `offset` | integer | No | `0` | `>= 0` | Number of results to skip |

**Response:** `200 OK`

**Response Model:** `SearchResponse`

**Example Request:**
```bash
GET /api/v1/collections/1/videos?limit=20&offset=0
```

**Example Response:**
```json
{
  "results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Python Tutorial: Machine Learning Basics",
      "channel_id": "UC1234567890",
      "channel_name": "Tech Educator",
      "watched_at": "2025-11-02T14:30:00Z",
      "duration_seconds": 3600,
      "duration_formatted": "1:00:00",
      "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
      "is_deleted": false,
      "relevance_score": null,
      "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  ],
  "total_count": 25,
  "query": "collection:1",
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "execution_time_ms": 0.0
}
```

**Error Responses:**
- `404 Not Found`: Collection with the specified ID does not exist

---

#### GET `/api/v1/collections/{collection_id}/stats`

Get statistics for a specific collection.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | integer | Yes | Collection ID |

**Response:** `200 OK`

**Response Model:** `CollectionStatsResponse`

**Example Request:**
```bash
GET /api/v1/collections/1/stats
```

**Example Response:**
```json
{
  "name": "Python Tutorials",
  "video_count": 25,
  "total_hours": 50.5,
  "top_keywords": ["python", "tutorial", "programming", "machine learning"]
}
```

**Error Responses:**
- `404 Not Found`: Collection with the specified ID does not exist

---

### Transcripts

#### GET `/api/v1/videos/{video_id}/transcript`

Get transcript for a video. If the requested language is not available, returns any available transcript for the video.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID (11 characters) |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | string | No | `en` | Language code for transcript (e.g., `en`, `es`, `fr`) |

**Response:** `200 OK`

**Response Model:** `TranscriptResponse`

**Example Request:**
```bash
GET /api/v1/videos/dQw4w9WgXcQ/transcript?language=en
```

**Example Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "language_code": "en",
  "transcript_text": "Welcome to this Python tutorial. Today we'll be learning about machine learning...",
  "transcript_json": "{\"segments\": [{\"start\": 0.0, \"end\": 5.0, \"text\": \"Welcome to this Python tutorial.\"}]}",
  "fetched_at": "2025-11-02T14:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Transcript not found for the specified video and language

**Example Error:**
```json
{
  "detail": "Transcript not found for video dQw4w9WgXcQ (language: en)"
}
```

---

## Data Models

### VideoResponse

Complete video metadata including enrichment data from YouTube Data API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID (11 characters) |
| `title` | string | Yes | Video title |
| `channel_id` | string | Yes | YouTube channel ID |
| `channel_name` | string | No | Channel name |
| `description` | string | No | Video description |
| `duration_seconds` | integer | No | Video duration in seconds |
| `duration_formatted` | string | No | Human-readable duration (e.g., "1:00:00") |
| `published_at` | datetime | No | Video publication date (ISO 8601) |
| `thumbnail_url` | string | No | Video thumbnail URL |
| `is_deleted` | boolean | No | Whether video has been deleted (default: `false`) |
| `deleted_at` | datetime | No | Date when video was deleted |
| `view_count` | integer | No | Total view count |
| `like_count` | integer | No | Total like count |
| `comment_count` | integer | No | Total comment count |
| `category_id` | string | No | YouTube category ID |
| `tags` | string | No | Comma-separated tags |
| `has_captions` | boolean | No | Whether video has captions (default: `false`) |
| `video_url` | string | No | Full YouTube video URL |
| `created_at` | datetime | Yes | Record creation timestamp (ISO 8601) |
| `updated_at` | datetime | Yes | Record last update timestamp (ISO 8601) |

**Example:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Python Tutorial: Machine Learning Basics",
  "channel_id": "UC1234567890",
  "channel_name": "Tech Educator",
  "description": "Learn the basics of machine learning...",
  "duration_seconds": 3600,
  "duration_formatted": "1:00:00",
  "published_at": "2024-01-15T10:00:00Z",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
  "is_deleted": false,
  "deleted_at": null,
  "view_count": 50000,
  "like_count": 1200,
  "comment_count": 150,
  "category_id": "27",
  "tags": "python,machine learning,tutorial",
  "has_captions": true,
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "created_at": "2025-11-02T14:30:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

---

### ChannelResponse

Channel information and statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID |
| `name` | string | Yes | Channel name |
| `description` | string | No | Channel description |
| `subscriber_count` | integer | No | Total subscriber count |
| `video_count` | integer | No | Total video count |
| `view_count` | integer | No | Total view count |
| `channel_url` | string | No | Channel URL |
| `created_at` | datetime | Yes | Record creation timestamp (ISO 8601) |
| `updated_at` | datetime | Yes | Record last update timestamp (ISO 8601) |

**Example:**
```json
{
  "channel_id": "UC1234567890",
  "name": "Tech Educator",
  "description": "Educational technology content",
  "subscriber_count": 100000,
  "video_count": 500,
  "view_count": 5000000,
  "channel_url": "https://www.youtube.com/channel/UC1234567890",
  "created_at": "2025-11-02T14:30:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

---

### SearchResultResponse

Single search result item (used in search and list endpoints).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |
| `title` | string | Yes | Video title |
| `channel_id` | string | Yes | YouTube channel ID |
| `channel_name` | string | Yes | Channel name |
| `watched_at` | datetime | Yes | When the video was watched (ISO 8601) |
| `duration_seconds` | integer | No | Video duration in seconds |
| `duration_formatted` | string | No | Human-readable duration (e.g., "1:00:00") |
| `thumbnail_url` | string | No | Video thumbnail URL |
| `is_deleted` | boolean | Yes | Whether video has been deleted |
| `relevance_score` | float | No | Search relevance score (0.0-1.0) |
| `watch_url` | string | Yes | Full YouTube video URL |

**Example:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Python Tutorial: Machine Learning Basics",
  "channel_id": "UC1234567890",
  "channel_name": "Tech Educator",
  "watched_at": "2025-11-02T14:30:00Z",
  "duration_seconds": 3600,
  "duration_formatted": "1:00:00",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
  "is_deleted": false,
  "relevance_score": 0.95,
  "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

---

### SearchResponse

Paginated search results container.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `results` | array | Yes | Array of `SearchResultResponse` objects |
| `total_count` | integer | Yes | Total number of matching items |
| `query` | string | Yes | The search query used |
| `limit` | integer | Yes | Maximum number of results per page |
| `offset` | integer | Yes | Number of results skipped |
| `has_more` | boolean | Yes | Whether more results are available |
| `execution_time_ms` | float | Yes | Query execution time in milliseconds |

---

### ChannelStatsResponse

Channel statistics for analytics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID |
| `channel_name` | string | Yes | Channel name |
| `video_count` | integer | Yes | Number of videos watched from this channel |
| `total_watch_events` | integer | Yes | Total number of watch events |
| `first_watched` | datetime | Yes | First time a video from this channel was watched (ISO 8601) |
| `last_watched` | datetime | Yes | Most recent time a video from this channel was watched (ISO 8601) |

**Example:**
```json
{
  "channel_id": "UC1234567890",
  "channel_name": "Tech Educator",
  "video_count": 50,
  "total_watch_events": 200,
  "first_watched": "2020-01-15T08:00:00Z",
  "last_watched": "2025-11-02T14:30:00Z"
}
```

---

### CollectionStatsResponse

Collection statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Collection name |
| `video_count` | integer | Yes | Number of videos in collection |
| `total_hours` | float | Yes | Total watch time in hours |
| `top_keywords` | array[string] | Yes | Top keywords extracted from collection videos |

**Example:**
```json
{
  "name": "Python Tutorials",
  "video_count": 25,
  "total_hours": 50.5,
  "top_keywords": ["python", "tutorial", "programming", "machine learning"]
}
```

---

### WatchStatisticsResponse

Comprehensive watch history statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_videos` | integer | Yes | Total number of unique videos |
| `total_channels` | integer | Yes | Total number of unique channels |
| `total_watch_events` | integer | Yes | Total number of watch events |
| `oldest_watch` | datetime | No | Oldest watch event timestamp (ISO 8601) |
| `newest_watch` | datetime | No | Newest watch event timestamp (ISO 8601) |
| `videos_with_duration` | integer | Yes | Number of videos with duration metadata |
| `videos_needing_enrichment` | integer | Yes | Number of videos missing metadata |
| `videos_with_transcripts` | integer | No | Number of videos with transcripts (default: `0`) |
| `total_watch_time_hours` | float | No | Total watch time in hours (default: `0.0`) |
| `average_video_duration_seconds` | float | No | Average video duration in seconds (default: `0.0`) |
| `total_collections` | integer | No | Total number of collections (default: `0`) |
| `top_channels` | array | No | Array of `ChannelStatsResponse` objects (default: `[]`) |
| `collections_info` | array | No | Array of `CollectionStatsResponse` objects (default: `[]`) |

---

### CollectionResponse

Collection information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Collection ID |
| `name` | string | Yes | Collection name |
| `description` | string | No | Collection description |
| `created_at` | datetime | Yes | Collection creation timestamp (ISO 8601) |
| `updated_at` | datetime | Yes | Collection last update timestamp (ISO 8601) |

**Example:**
```json
{
  "id": 1,
  "name": "Python Tutorials",
  "description": "Collection of Python programming tutorials",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-11-02T14:30:00Z"
}
```

---

### TranscriptResponse

Video transcript data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |
| `language_code` | string | Yes | Language code (e.g., `en`, `es`) |
| `transcript_text` | string | Yes | Full transcript text |
| `transcript_json` | string | No | JSON string with timestamped segments |
| `fetched_at` | datetime | No | When transcript was fetched (ISO 8601) |

**Example:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "language_code": "en",
  "transcript_text": "Welcome to this Python tutorial...",
  "transcript_json": "{\"segments\": [...]}",
  "fetched_at": "2025-11-02T14:30:00Z"
}
```

---

### HealthResponse

Health check response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Health status (`healthy` or `degraded`) |
| `version` | string | Yes | API version |
| `database_connected` | boolean | Yes | Whether database is connected |

---

### ErrorResponse

Standard error response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail` | string | Yes | Error message |
| `error_type` | string | No | Error type (`DatabaseError`, `SearchError`, `ValidationError`) |

---

## Usage Examples

### Example 1: Search for Python Tutorials

Search for videos containing "python" and "tutorial" from a specific channel, watched in the last year.

```bash
GET /api/v1/search?q=python+tutorial&channel_id=UC1234567890&date_from=2024-11-02&limit=20
```

### Example 2: Get Recent Videos with Pagination

Get the most recent 50 videos, then fetch the next page.

```bash
# First page
GET /api/v1/videos?limit=50&offset=0

# Second page
GET /api/v1/videos?limit=50&offset=50
```

### Example 3: Find Long-Form Content

Search for videos longer than 30 minutes (1800 seconds).

```bash
GET /api/v1/search?q=machine+learning&min_duration=1800&limit=10
```

### Example 4: Get Channel Statistics

Get statistics for a specific channel and then list all videos from that channel.

```bash
# Get channel info
GET /api/v1/channels/UC1234567890

# Get all videos from that channel
GET /api/v1/videos?channel_id=UC1234567890&limit=100
```

### Example 5: Browse Collections

List all collections, then get videos from a specific collection.

```bash
# List collections
GET /api/v1/collections

# Get videos in collection
GET /api/v1/collections/1/videos?limit=25
```

### Example 6: Get Overall Statistics

Get comprehensive statistics about watch history.

```bash
GET /api/v1/stats
```

### Example 7: Date Range Search

Find videos watched between two dates.

```bash
GET /api/v1/search?q=&date_from=2025-01-01&date_to=2025-12-31&limit=100
```

### Example 8: Get Video Transcript

Retrieve transcript for a specific video.

```bash
GET /api/v1/videos/dQw4w9WgXcQ/transcript?language=en
```

---

## Best Practices

### Pagination

- Use reasonable `limit` values (10-100) for better performance
- Always check `has_more` before fetching the next page
- Use `offset` for sequential pagination

### Search Queries

- Use specific keywords for better results
- Combine multiple filters to narrow results
- Use date ranges to limit search scope
- For phrase searches, use quotes: `"machine learning"`

### Performance

- Limit result sets to what you need
- Use filters to reduce result size
- Cache statistics endpoints if calling frequently
- Use specific endpoints (e.g., `/videos/{id}`) instead of searching when you know the ID

### Error Handling

- Always check HTTP status codes
- Parse `error_type` to handle different error categories appropriately
- Display `detail` message to users for debugging
- Implement retry logic for `500` errors

---

## CORS Configuration

The API is configured to allow CORS from all origins, making it suitable for local network deployments and development. For production deployments, consider restricting CORS to specific domains.

---

## Rate Limiting

Currently, the API does not implement rate limiting. For production deployments, consider adding rate limiting to prevent abuse.

---

## Notes for AI Systems

When using this API:

1. **Always check response status codes** before processing data
2. **Handle pagination** by checking `has_more` and incrementing `offset`
3. **Parse datetime fields** as ISO 8601 strings
4. **Use appropriate filters** to reduce result sizes and improve performance
5. **Handle optional fields** - many fields can be `null` or missing
6. **Validate video IDs** are 11 characters before making requests
7. **Use collection IDs** as integers, not strings
8. **Date filters** use `YYYY-MM-DD` format, not full datetime
9. **Search queries** support FTS5 syntax for advanced searching
10. **Error responses** always include a `detail` field with human-readable messages

---

## Version History

- **1.0.0** (Current): Initial API release with full CRUD operations for watch history data

---

## Support

For issues, questions, or contributions, refer to the project repository or documentation.

