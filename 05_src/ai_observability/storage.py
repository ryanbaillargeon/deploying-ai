"""Log storage and querying utilities"""

import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path


class LogStorage:
    """Interface for querying AI logs"""
    
    def __init__(self, db_path: str, create_if_missing: bool = True):
        """
        Initialize log storage
        
        Args:
            db_path: Path to SQLite database file
            create_if_missing: If True, create database schema if it doesn't exist
        """
        self.db_path = db_path
        
        # Create database schema if it doesn't exist
        if create_if_missing and not Path(db_path).exists():
            self._init_db()
        elif not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}. Ensure AI logger has been initialized.")
    
    def _init_db(self):
        """Initialize database schema (same as AILogger._init_db)"""
        conn = sqlite3.connect(self.db_path)
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
    
    def query_logs(
        self,
        conversation_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        model_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query logs with filters
        
        Args:
            conversation_id: Filter by conversation ID
            category: Filter by category
            severity: Filter by severity level
            model_name: Filter by model name
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of log entries as dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if conversation_id:
            conditions.append("conversation_id = ?")
            params.append(conversation_id)
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        
        if model_name:
            conditions.append("model_name = ?")
            params.append(model_name)
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT * FROM ai_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to dictionaries
        result = []
        for row in rows:
            log_dict = dict(row)
            # Parse JSON fields
            if log_dict.get('metadata'):
                try:
                    log_dict['metadata'] = json.loads(log_dict['metadata'])
                except (json.JSONDecodeError, TypeError):
                    log_dict['metadata'] = {}
            
            if log_dict.get('evaluation_scores'):
                try:
                    log_dict['evaluation_scores'] = json.loads(log_dict['evaluation_scores'])
                except (json.JSONDecodeError, TypeError):
                    log_dict['evaluation_scores'] = None
            
            result.append(log_dict)
        
        return result
    
    def get_conversation_logs(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of log entries for the conversation
        """
        return self.query_logs(conversation_id=conversation_id, limit=10000)
    
    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics
        
        Args:
            start_time: Start time for statistics (optional)
            end_time: End time for statistics (optional)
            
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Total logs
        cursor.execute(f"SELECT COUNT(*) FROM ai_logs WHERE {where_clause}", params)
        total_logs = cursor.fetchone()[0]
        
        # By category
        cursor.execute(f'''
            SELECT category, COUNT(*) as count
            FROM ai_logs
            WHERE {where_clause}
            GROUP BY category
        ''', params)
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By severity
        cursor.execute(f'''
            SELECT severity, COUNT(*) as count
            FROM ai_logs
            WHERE {where_clause}
            GROUP BY severity
        ''', params)
        by_severity = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total tokens and cost
        cursor.execute(f'''
            SELECT 
                SUM(token_count_input) as total_input_tokens,
                SUM(token_count_output) as total_output_tokens,
                SUM(cost_usd) as total_cost,
                AVG(latency_ms) as avg_latency
            FROM ai_logs
            WHERE {where_clause} AND token_count_input IS NOT NULL
        ''', params)
        row = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_logs': total_logs,
            'by_category': by_category,
            'by_severity': by_severity,
            'total_input_tokens': row[0] or 0,
            'total_output_tokens': row[1] or 0,
            'total_cost_usd': row[2] or 0.0,
            'avg_latency_ms': row[3] or 0.0
        }
    
    def get_unique_conversation_ids(self, limit: int = 100) -> List[str]:
        """
        Get list of unique conversation IDs
        
        Args:
            limit: Maximum number of conversation IDs to return
            
        Returns:
            List of conversation IDs, ordered by most recent
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT conversation_id
            FROM ai_logs
            WHERE conversation_id IS NOT NULL
            GROUP BY conversation_id
            ORDER BY MAX(timestamp) DESC
            LIMIT ?
        ''', (limit,))
        
        ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return ids
    
    def get_unique_model_names(self) -> List[str]:
        """
        Get list of unique model names
        
        Returns:
            List of model names
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT model_name
            FROM ai_logs
            WHERE model_name IS NOT NULL
            ORDER BY model_name
        ''')
        
        names = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return names

