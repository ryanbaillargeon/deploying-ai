<!-- 1870582b-ced3-4229-8471-c4a03acc3808 4eb8ff82-5dd3-48c5-a554-d80d7c104713 -->
# AI Observability Logging System Implementation Plan

## Overview

Create a reusable AI observability system that provides structured logging for AI/LLM applications, separate from application performance logging. The system includes a real-time web UI for log viewing, filtering capabilities, and comprehensive tracking of prompts, responses, tool calls, costs, and performance metrics.

## Architecture

```
05_src/
├── utils/
│   ├── ai_logger.py          # Core AI logging module (NEW)
│   └── logger.py             # Existing app logger (unchanged)
├── ai_observability/         # Reusable component package (NEW)
│   ├── __init__.py
│   ├── storage.py            # Log storage and querying
│   ├── ui.py                 # Gradio UI dashboard
│   ├── models.py             # Pydantic models (if needed)
│   └── README.md             # Implementation guide
└── assignment_chat/
    └── src/
        └── core/
            └── chat_engine.py  # Integrate AI logging (MODIFY)
```

## Implementation Steps

### Phase 1: Core AI Logger Module

**File: `05_src/utils/ai_logger.py`**

Create the core AI logging module with:

1. **Enums and Data Models**

   - `LogCategory` enum: PROMPT, RESPONSE, TOOL_CALL, TOOL_RESULT, EVALUATION, PERFORMANCE, COST, ERROR, GUARDRAIL, MODEL_CONFIG
   - `LogSeverity` enum: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - `AILogEntry` dataclass with all fields (id, timestamp, conversation_id, category, severity, message, metadata, model_name, prompt_text, response_text, token counts, latency, cost, tool_name, evaluation_scores)

2. **Context Management**

   - Use `contextvars.ContextVar` for thread-local conversation_id tracking
   - `conversation_id_ctx` variable for automatic conversation ID propagation

3. **AILogger Class**

   - `__init__` with configurable parameters:
     - `storage_path`: SQLite database path (default: `./ai_logs.db` or `AI_LOG_DB_PATH` env var)
     - `min_severity`: Minimum severity level to log (default: INFO)
     - `enabled_categories`: List of categories to log (None = all)
     - `max_log_length`: Maximum text length before truncation (default: 10000)
   - `_init_db()`: Create SQLite schema with indexes on conversation_id, category, severity, timestamp
   - `_should_log()`: Check severity and category filters
   - `_truncate_text()`: Truncate long prompts/responses
   - `log()`: Main logging method with all parameters
   - `_store()`: Store log entry in SQLite database
   - Convenience methods: `log_prompt()`, `log_response()`, `log_tool_call()`, `log_tool_result()`, `log_evaluation()`
   - Context methods: `set_conversation_id()`, `clear_conversation_id()`

4. **Global Logger Instance**

   - `get_ai_logger()`: Singleton pattern for global logger
   - `set_ai_logger()`: Allow custom logger configuration
   - Read environment variables: `AI_LOG_DB_PATH`, `AI_LOG_MIN_SEVERITY`

### Phase 2: Log Storage Module

**File: `05_src/ai_observability/storage.py`**

Create storage and querying interface:

1. **LogStorage Class**

   - `__init__(db_path)`: Initialize with database path
   - `query_logs()`: Query with filters (conversation_id, category, severity, model_name, start_time, end_time, limit, offset)
   - `get_conversation_logs()`: Get all logs for a specific conversation
   - `get_statistics()`: Aggregate statistics (total logs, by category, by severity, total tokens, total cost, avg latency)
   - `get_unique_conversation_ids()`: Get list of unique conversation IDs for dropdown

### Phase 3: Real-time UI Dashboard

**File: `05_src/ai_observability/ui.py`**

Create Gradio-based UI:

1. **AILogViewer Class**

   - `__init__(db_path)`: Initialize with LogStorage instance
   - `format_log_entry()`: Format log entry for display with all relevant fields
   - `get_logs()`: Get filtered logs based on UI inputs
   - `get_statistics()`: Get formatted statistics display
   - `get_conversation_ids()`: Get conversation IDs for dropdown
   - `create_ui()`: Build Gradio interface with:
     - Filters: Conversation ID dropdown, Category dropdown, Severity dropdown, Model dropdown, Hours back slider
     - Actions: Refresh Logs button, View Statistics button
     - Outputs: Logs textbox (30-50 lines), Statistics textbox (20 lines)
     - Auto-refresh: Load logs every 5 seconds using `ui.load(every=5)`

2. **Launch Function**

   - `launch_ui(db_path, server_port)`: Launch Gradio UI on specified port (default: 7861)

### Phase 4: Package Initialization

**File: `05_src/ai_observability/__init__.py`**

Export main components:

- `from .storage import LogStorage`
- `from .ui import AILogViewer, launch_ui`
- `from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity`

### Phase 5: Integration into assignment_chat

**File: `05_src/assignment_chat/src/core/chat_engine.py`**

Integrate AI logging into ChatEngine:

1. **Imports**

   - Add: `from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity`
   - Add: `import uuid`, `import time`

2. **ChatEngine.init**

   - Initialize: `self.ai_logger = get_ai_logger()`
   - Store model name: `self.model_name = model_name or os.getenv('OPENAI_MODEL', 'gpt-4o')`

3. **ChatEngine.process_message**

   - Generate conversation_id: `conversation_id = str(uuid.uuid4())`
   - Set context: `self.ai_logger.set_conversation_id(conversation_id)`
   - Track start time: `start_time = time.time()`
   - Log prompt before model invocation
   - Extract token counts from response metadata if available
   - Calculate latency: `latency_ms = (time.time() - start_time) * 1000`
   - Log response after receiving it
   - Update `_handle_tool_calls` call to pass conversation_id
   - Wrap in try/except with error logging
   - Clear conversation_id in finally block

4. **ChatEngine._handle_tool_calls**

   - Add `conversation_id` parameter
   - Log each tool call before execution
   - Track tool execution time
   - Log tool results (success/failure) with latency
   - Pass conversation_id to recursive calls

### Phase 6: Implementation Guide

**File: `05_src/ai_observability/README.md`**

Create comprehensive guide with:

1. **Overview**: Purpose and features
2. **Quick Start**: Basic usage examples
3. **Configuration**: Environment variables and programmatic config
4. **Launch UI**: How to start the dashboard
5. **Log Categories**: Description of each category
6. **Filtering and Verbosity Control**: 

   - By severity (min_severity parameter)
   - By category (enabled_categories parameter)
   - Text truncation (max_log_length parameter)

7. **Integration Patterns**:

   - Context manager pattern for conversation tracking
   - Decorator pattern for automatic logging

8. **Querying Logs**: Programmatic querying examples
9. **Best Practices**: Guidelines for effective logging
10. **Project Structure**: How to add to new projects
11. **Troubleshooting**: Common issues and solutions

### Phase 7: Testing and Validation

1. **Test Core Logger**

   - Test all log categories
   - Test severity filtering
   - Test category filtering
   - Test text truncation
   - Test conversation ID context

2. **Test Storage**

   - Test querying with various filters
   - Test statistics aggregation
   - Test conversation ID retrieval

3. **Test UI**

   - Test all filters work correctly
   - Test auto-refresh functionality
   - Test statistics display

4. **Test Integration**

   - Test logging in chat_engine
   - Verify logs are created during chat interactions
   - Verify UI can display logs

## Key Design Decisions

1. **SQLite Storage**: Simple, file-based, no external dependencies, suitable for development and small-medium deployments
2. **Context Variables**: Thread-safe conversation ID tracking without passing IDs everywhere
3. **Gradio UI**: Already in dependencies, easy to use, supports auto-refresh
4. **Structured Logging**: All logs stored as structured data for easy querying
5. **Separation of Concerns**: AI logging completely separate from application logging
6. **Reusability**: Standalone package that can be copied to other projects

## File Changes Summary

**New Files:**

- `05_src/utils/ai_logger.py` (~400 lines)
- `05_src/ai_observability/__init__.py` (~10 lines)
- `05_src/ai_observability/storage.py` (~150 lines)
- `05_src/ai_observability/ui.py` (~200 lines)
- `05_src/ai_observability/README.md` (~300 lines)

**Modified Files:**

- `05_src/assignment_chat/src/core/chat_engine.py` (add AI logging integration)

## Dependencies

All required dependencies already in `pyproject.toml`:

- sqlite3 (built-in)
- gradio (already included)
- pydantic (already included)
- contextvars (built-in Python 3.7+)

## Environment Variables

- `AI_LOG_DB_PATH`: Path to SQLite database (default: `./ai_logs.db`)
- `AI_LOG_MIN_SEVERITY`: Minimum severity level (default: `INFO`)

## Success Criteria

1. AI logger creates structured log entries in SQLite database
2. All log categories work correctly
3. Severity and category filtering work as expected
4. UI displays logs in real-time with filtering
5. Integration in chat_engine logs all AI interactions
6. Implementation guide is clear and complete
7. System is reusable across projects

### To-dos

- [ ] Create core AI logger module (utils/ai_logger.py) with enums, data models, context management, AILogger class, and global instance management
- [ ] Create log storage module (ai_observability/storage.py) with LogStorage class for querying and statistics
- [ ] Create Gradio UI module (ai_observability/ui.py) with AILogViewer class and real-time dashboard
- [ ] Create package initialization file (ai_observability/__init__.py) with proper exports
- [ ] Create comprehensive implementation guide (ai_observability/README.md) with usage examples, patterns, and best practices
- [ ] Integrate AI logging into assignment_chat ChatEngine (chat_engine.py) with conversation tracking, prompt/response logging, and tool call logging
- [ ] Test all components: logger functionality, storage queries, UI filters, and integration in chat_engine