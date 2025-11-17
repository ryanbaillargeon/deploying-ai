# AI Observability System - Implementation Guide

## Overview

The AI Observability System provides structured logging specifically for AI/LLM applications, separate from application performance logging. It includes:

- Structured AI event logging
- Real-time log viewing UI
- Filtering and querying capabilities
- Cost and performance tracking
- Reusable across projects

## Quick Start

### 1. Installation

No additional dependencies beyond what's already in the project (sqlite3, gradio, pydantic).

### 2. Basic Usage

```python
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity

# Get logger instance
ai_logger = get_ai_logger()

# Set conversation context
ai_logger.set_conversation_id("conv-123")

# Log a prompt
ai_logger.log_prompt(
    prompt_text="What is the weather?",
    model_name="gpt-4o"
)

# Log a response
ai_logger.log_response(
    response_text="The weather is sunny.",
    model_name="gpt-4o",
    token_count_input=10,
    token_count_output=5,
    latency_ms=250.5
)

# Log tool calls
ai_logger.log_tool_call(
    tool_name="get_weather",
    tool_args={"location": "NYC"}
)
```

### 3. Configuration

Set environment variables:

```bash
# Log database path (use absolute path or path relative to where app runs)
export AI_LOG_DB_PATH="./ai_logs.db"

# Minimum severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export AI_LOG_MIN_SEVERITY="INFO"
```

**Important**: The database path is relative to where your application runs. If your app runs from `assignment_chat/`, the database will be created there. When launching the UI, make sure to point it to the same database file:

```bash
# If your app runs from assignment_chat/, use:
python -m ai_observability.ui --db-path ./assignment_chat/ai_logs.db --port 7861

# Or set AI_LOG_DB_PATH in your .env file to use an absolute path:
# AI_LOG_DB_PATH=/absolute/path/to/ai_logs.db
```

Or configure programmatically:

```python
from utils.ai_logger import AILogger, LogSeverity, LogCategory

logger = AILogger(
    storage_path="./custom_path/ai_logs.db",
    min_severity=LogSeverity.WARNING,  # Only log warnings and above
    enabled_categories=[LogCategory.PROMPT, LogCategory.RESPONSE],  # Only these categories
    max_log_length=5000  # Truncate long texts
)

from utils.ai_logger import set_ai_logger
set_ai_logger(logger)
```

### 4. Launch UI

```python
from ai_observability.ui import launch_ui

# Launch on default port 7861
launch_ui(db_path="./ai_logs.db")

# Or custom port
launch_ui(db_path="./ai_logs.db", server_port=7862)
```

Or from command line:

```bash
python -m ai_observability.ui --db-path ./ai_logs.db --port 7861
```

## Log Categories

- `PROMPT`: User prompts sent to models
- `RESPONSE`: Model responses received
- `TOOL_CALL`: Tool/function calls made
- `TOOL_RESULT`: Tool execution results
- `EVALUATION`: Response quality evaluations
- `PERFORMANCE`: Performance metrics
- `COST`: Cost tracking
- `ERROR`: Errors and exceptions
- `GUARDRAIL`: Guardrail violations
- `MODEL_CONFIG`: Model configuration changes

## Filtering and Verbosity Control

### By Severity

```python
# Only log INFO and above
logger = AILogger(min_severity=LogSeverity.INFO)

# Only log errors
logger = AILogger(min_severity=LogSeverity.ERROR)
```

### By Category

```python
# Only log prompts and responses
logger = AILogger(
    enabled_categories=[LogCategory.PROMPT, LogCategory.RESPONSE]
)
```

### Text Truncation

```python
# Truncate prompts/responses longer than 1000 chars
logger = AILogger(max_log_length=1000)
```

## Integration Patterns

### Pattern 1: Context Manager (Recommended)

```python
from contextlib import contextmanager
import uuid

@contextmanager
def conversation_context(conversation_id: Optional[str] = None):
    from utils.ai_logger import get_ai_logger
    ai_logger = get_ai_logger()
    conv_id = conversation_id or str(uuid.uuid4())
    ai_logger.set_conversation_id(conv_id)
    try:
        yield conv_id
    finally:
        ai_logger.clear_conversation_id()

# Usage
with conversation_context() as conv_id:
    ai_logger.log_prompt(...)
    # All logs in this block use conv_id
```

### Pattern 2: Decorator

```python
from functools import wraps
import uuid
import time
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity

def log_ai_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ai_logger = get_ai_logger()
        conv_id = str(uuid.uuid4())
        ai_logger.set_conversation_id(conv_id)
        try:
            start = time.time()
            result = func(*args, **kwargs)
            latency = (time.time() - start) * 1000
            ai_logger.log(
                category=LogCategory.PERFORMANCE,
                message=f"{func.__name__} completed",
                latency_ms=latency
            )
            return result
        finally:
            ai_logger.clear_conversation_id()
    return wrapper

@log_ai_call
def my_ai_function(prompt):
    # ... function code ...
    pass
```

### Pattern 3: Direct Integration

```python
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity
import uuid
import time

ai_logger = get_ai_logger()

def process_user_message(message: str):
    conversation_id = str(uuid.uuid4())
    ai_logger.set_conversation_id(conversation_id)
    
    try:
        start_time = time.time()
        
        # Log prompt
        ai_logger.log_prompt(
            prompt_text=message,
            model_name="gpt-4o",
            conversation_id=conversation_id
        )
        
        # Process message
        response = model.invoke(message)
        
        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        token_input = getattr(response, 'usage', {}).get('prompt_tokens', 0)
        token_output = getattr(response, 'usage', {}).get('completion_tokens', 0)
        
        # Log response
        ai_logger.log_response(
            response_text=response.content,
            model_name="gpt-4o",
            token_count_input=token_input,
            token_count_output=token_output,
            latency_ms=latency_ms,
            conversation_id=conversation_id
        )
        
        return response.content
        
    except Exception as e:
        ai_logger.log(
            category=LogCategory.ERROR,
            message=f"Error processing message: {e}",
            severity=LogSeverity.ERROR,
            conversation_id=conversation_id
        )
        raise
    finally:
        ai_logger.clear_conversation_id()
```

## Querying Logs Programmatically

```python
from ai_observability.storage import LogStorage
from datetime import datetime, timedelta

storage = LogStorage("./ai_logs.db")

# Get logs for a conversation
logs = storage.get_conversation_logs("conv-123")

# Query with filters
logs = storage.query_logs(
    conversation_id="conv-123",
    category="response",
    severity="INFO",
    limit=100
)

# Get statistics
stats = storage.get_statistics()
print(f"Total cost: ${stats['total_cost_usd']:.2f}")
print(f"Total logs: {stats['total_logs']}")
print(f"By category: {stats['by_category']}")

# Get statistics for last 24 hours
start_time = datetime.utcnow() - timedelta(hours=24)
stats = storage.get_statistics(start_time=start_time)
```

## Best Practices

1. **Always set conversation_id**: Use context managers or explicit setting to track conversations
2. **Log at appropriate levels**: Use DEBUG for development, INFO for production
3. **Don't log sensitive data**: Be careful with prompts/responses containing PII
4. **Use categories appropriately**: Choose the right category for each event
5. **Monitor costs**: Track token usage and costs regularly
6. **Review logs regularly**: Use the UI to spot issues and trends
7. **Set appropriate filters**: Use severity and category filters to reduce log volume in production

## Project Structure

When adding to a new project:

```
your_project/
├── src/
│   └── your_code.py  # Your application code
├── ai_observability/  # Copy this directory
│   ├── __init__.py
│   ├── storage.py
│   ├── ui.py
│   └── README.md
└── utils/
    └── ai_logger.py  # Copy this file
```

Then import:

```python
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from ai_logger import get_ai_logger
```

## UI Features

The Gradio UI provides:

- **Real-time log viewing**: Auto-refreshes every 5 seconds
- **Filtering**: By conversation ID, category, severity, model, time range
- **Statistics**: Aggregate metrics including total tokens, costs, latency
- **Search**: Filter logs by multiple criteria simultaneously
- **Export**: Copy logs and statistics for analysis

## Troubleshooting

**UI not showing logs**: 
- Check that `db_path` matches where logs are being written
- Ensure the database file exists and is accessible
- Verify logs have been created (check database file size)

**Too many logs**: 
- Adjust `min_severity` to filter by severity level
- Use `enabled_categories` to filter by category
- Increase `max_log_length` truncation threshold

**Database locked**: 
- Ensure only one process writes to the database at a time
- Close any other connections to the database
- Check for long-running transactions

**Missing conversation IDs**: 
- Make sure to call `set_conversation_id()` before logging
- Use context managers to ensure conversation IDs are set correctly
- Check that conversation_id is passed explicitly when needed

**Import errors**: 
- Ensure `utils/ai_logger.py` is in your Python path
- Check that all dependencies (sqlite3, gradio, pydantic) are installed
- Verify the `ai_observability` package structure is correct

## Example: Full Integration

```python
from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity
from langchain_openai import ChatOpenAI
import uuid
import time

class AIChatService:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")
        self.ai_logger = get_ai_logger()
    
    def chat(self, message: str, history: list = None):
        conversation_id = str(uuid.uuid4())
        self.ai_logger.set_conversation_id(conversation_id)
        
        try:
            start_time = time.time()
            
            # Log prompt
            self.ai_logger.log_prompt(
                prompt_text=message,
                model_name="gpt-4o",
                conversation_id=conversation_id,
                history_length=len(history) if history else 0
            )
            
            # Get response
            response = self.model.invoke(message)
            
            # Extract metrics
            latency_ms = (time.time() - start_time) * 1000
            usage = getattr(response, 'response_metadata', {}).get('token_usage', {})
            token_input = usage.get('prompt_tokens', 0)
            token_output = usage.get('completion_tokens', 0)
            
            # Log response
            self.ai_logger.log_response(
                response_text=response.content,
                model_name="gpt-4o",
                token_count_input=token_input,
                token_count_output=token_output,
                latency_ms=latency_ms,
                conversation_id=conversation_id
            )
            
            return response.content
            
        except Exception as e:
            self.ai_logger.log(
                category=LogCategory.ERROR,
                message=f"Chat error: {e}",
                severity=LogSeverity.ERROR,
                conversation_id=conversation_id,
                error_type=type(e).__name__
            )
            raise
        finally:
            self.ai_logger.clear_conversation_id()
```

## Advanced Usage

### Custom Log Categories

While the system provides standard categories, you can use the generic `log()` method with any category:

```python
ai_logger.log(
    category=LogCategory.PERFORMANCE,
    message="Custom performance metric",
    custom_metric=42.5,
    custom_label="throughput"
)
```

### Batch Logging

For high-volume scenarios, consider batching writes (future enhancement) or using async logging.

### Database Maintenance

The SQLite database will grow over time. Consider:
- Periodic cleanup of old logs
- Archiving logs to separate files
- Using database compression
- Setting up log rotation

## License

See LICENSE file in project root.

