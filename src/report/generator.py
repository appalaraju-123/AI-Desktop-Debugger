"""
Report generator for Module 5: Debugging Report & Performance Analysis.
Synthesizes ExecutionResult, ErrorInfo, and AIAnalysisResult into a cohesive DebugReport.
"""

from datetime import datetime
import os
from typing import Optional

from src.core.runner import ExecutionResult
from src.core.error_classifier import ErrorInfo
from src.ai.models import AIAnalysisResult
from src.report.models import PerformanceMetrics, DebugReport


class ReportGenerator:
    """
    Constructs structured debugging reports and performs execution-time performance analysis.
    """

    LANGUAGE_NAMES = {
        "python": "Python",
        "java": "Java",
        "c": "C",
        "cpp": "C++",
        "javascript": "JavaScript",
    }

    @classmethod
    def evaluate_performance(cls, result: ExecutionResult) -> PerformanceMetrics:
        """
        Derives an execution-time performance evaluation from process execution results.
        Note: The speed rating is a simple execution-time indicator, not a true hardware benchmark.
        """
        elapsed = result.execution_time

        if result.timed_out:
            speed_rating = "Timeout Exceeded (>15.0s) [Execution-time indicator]"
        elif elapsed < 0.5:
            speed_rating = "Fast (<0.5s) [Execution-time indicator]"
        elif elapsed <= 2.0:
            speed_rating = "Moderate (0.5s–2.0s) [Execution-time indicator]"
        else:
            speed_rating = "Slow (>2.0s) [Execution-time indicator]"

        return PerformanceMetrics(
            execution_time=elapsed,
            execution_stage=result.stage,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            speed_rating=speed_rating,
            memory_note="Memory: Not measured",
        )

    @classmethod
    def determine_status_and_summary(
        cls,
        result: ExecutionResult,
        error_info: Optional[ErrorInfo],
        language: str,
    ) -> tuple[str, str]:
        """
        Synthesizes execution status and an overall summary message.
        Handles successful runs, compilation errors, runtime errors, and timeouts.
        """
        display_lang = cls.LANGUAGE_NAMES.get(language.lower(), language.capitalize())

        if result.timed_out:
            status = "TIMEOUT"
            summary = (
                f"Execution timed out after {result.execution_time:.2f}s. "
                f"The process was terminated to prevent system hanging (possible infinite loop or blocking I/O)."
            )
        elif result.has_error:
            if result.stage == "compilation":
                status = "COMPILATION_ERROR"
                err_type = error_info.error_type if error_info else "Compilation Error"
                loc = f" at line {error_info.line_number}" if (error_info and error_info.line_number) else ""
                summary = (
                    f"Compilation failed in {display_lang} compiler with exit code {result.exit_code} "
                    f"({err_type}{loc}) after {result.execution_time:.3f}s. Runtime execution was not reached."
                )
            elif result.stage == "environment":
                status = "ENVIRONMENT_ERROR"
                err_msg = result.stderr.strip() or "Environment / toolchain configuration error"
                summary = f"Execution aborted during environment preparation: {err_msg}."
            else:
                status = "RUNTIME_ERROR"
                err_type = error_info.error_type if error_info else "Runtime Error"
                loc = f" at line {error_info.line_number}" if (error_info and error_info.line_number) else ""
                summary = (
                    f"Program terminated abnormally with exit code {result.exit_code} "
                    f"({err_type}{loc}) after {result.execution_time:.3f}s."
                )
        else:
            status = "SUCCESS"
            summary = (
                f"Program executed successfully in {result.execution_time:.3f}s "
                f"with exit code 0. No errors or exceptions detected."
            )

        return status, summary

    @classmethod
    def build_report(
        cls,
        result: ExecutionResult,
        error_info: Optional[ErrorInfo],
        code: str,
        file_path: Optional[str],
        language: str,
        ai_analysis: Optional[AIAnalysisResult] = None,
    ) -> DebugReport:
        """
        Assembles a complete DebugReport instance from execution, diagnostic, and AI data.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path) if file_path else "Untitled Buffer"
        total_lines = len(code.splitlines()) if code else 0
        display_lang = cls.LANGUAGE_NAMES.get(language.lower(), language.capitalize())

        performance = cls.evaluate_performance(result)
        status, summary = cls.determine_status_and_summary(result, error_info, display_lang)

        return DebugReport(
            timestamp=timestamp,
            file_name=file_name,
            file_path=file_path,
            language=display_lang,
            total_lines=total_lines,
            execution_result=result,
            performance=performance,
            error_info=error_info,
            ai_analysis=ai_analysis,
            status=status,
            summary=summary,
        )

    @classmethod
    def attach_ai_analysis(cls, report: DebugReport, ai_analysis: AIAnalysisResult) -> DebugReport:
        """
        Attaches AI diagnosis and recommendations to an existing report.
        """
        report.ai_analysis = ai_analysis
        return report
