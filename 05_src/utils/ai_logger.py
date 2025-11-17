"""AI Observability Logger - Separate from application logging"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from contextvars import ContextVar
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

# Context variable for conversation ID (thread-local)
conversation_id_ctx: ContextVar[Optional[str]] = ContextVar('conversation_id', default=None)


class LogCategory(str, Enum):
    """Categories for AI-specific logs"""
    PROMPT = "prompt"
    RESPONSE = "response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    EVALUATION = "evaluation"
    PERFORMANCE = "performance"
    COST = "cost"
    ERROR = "error"
    GUARDRAIL = "guardrail"
    MODEL_CONFIG = "model_config"


class LogSeverity(str, Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AILogEntry:
    """Structured AI log entry"""
    id: str
    timestamp: datetime
    conversation_id: Optional[str]
    category: LogCategory
    severity: LogSeverity
    message: str
    metadata: Dict[str, Any]
    model_name: Optional[str] = None
    prompt_text: Optional[str] = None
    response_text: Optional[str] = None
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    tool_name: Optional[str] = None
    evaluation_scores: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        return data


class AILogger:
    """AI-specific logger with structured logging and storage"""
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        min_severity: LogSeverity = LogSeverity.INFO,
        enabled_categories: Optional[List[LogCategory]] = None,
        max_log_length: int = 10000,  # Truncate long prompts/responses
    ):
        """
        Initialize AI Logger
        
        Args:
            storage_path: Path to SQLite database (default: ./ai_logs.db)
            min_severity: Minimum severity level to log
            enabled_categories: List of categories to log (None = all)
            max_log_length: Maximum length for prompt/response text
        """
        self.storage_path = storage_path or os.getenv('AI_LOG_DB_PATH', './ai_logs.db')
        self.min_severity = min_severity
        self.enabled_categories = enabled_categories or list(LogCategory)
        self.max_log_length = max_log_length
        
        # Create storage directory if needed
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                conversation_id TEXT,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT NOT NULL,
                model_name TEXT,
                prompt_text TEXT,
                response_text TEXT,
                token_count_input INTEGER,
                token_count_output INTEGER,
                latency_ms REAL,
                cost_usd REAL,
                tool_name TEXT,
                evaluation_scores TEXT
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON ai_logs(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON ai_logs(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON ai_logs(severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON ai_logs(timestamp)')
        
        conn.commit()
        conn.close()
    
    def _should_log(self, severity: LogSeverity, category: LogCategory) -> bool:
        """Check if log entry should be recorded"""
        severity_levels = {
            LogSeverity.DEBUG: 0,
            LogSeverity.INFO: 1,
            LogSeverity.WARNING: 2,
            LogSeverity.ERROR: 3,
            LogSeverity.CRITICAL: 4,
        }
        
        if severity_levels[severity] < severity_levels[self.min_severity]:
            return False
        
        if category not in self.enabled_categories:
            return False
        
        return True
    
    def _truncate_text(self, text: Optional[str]) -> Optional[str]:
        """Truncate text if too long"""
        if text and len(text) > self.max_log_length:
            return text[:self.max_log_length] + f"... [truncated {len(text) - self.max_log_length} chars]"
        return text
    
    def log(
        self,
        category: LogCategory,
        message: str,
        severity: LogSeverity = LogSeverity.INFO,
        conversation_id: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_text: Optional[str] = None,
        response_text: Optional[str] = None,
        token_count_input: Optional[int] = None,
        token_count_output: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
        tool_name: Optional[str] = None,
        evaluation_scores: Optional[Dict[str, float]] = None,
        **metadata
    ):
        """
        Log an AI event
        
        Args:
            category: Log category
            message: Log message
            severity: Log severity level
            conversation_id: Conversation/request ID (auto from context if None)
            model_name: Model used
            prompt_text: Full prompt text
            response_text: Full response text
            token_count_input: Input token count
            token_count_output: Output token count
            latency_ms: Latency in milliseconds
            cost_usd: Cost in USD
            tool_name: Tool name (for tool calls)
            evaluation_scores: Dict of evaluation scores
            **metadata: Additional metadata
        """
        if not self._should_log(severity, category):
            return
        
        # Get conversation ID from context if not provided
        conv_id = conversation_id or conversation_id_ctx.get()
        
        entry = AILogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            conversation_id=conv_id,
            category=category,
            severity=severity,
            message=message,
            metadata=metadata,
            model_name=model_name,
            prompt_text=self._truncate_text(prompt_text),
            response_text=self._truncate_text(response_text),
            token_count_input=token_count_input,
            token_count_output=token_count_output,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tool_name=tool_name,
            evaluation_scores=evaluation_scores
        )
        
        self._store(entry)
    
    def _store(self, entry: AILogEntry):
        """Store log entry in database"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        eval_scores_json = json.dumps(entry.evaluation_scores) if entry.evaluation_scores else None
        
        cursor.execute('''
            INSERT INTO ai_logs (
                id, timestamp, conversation_id, category, severity, message,
                metadata, model_name, prompt_text, response_text,
                token_count_input, token_count_output, latency_ms, cost_usd,
                tool_name, evaluation_scores
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.timestamp.isoformat(),
            entry.conversation_id,
            entry.category.value,
            entry.severity.value,
            entry.message,
            json.dumps(entry.metadata),
            entry.model_name,
            entry.prompt_text,
            entry.response_text,
            entry.token_count_input,
            entry.token_count_output,
            entry.latency_ms,
            entry.cost_usd,
            entry.tool_name,
            eval_scores_json
        ))
        
        conn.commit()
        conn.close()
    
    def set_conversation_id(self, conversation_id: str):
        """Set conversation ID for current context"""
        conversation_id_ctx.set(conversation_id)
    
    def clear_conversation_id(self):
        """Clear conversation ID from context"""
        conversation_id_ctx.set(None)
    
    # Convenience methods for common log types
    def log_prompt(
        self,
        prompt_text: str,
        model_name: str,
        conversation_id: Optional[str] = None,
        **metadata
    ):
        """Log a prompt"""
        self.log(
            category=LogCategory.PROMPT,
            message=f"Prompt sent to {model_name}",
            prompt_text=prompt_text,
            model_name=model_name,
            conversation_id=conversation_id,
            **metadata
        )
    
    def log_response(
        self,
        response_text: str,
        model_name: str,
        token_count_input: int,
        token_count_output: int,
        latency_ms: float,
        cost_usd: Optional[float] = None,
        conversation_id: Optional[str] = None,
        **metadata
    ):
        """Log a model response"""
        self.log(
            category=LogCategory.RESPONSE,
            message=f"Response received from {model_name}",
            response_text=response_text,
            model_name=model_name,
            token_count_input=token_count_input,
            token_count_output=token_count_output,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            conversation_id=conversation_id,
            **metadata
        )
    
    def log_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_id: Optional[str] = None,
        **metadata
    ):
        """Log a tool call"""
        self.log(
            category=LogCategory.TOOL_CALL,
            message=f"Tool called: {tool_name}",
            tool_name=tool_name,
            conversation_id=conversation_id,
            tool_args=tool_args,
            **metadata
        )
    
    def log_tool_result(
        self,
        tool_name: str,
        success: bool,
        result: Optional[str] = None,
        latency_ms: Optional[float] = None,
        conversation_id: Optional[str] = None,
        **metadata
    ):
        """Log a tool result"""
        severity = LogSeverity.INFO if success else LogSeverity.ERROR
        self.log(
            category=LogCategory.TOOL_RESULT,
            message=f"Tool {tool_name} {'succeeded' if success else 'failed'}",
            severity=severity,
            tool_name=tool_name,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            success=success,
            result=result,
            **metadata
        )
    
    def log_evaluation(
        self,
        evaluation_scores: Dict[str, float],
        conversation_id: Optional[str] = None,
        **metadata
    ):
        """Log evaluation scores"""
        self.log(
            category=LogCategory.EVALUATION,
            message="Response evaluation completed",
            evaluation_scores=evaluation_scores,
            conversation_id=conversation_id,
            **metadata
        )


# Global logger instance (can be configured per project)
_ai_logger: Optional[AILogger] = None


def get_ai_logger() -> AILogger:
    """Get or create global AI logger instance"""
    global _ai_logger
    if _ai_logger is None:
        storage_path = os.getenv('AI_LOG_DB_PATH', './ai_logs.db')
        min_severity_str = os.getenv('AI_LOG_MIN_SEVERITY', 'INFO')
        try:
            min_severity = LogSeverity[min_severity_str]
        except KeyError:
            min_severity = LogSeverity.INFO
        _ai_logger = AILogger(storage_path=storage_path, min_severity=min_severity)
    return _ai_logger


def set_ai_logger(logger: AILogger):
    """Set global AI logger instance"""
    global _ai_logger
    _ai_logger = logger

