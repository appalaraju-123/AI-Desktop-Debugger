"""
Data models for Debugging Report & Performance Analysis (Module 5).
Reuses existing ExecutionResult, ErrorInfo, and AIAnalysisResult domain models.
"""

from dataclasses import dataclass
from typing import Optional
from src.core.runner import ExecutionResult
from src.core.error_classifier import ErrorInfo
from src.ai.models import AIAnalysisResult


@dataclass
class PerformanceMetrics:
    """
    Performance evaluation metrics derived from process execution data.
    Note: Indicates execution duration characteristics, not a true hardware performance benchmark.
    """

    execution_time: float  # Elapsed time in seconds
    execution_stage: str  # "environment", "compilation", or "execution"
    exit_code: int  # Process return code
    timed_out: bool  # True if execution exceeded timeout
    speed_rating: str  # Simple execution-time indicator: e.g. "Fast (<0.5s)", "Moderate (0.5s-2.0s)", "Slow (>2.0s)"
    memory_note: str = "Memory: Not measured"  # Memory usage is not measured by the current execution engine


@dataclass
class DebugReport:
    """
    Consolidated debugging and execution report encapsulating:
    1. Program and environment information
    2. Execution metrics and performance evaluation
    3. Structured error classification (if an error occurred)
    4. AI-assisted diagnosis and recommendations (if generated)
    5. High-level summary and overall execution status
    """

    # Program / source metadata
    timestamp: str  # Format: "YYYY-MM-DD HH:MM:SS"
    file_name: str  # e.g., "script.py" or "Untitled Buffer"
    file_path: Optional[str]  # Absolute path on disk, or None if in-memory
    language: str  # "Python", "Java", "C", "C++", "JavaScript"
    total_lines: int  # Source line count

    # Execution & Performance
    execution_result: ExecutionResult
    performance: PerformanceMetrics

    # Error diagnostics (None if successful execution)
    error_info: Optional[ErrorInfo] = None

    # AI root-cause analysis & fix (None if not yet requested or not applicable)
    ai_analysis: Optional[AIAnalysisResult] = None

    # Overall outcome
    status: str = "SUCCESS"  # "SUCCESS", "COMPILATION_ERROR", "RUNTIME_ERROR", "TIMEOUT", "ENVIRONMENT_ERROR"
    summary: str = ""  # High-level plain language synthesis
