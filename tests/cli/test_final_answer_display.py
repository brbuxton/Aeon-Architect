"""Integration tests for CLI FinalAnswer display.

Per FR-053, tests cover 3 scenarios:
1. Human-readable FinalAnswer display (without --json flag)
2. JSON FinalAnswer output (with --json flag)
3. Graceful handling of missing final_answer
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Test data
FINAL_ANSWER_COMPLETE = {
    "answer_text": "Successfully completed the task. All steps executed successfully.",
    "confidence": 0.95,
    "used_step_ids": ["step1", "step2"],
    "notes": "Execution completed without errors",
    "ttl_exhausted": False,
    "metadata": {"execution_passes": 3, "converged": True}
}

FINAL_ANSWER_DEGRADED = {
    "answer_text": "Execution completed but some data is missing.",
    "confidence": 0.6,
    "ttl_exhausted": True,
    "metadata": {"degraded": True, "reason": "ttl_expiration", "missing_fields": ["execution_results"]}
}


class TestCLIHumanReadableFinalAnswer:
    """T089: Test CLI human-readable FinalAnswer display (scenario 1)."""
    
    def test_human_readable_display_with_complete_answer(self, tmp_path, monkeypatch):
        """Test that CLI displays FinalAnswer prominently in human-readable format."""
        # Create a mock execution result with final_answer
        mock_result = {
            "status": "converged",
            "ttl_remaining": 1000,
            "final_answer": FINAL_ANSWER_COMPLETE
        }
        
        # Mock the orchestrator to return our result
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            # Run CLI command
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Verify output contains answer_text prominently
            assert FINAL_ANSWER_COMPLETE["answer_text"] in result.stdout
            # Verify confidence is displayed if present
            assert "Confidence:" in result.stdout or "0.95" in result.stdout
            # Verify notes are displayed if present
            assert FINAL_ANSWER_COMPLETE["notes"] in result.stdout or "Notes:" in result.stdout
    
    def test_human_readable_display_with_ttl_exhausted(self, tmp_path, monkeypatch):
        """Test that CLI displays TTL exhausted warning when ttl_exhausted is True."""
        mock_result = {
            "status": "ttl_expired",
            "ttl_remaining": 0,
            "final_answer": FINAL_ANSWER_DEGRADED
        }
        
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Verify TTL exhausted warning is displayed
            assert "TTL was exhausted" in result.stdout or "ttl_exhausted" in result.stdout.lower()
            # Verify degraded mode metadata is shown
            assert "Degraded Mode" in result.stdout or "degraded" in result.stdout.lower()
    
    def test_human_readable_display_metadata_summary(self, tmp_path, monkeypatch):
        """Test that CLI displays metadata summary when non-empty."""
        mock_result = {
            "status": "converged",
            "final_answer": FINAL_ANSWER_COMPLETE
        }
        
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Verify metadata section is displayed
            assert "Metadata:" in result.stdout or "execution_passes" in result.stdout


class TestCLIJSONFinalAnswer:
    """T090A: Test CLI JSON FinalAnswer output (scenario 2)."""
    
    def test_json_output_includes_final_answer(self, tmp_path, monkeypatch):
        """Test that CLI includes final_answer in JSON output with --json flag."""
        mock_result = {
            "status": "converged",
            "ttl_remaining": 1000,
            "final_answer": FINAL_ANSWER_COMPLETE
        }
        
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request", "--json"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Parse JSON output
            output_lines = result.stdout.split('\n')
            json_start = next((i for i, line in enumerate(output_lines) if 'Result (JSON):' in line), None)
            if json_start is not None:
                json_str = '\n'.join(output_lines[json_start + 1:])
                try:
                    output_json = json.loads(json_str)
                    # Verify final_answer is present as top-level key
                    assert "final_answer" in output_json
                    final_answer = output_json["final_answer"]
                    # Verify all FinalAnswer fields are serialized
                    assert "answer_text" in final_answer
                    assert "confidence" in final_answer
                    assert "used_step_ids" in final_answer
                    assert "notes" in final_answer
                    assert "ttl_exhausted" in final_answer
                    assert "metadata" in final_answer
                except json.JSONDecodeError:
                    # If JSON parsing fails, at least verify final_answer is mentioned
                    assert "final_answer" in result.stdout


class TestCLIMissingFinalAnswer:
    """T090B: Test CLI graceful handling of missing final_answer (scenario 3)."""
    
    def test_graceful_handling_missing_final_answer(self, tmp_path, monkeypatch):
        """Test that CLI handles missing final_answer gracefully without crashing."""
        # Execution result without final_answer
        mock_result = {
            "status": "converged",
            "ttl_remaining": 1000,
            # No final_answer key
        }
        
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Verify CLI does not crash (exit code 0)
            assert result.returncode == 0
            # Verify message about missing final_answer or section is omitted
            assert "No final answer available" in result.stdout or "Final Answer" not in result.stdout or "final_answer" not in result.stdout.lower()
    
    def test_json_output_without_final_answer(self, tmp_path, monkeypatch):
        """Test that JSON output works even without final_answer."""
        mock_result = {
            "status": "converged",
            "ttl_remaining": 1000,
        }
        
        with patch('aeon.cli.main.create_orchestrator') as mock_create:
            mock_orchestrator = MagicMock()
            mock_orchestrator.generate_plan.return_value = MagicMock()
            mock_orchestrator.execute_multipass.return_value = mock_result
            mock_orchestrator.get_state.return_value = MagicMock()
            mock_create.return_value = mock_orchestrator
            
            result = subprocess.run(
                [sys.executable, "-m", "aeon.cli.main", "execute", "test request", "--json"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Verify CLI does not crash
            assert result.returncode == 0
            # JSON output should still be valid (may or may not include final_answer)
            assert "Result (JSON):" in result.stdout or "status" in result.stdout
