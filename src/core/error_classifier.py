"""
Error detection and classification engine for the AI-Based Intelligent Desktop Debugger.
Extracts structured diagnostic data (error type, location, severity, and category)
from multi-language compiler and runtime execution results.
"""

from dataclasses import dataclass
import re
from src.core.runner import ExecutionResult


@dataclass
class ErrorInfo:
    """Structured diagnostic information extracted from an execution failure."""

    language: str  # "Python", "Java", "C", "C++", "JavaScript"
    error_category: str  # "Compilation Error", "Syntax Error", "Runtime Error", "Logical Error", "Timeout Error", "Environment Error"
    error_type: str  # e.g., "ZeroDivisionError", "NullPointerException", "IncompatibleTypes"
    message: str  # e.g., "division by zero"
    line_number: int | None = None
    column_number: int | None = None
    severity: str = "High"  # "Critical", "High", "Medium", "Low"
    code_context: str = ""  # The source line where the error occurred
    raw_details: str = ""  # Traceback or relevant compiler output


class ErrorClassifier:
    """
    Parses ExecutionResult and source code to classify errors and pinpoint locations.
    Supports Python, Java, C, C++, and JavaScript.
    """

    LANGUAGE_NAMES = {
        "python": "Python",
        "java": "Java",
        "c": "C",
        "cpp": "C++",
        "javascript": "JavaScript",
    }

    @classmethod
    def classify(
        cls,
        result: ExecutionResult,
        code: str,
        language: str,
    ) -> ErrorInfo | None:
        """
        Classifies an execution result into structured ErrorInfo.
        Returns None if no error or assertion failure occurred.
        """
        # Rule: Programs with exit code 0 and no timeout or error flag return None
        if not result.has_error and not result.timed_out and result.exit_code == 0:
            return None

        clean_lang = language.lower().strip()
        display_lang = cls.LANGUAGE_NAMES.get(clean_lang, clean_lang.capitalize())

        # 1. Handle Timeout Errors (Infinite loops / hanging I/O)
        if result.timed_out:
            return ErrorInfo(
                language=display_lang,
                error_category="Timeout Error",
                error_type="ExecutionTimeout",
                message=f"Process timed out after {result.execution_time:.2f}s (possible infinite loop or blocking I/O).",
                severity="High",
                raw_details=result.stderr or result.stdout,
            )

        # 2. Handle Toolchain / Environment Errors
        if result.stage == "environment":
            first_line = result.stderr.splitlines()[0] if result.stderr else "Compiler or runtime environment not found."
            return ErrorInfo(
                language=display_lang,
                error_category="Environment Error",
                error_type="MissingToolchain",
                message=first_line,
                severity="High",
                raw_details=result.stderr,
            )

        # 3. Language-Specific Parsing
        stderr = result.stderr or ""
        stdout = result.stdout or ""

        if clean_lang == "python":
            return cls._classify_python(stderr, stdout, code)
        elif clean_lang == "java":
            return cls._classify_java(result.stage, stderr, stdout, code)
        elif clean_lang in ("c", "cpp"):
            return cls._classify_c_cpp(result.stage, stderr, stdout, code, display_lang)
        elif clean_lang == "javascript":
            return cls._classify_javascript(stderr, stdout, code)
        else:
            return cls._classify_generic(result, code, display_lang)

    @classmethod
    def _extract_code_context(cls, code: str, line_number: int | None) -> str:
        """Helper to extract the specific line of code if available."""
        if not code or line_number is None or line_number < 1:
            return ""
        lines = code.splitlines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""

    @classmethod
    def _classify_python(cls, stderr: str, stdout: str, code: str) -> ErrorInfo:
        """Parses Python tracebacks and syntax errors."""
        raw_text = stderr if stderr.strip() else stdout
        line_number = None
        column_number = None
        error_type = "RuntimeError"
        message = "Unknown Python runtime error"
        category = "Runtime Error"
        severity = "High"

        # Look for SyntaxError / IndentationError first
        syntax_match = re.search(r'File ".*?", line (\d+)(?:, in .*)?\n(?:\s*(.*?)\n\s*(\^+))?', raw_text)
        if "SyntaxError:" in raw_text or "IndentationError:" in raw_text:
            category = "Syntax Error"
            error_match = re.search(r"(SyntaxError|IndentationError):\s*(.*)", raw_text)
            if error_match:
                error_type = error_match.group(1)
                message = error_match.group(2).strip()

            line_match = re.search(r'File ".*?", line (\d+)', raw_text)
            if line_match:
                line_number = int(line_match.group(1))

            # Column from caret line
            caret_match = re.search(r"\n\s*(\^+)", raw_text)
            if caret_match:
                column_number = len(caret_match.group(0).splitlines()[-1])
        else:
            # Runtime Traceback
            # Find the last "File ..., line X" reference (user's code or deepest call)
            file_matches = list(re.finditer(r'File ".*?", line (\d+)(?:, in (.+))?', raw_text))
            if file_matches:
                last_frame = file_matches[-1]
                line_number = int(last_frame.group(1))

            # Find exception class and message on the last line
            exc_match = re.search(r"^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning|Interrupt))(?::\s*(.*))?$", raw_text, re.MULTILINE)
            if exc_match:
                error_type = exc_match.group(1)
                message = (exc_match.group(2) or "").strip()
            else:
                # Fallback to last non-empty line
                non_empty = [line.strip() for line in raw_text.splitlines() if line.strip()]
                if non_empty:
                    message = non_empty[-1]

            # Categorize specific types
            if error_type == "AssertionError":
                category = "Logical Error"
                severity = "Medium"
                if not message:
                    message = "Assertion condition failed (logical test failure)."
            elif error_type in ("MemoryError", "RecursionError", "SystemError"):
                category = "Runtime Error"
                severity = "Critical"
            else:
                category = "Runtime Error"
                severity = "High"

        code_context = cls._extract_code_context(code, line_number)

        return ErrorInfo(
            language="Python",
            error_category=category,
            error_type=error_type,
            message=message,
            line_number=line_number,
            column_number=column_number,
            severity=severity,
            code_context=code_context,
            raw_details=raw_text.strip(),
        )

    @classmethod
    def _classify_java(cls, stage: str, stderr: str, stdout: str, code: str) -> ErrorInfo:
        """Parses Java javac compilation errors and runtime exceptions."""
        raw_text = stderr if stderr.strip() else stdout
        line_number = None
        column_number = None
        code_context = ""

        # 1. Compilation Stage (javac)
        if stage == "compilation" or "error:" in raw_text:
            # Pattern: <filename>:<line>: error: <message>
            compile_match = re.search(r"([^:\n]+):(\d+):\s*error:\s*(.*)", raw_text)
            if compile_match:
                line_number = int(compile_match.group(2))
                raw_msg = compile_match.group(3).strip()
            else:
                raw_msg = "Java compilation error"

            # Check for caret line to get column
            caret_match = re.search(r"\n(\s*)\^", raw_text)
            if caret_match:
                column_number = len(caret_match.group(1)) + 1

            # Categorize compilation error
            if "';' expected" in raw_msg or "')' expected" in raw_msg or "illegal start" in raw_msg:
                category = "Syntax Error"
                error_type = "SyntaxError"
            elif "incompatible types" in raw_msg:
                category = "Compilation Error"
                error_type = "IncompatibleTypes"
            elif "cannot find symbol" in raw_msg:
                category = "Compilation Error"
                error_type = "UnresolvedSymbol"
            else:
                category = "Compilation Error"
                error_type = "CompilationError"

            return ErrorInfo(
                language="Java",
                error_category=category,
                error_type=error_type,
                message=raw_msg,
                line_number=line_number,
                column_number=column_number,
                severity="High",
                code_context=cls._extract_code_context(code, line_number),
                raw_details=raw_text.strip(),
            )

        # 2. Runtime Stage (java)
        # Exception in thread "main" java.lang.NullPointerException: message
        #     at Main.main(Main.java:5)
        exc_match = re.search(r'Exception in thread "[^"]+"\s+([\w.$]+)(?::\s*(.*))?', raw_text)
        if exc_match:
            full_exc = exc_match.group(1)
            error_type = full_exc.split(".")[-1]
            message = (exc_match.group(2) or "").strip()
            if not message:
                message = f"Unhandled {error_type}"
        else:
            error_type = "RuntimeError"
            message = "Java program crashed during execution"

        # Frame location
        frame_match = re.search(r"\bat\s+[\w.$]+\([^:]+:(\d+)\)", raw_text)
        if frame_match:
            line_number = int(frame_match.group(1))

        if error_type == "AssertionError":
            category = "Logical Error"
            severity = "Medium"
            if not message or message == f"Unhandled {error_type}":
                message = "Java assertion condition evaluated to false."
        elif error_type in ("OutOfMemoryError", "StackOverflowError"):
            category = "Runtime Error"
            severity = "Critical"
        else:
            category = "Runtime Error"
            severity = "High"

        return ErrorInfo(
            language="Java",
            error_category=category,
            error_type=error_type,
            message=message,
            line_number=line_number,
            column_number=column_number,
            severity=severity,
            code_context=cls._extract_code_context(code, line_number),
            raw_details=raw_text.strip(),
        )

    @classmethod
    def _classify_c_cpp(cls, stage: str, stderr: str, stdout: str, code: str, language: str) -> ErrorInfo:
        """Parses GCC/G++ compilation diagnostics and C/C++ runtime faults."""
        raw_text = stderr if stderr.strip() else stdout
        line_number = None
        column_number = None

        # 1. Compilation Stage
        if stage == "compilation" or re.search(r":\d+:\d+:\s*(fatal\s+)?error:", raw_text):
            # Pattern: <filename>:<line>:<col>: error: <message>
            match = re.search(r":(\d+):(\d+):\s*(?:fatal\s+)?error:\s*(.*)", raw_text)
            if match:
                line_number = int(match.group(1))
                column_number = int(match.group(2))
                raw_msg = match.group(3).strip()
            else:
                fallback_match = re.search(r":(\d+):\s*(?:fatal\s+)?error:\s*(.*)", raw_text)
                if fallback_match:
                    line_number = int(fallback_match.group(1))
                    raw_msg = fallback_match.group(2).strip()
                else:
                    raw_msg = f"{language} compilation failure"

            # Check if syntax or semantic
            if "expected" in raw_msg or "undeclared" in raw_msg or "syntax error" in raw_msg:
                category = "Syntax Error" if "expected" in raw_msg else "Compilation Error"
                error_type = "SyntaxError" if "expected" in raw_msg else "UndeclaredIdentifier"
            else:
                category = "Compilation Error"
                error_type = "CompilationError"

            return ErrorInfo(
                language=language,
                error_category=category,
                error_type=error_type,
                message=raw_msg,
                line_number=line_number,
                column_number=column_number,
                severity="High",
                code_context=cls._extract_code_context(code, line_number),
                raw_details=raw_text.strip(),
            )

        # 2. Runtime Stage
        # Check for Segmentation fault / memory errors
        if "Segmentation fault" in raw_text or "SIGSEGV" in raw_text or "core dumped" in raw_text:
            return ErrorInfo(
                language=language,
                error_category="Runtime Error",
                error_type="SegmentationFault",
                message="Memory access violation (Segmentation fault / SIGSEGV).",
                severity="Critical",
                code_context="",
                raw_details=raw_text.strip(),
            )

        # Check for Assertion failure
        assert_match = re.search(r"Assertion `(.*?)' failed", raw_text)
        if assert_match:
            line_match = re.search(r":(\d+):", raw_text)
            if line_match:
                line_number = int(line_match.group(1))
            return ErrorInfo(
                language=language,
                error_category="Logical Error",
                error_type="AssertionFailure",
                message=f"Assertion failed: {assert_match.group(1)}",
                line_number=line_number,
                severity="Medium",
                code_context=cls._extract_code_context(code, line_number),
                raw_details=raw_text.strip(),
            )

        return ErrorInfo(
            language=language,
            error_category="Runtime Error",
            error_type="RuntimeError",
            message=raw_text.strip() or f"Process terminated with abnormal exit code.",
            severity="High",
            code_context="",
            raw_details=raw_text.strip(),
        )

    @classmethod
    def _classify_javascript(cls, stderr: str, stdout: str, code: str) -> ErrorInfo:
        """Parses Node.js runtime exceptions and syntax errors."""
        raw_text = stderr if stderr.strip() else stdout
        line_number = None
        column_number = None
        error_type = "RuntimeError"
        message = "Unknown JavaScript execution error"
        category = "Runtime Error"
        severity = "High"

        # Line/Column locator: filename:line:col or filename:line
        loc_match = re.search(r":(\d+)(?::(\d+))?", raw_text)
        if loc_match:
            line_number = int(loc_match.group(1))
            if loc_match.group(2):
                column_number = int(loc_match.group(2))

        # Check for error name and message
        err_match = re.search(r"([A-Za-z0-9_]+Error)(?: \[.*?\])?: (.*)", raw_text)
        if err_match:
            error_type = err_match.group(1)
            message = err_match.group(2).strip()

        if error_type == "SyntaxError":
            category = "Syntax Error"
            severity = "High"
        elif error_type in ("AssertionError", "ERR_ASSERTION"):
            category = "Logical Error"
            error_type = "AssertionError"
            severity = "Medium"
        elif error_type in ("RangeError", "ReferenceError", "TypeError"):
            category = "Runtime Error"
            severity = "High"

        return ErrorInfo(
            language="JavaScript",
            error_category=category,
            error_type=error_type,
            message=message,
            line_number=line_number,
            column_number=column_number,
            severity=severity,
            code_context=cls._extract_code_context(code, line_number),
            raw_details=raw_text.strip(),
        )

    @classmethod
    def _classify_generic(cls, result: ExecutionResult, code: str, language: str) -> ErrorInfo:
        """Fallback classifier for unhandled or unknown languages."""
        message = result.stderr.strip() if result.stderr else f"Execution failed with exit code {result.exit_code}."
        return ErrorInfo(
            language=language,
            error_category="Runtime Error",
            error_type="ExecutionError",
            message=message.splitlines()[0] if message else "Execution failed",
            severity="High",
            raw_details=result.stderr,
        )
