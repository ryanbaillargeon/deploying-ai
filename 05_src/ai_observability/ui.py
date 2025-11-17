"""Gradio UI for real-time AI log viewing"""

import gradio as gr
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from .storage import LogStorage


class AILogViewer:
    """Real-time AI log viewer UI"""
    
    def __init__(self, db_path: str, create_if_missing: bool = True):
        """
        Initialize log viewer
        
        Args:
            db_path: Path to SQLite database
            create_if_missing: If True, create database schema if it doesn't exist
        """
        self.storage = LogStorage(db_path, create_if_missing=create_if_missing)
        self.auto_refresh = True
    
    def format_log_entry(self, entry: Dict[str, Any]) -> str:
        """Format a log entry for display"""
        timestamp = entry.get('timestamp', '')
        category = entry.get('category', '')
        severity = entry.get('severity', '')
        message = entry.get('message', '')
        conversation_id = entry.get('conversation_id', 'N/A')
        model_name = entry.get('model_name', '')
        
        lines = [
            f"[{timestamp}] {severity} | {category}",
            f"Conversation: {conversation_id}",
        ]
        
        if model_name:
            lines.append(f"Model: {model_name}")
        
        lines.append(f"Message: {message}")
        
        if entry.get('token_count_input') is not None:
            lines.append(f"Tokens: {entry['token_count_input']} in / {entry.get('token_count_output', 0)} out")
        
        if entry.get('latency_ms') is not None:
            lines.append(f"Latency: {entry['latency_ms']:.2f}ms")
        
        if entry.get('cost_usd') is not None:
            lines.append(f"Cost: ${entry['cost_usd']:.6f}")
        
        if entry.get('tool_name'):
            lines.append(f"Tool: {entry['tool_name']}")
        
        if entry.get('evaluation_scores'):
            scores = entry['evaluation_scores']
            if isinstance(scores, str):
                try:
                    scores = json.loads(scores)
                except json.JSONDecodeError:
                    scores = {}
            if scores:
                score_str = ", ".join([f"{k}: {v:.2f}" for k, v in scores.items()])
                lines.append(f"Evaluation: {score_str}")
        
        if entry.get('prompt_text'):
            prompt_preview = entry['prompt_text'][:200] + "..." if len(entry['prompt_text']) > 200 else entry['prompt_text']
            lines.append(f"Prompt: {prompt_preview}")
        
        if entry.get('response_text'):
            response_preview = entry['response_text'][:200] + "..." if len(entry['response_text']) > 200 else entry['response_text']
            lines.append(f"Response: {response_preview}")
        
        metadata = entry.get('metadata', {})
        if metadata and isinstance(metadata, dict) and metadata:
            # Show important metadata fields
            important_meta = {k: v for k, v in metadata.items() if k not in ['tool_args']}
            if important_meta:
                lines.append(f"Metadata: {important_meta}")
        
        return "\n".join(lines)
    
    def get_logs(
        self,
        conversation_id: Optional[str],
        category: Optional[str],
        severity: Optional[str],
        model_name: Optional[str],
        hours_back: int
    ) -> str:
        """Get filtered logs"""
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            # Convert empty strings to None
            conversation_id = conversation_id if conversation_id else None
            category = category if category else None
            severity = severity if severity else None
            model_name = model_name if model_name else None
            
            logs = self.storage.query_logs(
                conversation_id=conversation_id,
                category=category,
                severity=severity,
                model_name=model_name,
                start_time=start_time,
                limit=500
            )
            
            if not logs:
                return "No logs found matching criteria.\n\nNote: Logs will appear here once you start using the AI application."
            
            formatted = [self.format_log_entry(log) for log in logs]
            return "\n\n" + "="*80 + "\n\n".join(formatted)
        except Exception as e:
            return f"Error querying logs: {e}\n\nMake sure the database exists and is accessible."
    
    def get_statistics(self, hours_back: int) -> str:
        """Get statistics"""
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            stats = self.storage.get_statistics(start_time=start_time)
            
            lines = [
                "=== AI Observability Statistics ===",
                f"Time Range: Last {hours_back} hours",
                "",
                f"Total Logs: {stats['total_logs']}",
            ]
            
            if stats['total_logs'] == 0:
                lines.append("")
                lines.append("No logs found. Start using the AI application to generate logs.")
                return "\n".join(lines)
            
            lines.append("")
            lines.append("By Category:")
            for cat, count in sorted(stats['by_category'].items()):
                lines.append(f"  {cat}: {count}")
            
            lines.append("")
            lines.append("By Severity:")
            for sev, count in sorted(stats['by_severity'].items()):
                lines.append(f"  {sev}: {count}")
            
            lines.append("")
            lines.append("Performance Metrics:")
            lines.append(f"  Total Input Tokens: {stats['total_input_tokens']:,}")
            lines.append(f"  Total Output Tokens: {stats['total_output_tokens']:,}")
            lines.append(f"  Total Cost: ${stats['total_cost_usd']:.4f}")
            if stats['avg_latency_ms']:
                lines.append(f"  Avg Latency: {stats['avg_latency_ms']:.2f}ms")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting statistics: {e}\n\nMake sure the database exists and is accessible."
    
    def get_conversation_ids(self) -> List[str]:
        """Get list of conversation IDs"""
        try:
            ids = self.storage.get_unique_conversation_ids(limit=10)
            return ids
        except Exception as e:
            # Log error for debugging (can be removed in production)
            print(f"Error getting conversation IDs: {e}")
            return []
    
    def get_model_names(self) -> List[str]:
        """Get list of model names"""
        try:
            names = self.storage.get_unique_model_names()
            return names
        except Exception as e:
            # Log error for debugging (can be removed in production)
            print(f"Error getting model names: {e}")
            return []
    
    def create_ui(self) -> gr.Blocks:
        """Create Gradio UI"""
        with gr.Blocks(title="AI Observability Dashboard") as ui:
            gr.Markdown("# AI Observability Dashboard")
            
            with gr.Row():
                with gr.Column(scale=1):
                    conversation_dropdown = gr.Dropdown(
                        label="Conversation ID",
                        choices=[""] + self.get_conversation_ids(),
                        value="",
                        allow_custom_value=True,
                        interactive=True
                    )
                    
                    category_dropdown = gr.Dropdown(
                        label="Category",
                        choices=["", "prompt", "response", "tool_call", "tool_result", 
                                "evaluation", "performance", "cost", "error", "guardrail", "model_config"],
                        value="",
                        interactive=True
                    )
                    
                    severity_dropdown = gr.Dropdown(
                        label="Severity",
                        choices=["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        value="",
                        interactive=True
                    )
                    
                    model_dropdown = gr.Dropdown(
                        label="Model",
                        choices=[""] + self.get_model_names(),
                        value="",
                        allow_custom_value=True,
                        interactive=True
                    )
                    
                    hours_slider = gr.Slider(
                        label="Hours Back",
                        minimum=1,
                        maximum=168,
                        value=24,
                        step=1,
                        interactive=True
                    )
                    
                    refresh_btn = gr.Button("Refresh Logs", variant="primary")
                    stats_btn = gr.Button("View Statistics")
                    gr.Markdown("*Tip: Click 'Refresh Logs' to update. For auto-refresh, use browser refresh or check back periodically.*")
            
            with gr.Row():
                logs_output = gr.Textbox(
                    label="Logs",
                    lines=30,
                    max_lines=50,
                    show_copy_button=True,
                    autoscroll=True
                )
            
            with gr.Row():
                stats_output = gr.Textbox(
                    label="Statistics",
                    lines=20,
                    show_copy_button=True
                )
            
            def refresh_logs(conv_id, cat, sev, model, hours):
                logs_text = self.get_logs(conv_id, cat, sev, model, hours)
                # Get updated dropdown choices
                conversation_ids = [""] + self.get_conversation_ids()
                model_names = [""] + self.get_model_names()
                # Preserve current value if it exists in new choices, otherwise use empty string
                current_conv_id = conv_id if conv_id in conversation_ids else ""
                current_model = model if model in model_names else ""
                # Return logs text and updated dropdown choices
                return (
                    logs_text,
                    gr.update(choices=conversation_ids, value=current_conv_id),
                    gr.update(choices=model_names, value=current_model)
                )
            
            def refresh_stats(hours):
                return self.get_statistics(hours)
            
            refresh_btn.click(
                fn=refresh_logs,
                inputs=[conversation_dropdown, category_dropdown, severity_dropdown, 
                       model_dropdown, hours_slider],
                outputs=[logs_output, conversation_dropdown, model_dropdown]
            )
            
            stats_btn.click(
                fn=refresh_stats,
                inputs=[hours_slider],
                outputs=stats_output
            )
            
            # Initial load of logs and statistics
            ui.load(
                fn=refresh_logs,
                inputs=[conversation_dropdown, category_dropdown, severity_dropdown,
                       model_dropdown, hours_slider],
                outputs=[logs_output, conversation_dropdown, model_dropdown]
            )
            
            ui.load(
                fn=refresh_stats,
                inputs=[hours_slider],
                outputs=stats_output
            )
        
        return ui


def launch_ui(db_path: str = "./ai_logs.db", server_port: int = 7861, share: bool = False):
    """
    Launch the AI observability UI
    
    Args:
        db_path: Path to SQLite database
        server_port: Port to run the UI on
        share: Whether to create a public Gradio share link
    """
    viewer = AILogViewer(db_path)
    ui = viewer.create_ui()
    ui.launch(server_port=server_port, share=share)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch AI Observability Dashboard")
    parser.add_argument("--db-path", type=str, default="./ai_logs.db", help="Path to SQLite database")
    parser.add_argument("--port", type=int, default=7861, help="Server port")
    parser.add_argument("--share", action="store_true", help="Create public Gradio share link")
    
    args = parser.parse_args()
    launch_ui(db_path=args.db_path, server_port=args.port, share=args.share)

