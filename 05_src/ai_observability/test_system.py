"""Simple test script to validate AI observability system"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
_current_file_dir = Path(__file__).parent
_05_src_dir = _current_file_dir.parent
if str(_05_src_dir) not in sys.path:
    sys.path.insert(0, str(_05_src_dir))

from utils.ai_logger import get_ai_logger, LogCategory, LogSeverity, AILogger
from ai_observability.storage import LogStorage


def test_logger():
    """Test basic logger functionality"""
    print("Testing AI Logger...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize logger with temp database
        logger = AILogger(storage_path=db_path, min_severity=LogSeverity.DEBUG)
        
        # Test conversation ID context
        logger.set_conversation_id("test-conv-1")
        
        # Test logging different categories
        logger.log_prompt(
            prompt_text="Test prompt",
            model_name="test-model"
        )
        
        logger.log_response(
            response_text="Test response",
            model_name="test-model",
            token_count_input=10,
            token_count_output=5,
            latency_ms=100.5
        )
        
        logger.log_tool_call(
            tool_name="test_tool",
            tool_args={"arg1": "value1"}
        )
        
        logger.log_tool_result(
            tool_name="test_tool",
            success=True,
            latency_ms=50.0
        )
        
        logger.log_evaluation(
            evaluation_scores={"coherence": 0.9, "relevance": 0.8}
        )
        
        logger.log(
            category=LogCategory.ERROR,
            message="Test error",
            severity=LogSeverity.ERROR,
            error_type="TestError"
        )
        
        logger.clear_conversation_id()
        
        print("  ✓ Logger created and logs written")
        
        # Test storage
        storage = LogStorage(db_path)
        logs = storage.query_logs(limit=10)
        assert len(logs) >= 6, f"Expected at least 6 logs, got {len(logs)}"
        print(f"  ✓ Storage query returned {len(logs)} logs")
        
        # Test statistics
        stats = storage.get_statistics()
        assert stats['total_logs'] >= 6, f"Expected at least 6 total logs, got {stats['total_logs']}"
        print(f"  ✓ Statistics: {stats['total_logs']} total logs")
        
        # Test conversation logs
        conv_logs = storage.get_conversation_logs("test-conv-1")
        assert len(conv_logs) >= 6, f"Expected at least 6 logs for conversation, got {len(conv_logs)}"
        print(f"  ✓ Conversation logs: {len(conv_logs)} logs")
        
        # Test filtering
        prompt_logs = storage.query_logs(category="prompt")
        assert len(prompt_logs) >= 1, "Expected at least 1 prompt log"
        print(f"  ✓ Category filtering: {len(prompt_logs)} prompt logs")
        
        error_logs = storage.query_logs(severity="ERROR")
        assert len(error_logs) >= 1, "Expected at least 1 error log"
        print(f"  ✓ Severity filtering: {len(error_logs)} error logs")
        
        print("  ✓ All logger tests passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        # Test core imports
        from utils.ai_logger import LogCategory, LogSeverity, get_ai_logger, AILogger
        from ai_observability.storage import LogStorage
        print("  ✓ Core imports successful")
        
        # Test UI imports (may fail if gradio not available)
        try:
            from ai_observability.ui import AILogViewer, launch_ui
            print("  ✓ UI imports successful")
        except ImportError as e:
            print(f"  ⚠ UI imports skipped (gradio may not be available): {e}")
        
        return True
    except Exception as e:
        print(f"  ✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_severity_filtering():
    """Test severity filtering"""
    print("Testing severity filtering...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create logger with WARNING minimum severity
        logger = AILogger(storage_path=db_path, min_severity=LogSeverity.WARNING)
        
        # Log at different severity levels
        logger.log(
            category=LogCategory.PROMPT,
            message="Debug message",
            severity=LogSeverity.DEBUG
        )
        
        logger.log(
            category=LogCategory.PROMPT,
            message="Info message",
            severity=LogSeverity.INFO
        )
        
        logger.log(
            category=LogCategory.ERROR,
            message="Warning message",
            severity=LogSeverity.WARNING
        )
        
        logger.log(
            category=LogCategory.ERROR,
            message="Error message",
            severity=LogSeverity.ERROR
        )
        
        # Check storage
        storage = LogStorage(db_path)
        all_logs = storage.query_logs()
        
        # Should only have WARNING and ERROR logs
        assert len(all_logs) == 2, f"Expected 2 logs (WARNING and ERROR), got {len(all_logs)}"
        severities = [log['severity'] for log in all_logs]
        assert 'WARNING' in severities, "Expected WARNING log"
        assert 'ERROR' in severities, "Expected ERROR log"
        assert 'DEBUG' not in severities, "Should not have DEBUG log"
        assert 'INFO' not in severities, "Should not have INFO log"
        
        print("  ✓ Severity filtering works correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Severity filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_category_filtering():
    """Test category filtering"""
    print("Testing category filtering...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create logger with only PROMPT and RESPONSE categories enabled
        logger = AILogger(
            storage_path=db_path,
            enabled_categories=[LogCategory.PROMPT, LogCategory.RESPONSE]
        )
        
        # Log different categories
        logger.log_prompt(prompt_text="Test", model_name="test")
        logger.log_response(
            response_text="Test",
            model_name="test",
            token_count_input=1,
            token_count_output=1,
            latency_ms=1.0
        )
        logger.log_tool_call(tool_name="test", tool_args={})
        
        # Check storage
        storage = LogStorage(db_path)
        all_logs = storage.query_logs()
        
        # Should only have PROMPT and RESPONSE logs
        assert len(all_logs) == 2, f"Expected 2 logs, got {len(all_logs)}"
        categories = [log['category'] for log in all_logs]
        assert 'prompt' in categories, "Expected prompt log"
        assert 'response' in categories, "Expected response log"
        assert 'tool_call' not in categories, "Should not have tool_call log"
        
        print("  ✓ Category filtering works correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Category filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    print("=" * 60)
    print("AI Observability System Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    print()
    
    results.append(("Logger Functionality", test_logger()))
    print()
    
    results.append(("Severity Filtering", test_severity_filtering()))
    print()
    
    results.append(("Category Filtering", test_category_filtering()))
    print()
    
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)

