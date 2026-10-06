"""
Compilation and execution engine for the AI-Based Intelligent Desktop Debugger.
Provides language-independent execution strategies for Python, C, C++, Java, and JavaScript.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


@dataclass
class ExecutionResult:
    """Encapsulates the complete result of a program compilation and execution cycle."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    stage: str = "execution"  # "environment", "compilation", or "execution"
    has_error: bool = False
    timed_out: bool = False


class BaseRunner(ABC):
    """Abstract base strategy for language-specific compilation and execution."""

    @abstractmethod
    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        """Executes the given source file and returns an ExecutionResult."""
        pass


class PythonRunner(BaseRunner):
    """Executes Python code using the active Python interpreter."""

    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        # Use active virtual environment interpreter if available, otherwise current sys.executable
        interpreter = sys.executable

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        start_time = time.perf_counter()
        try:
            process = subprocess.run(
                [interpreter, "-u", file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=os.path.dirname(os.path.abspath(file_path)),
            )
            elapsed = time.perf_counter() - start_time
            has_error = process.returncode != 0

            return ExecutionResult(
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
                execution_time=elapsed,
                stage="execution",
                has_error=has_error,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start_time
            stdout_str = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode() if exc.stdout else "")
            stderr_str = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode() if exc.stderr else "")
            timeout_msg = f"Execution timed out after {timeout} seconds."
            full_stderr = f"{stderr_str}\n{timeout_msg}".strip()

            return ExecutionResult(
                stdout=stdout_str,
                stderr=full_stderr,
                exit_code=-1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
                timed_out=True,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                stderr=f"Runtime execution error: {exc}",
                exit_code=1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
            )


class CRunner(BaseRunner):
    """Compiles and executes C source files using GCC."""

    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        # Check compiler availability
        if not shutil.which("gcc"):
            return ExecutionResult(
                stderr=(
                    "Error: GCC compiler ('gcc') not found on system PATH.\n"
                    "Please install MinGW-w64 or GCC and ensure 'gcc' is available in your PATH environment variable."
                ),
                exit_code=127,
                stage="environment",
                has_error=True,
            )

        file_dir = os.path.dirname(os.path.abspath(file_path))
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_exe = os.path.join(file_dir, f"{base_name}_exec.exe" if os.name == "nt" else f"{base_name}_exec")

        # 1. Compilation Phase
        compile_start = time.perf_counter()
        try:
            compile_process = subprocess.run(
                ["gcc", file_path, "-o", output_exe],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
        except Exception as exc:
            return ExecutionResult(
                stderr=f"Compilation failed to start: {exc}",
                exit_code=1,
                stage="compilation",
                has_error=True,
            )

        if compile_process.returncode != 0:
            compile_time = time.perf_counter() - compile_start
            return ExecutionResult(
                stdout=compile_process.stdout,
                stderr=compile_process.stderr,
                exit_code=compile_process.returncode,
                execution_time=compile_time,
                stage="compilation",
                has_error=True,
            )

        # 2. Execution Phase
        exec_start = time.perf_counter()
        try:
            run_process = subprocess.run(
                [output_exe],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stdout=run_process.stdout,
                stderr=run_process.stderr,
                exit_code=run_process.returncode,
                execution_time=elapsed,
                stage="execution",
                has_error=run_process.returncode != 0,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - exec_start
            stdout_str = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode() if exc.stdout else "")
            stderr_str = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode() if exc.stderr else "")
            return ExecutionResult(
                stdout=stdout_str,
                stderr=f"{stderr_str}\nExecution timed out after {timeout} seconds.".strip(),
                exit_code=-1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
                timed_out=True,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stderr=f"Runtime error: {exc}",
                exit_code=1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
            )
        finally:
            if os.path.exists(output_exe):
                try:
                    os.remove(output_exe)
                except OSError:
                    pass


class CppRunner(BaseRunner):
    """Compiles and executes C++ source files using G++."""

    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        # Check compiler availability
        if not shutil.which("g++"):
            return ExecutionResult(
                stderr=(
                    "Error: G++ compiler ('g++') not found on system PATH.\n"
                    "Please install MinGW-w64 or GCC/G++ and ensure 'g++' is available in your PATH environment variable."
                ),
                exit_code=127,
                stage="environment",
                has_error=True,
            )

        file_dir = os.path.dirname(os.path.abspath(file_path))
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_exe = os.path.join(file_dir, f"{base_name}_exec.exe" if os.name == "nt" else f"{base_name}_exec")

        # 1. Compilation Phase
        compile_start = time.perf_counter()
        try:
            compile_process = subprocess.run(
                ["g++", file_path, "-o", output_exe],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
        except Exception as exc:
            return ExecutionResult(
                stderr=f"Compilation failed to start: {exc}",
                exit_code=1,
                stage="compilation",
                has_error=True,
            )

        if compile_process.returncode != 0:
            compile_time = time.perf_counter() - compile_start
            return ExecutionResult(
                stdout=compile_process.stdout,
                stderr=compile_process.stderr,
                exit_code=compile_process.returncode,
                execution_time=compile_time,
                stage="compilation",
                has_error=True,
            )

        # 2. Execution Phase
        exec_start = time.perf_counter()
        try:
            run_process = subprocess.run(
                [output_exe],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stdout=run_process.stdout,
                stderr=run_process.stderr,
                exit_code=run_process.returncode,
                execution_time=elapsed,
                stage="execution",
                has_error=run_process.returncode != 0,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - exec_start
            stdout_str = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode() if exc.stdout else "")
            stderr_str = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode() if exc.stderr else "")
            return ExecutionResult(
                stdout=stdout_str,
                stderr=f"{stderr_str}\nExecution timed out after {timeout} seconds.".strip(),
                exit_code=-1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
                timed_out=True,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stderr=f"Runtime error: {exc}",
                exit_code=1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
            )
        finally:
            if os.path.exists(output_exe):
                try:
                    os.remove(output_exe)
                except OSError:
                    pass


class JavaRunner(BaseRunner):
    """Compiles and executes Java source files using JDK (javac and java)."""

    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        if not shutil.which("javac") or not shutil.which("java"):
            return ExecutionResult(
                stderr=(
                    "Error: Java Development Kit (JDK) 'javac' or 'java' not found on system PATH.\n"
                    "Please install the JDK and ensure both 'javac' and 'java' are in your PATH."
                ),
                exit_code=127,
                stage="environment",
                has_error=True,
            )

        file_dir = os.path.dirname(os.path.abspath(file_path))

        # 1. Determine Main Class Name
        class_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            match = re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+([A-Za-z0-9_$]+)", source)
            if match:
                class_name = match.group(1)
            else:
                match_any = re.search(r"\bclass\s+([A-Za-z0-9_$]+)", source)
                if match_any:
                    class_name = match_any.group(1)
        except Exception:
            pass

        # 2. Compilation Phase
        compile_start = time.perf_counter()
        try:
            compile_process = subprocess.run(
                ["javac", "-d", file_dir, file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
        except Exception as exc:
            return ExecutionResult(
                stderr=f"Java compilation failed to start: {exc}",
                exit_code=1,
                stage="compilation",
                has_error=True,
            )

        if compile_process.returncode != 0:
            compile_time = time.perf_counter() - compile_start
            return ExecutionResult(
                stdout=compile_process.stdout,
                stderr=compile_process.stderr,
                exit_code=compile_process.returncode,
                execution_time=compile_time,
                stage="compilation",
                has_error=True,
            )

        # 3. Execution Phase
        exec_start = time.perf_counter()
        try:
            run_process = subprocess.run(
                ["java", "-cp", file_dir, class_name],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stdout=run_process.stdout,
                stderr=run_process.stderr,
                exit_code=run_process.returncode,
                execution_time=elapsed,
                stage="execution",
                has_error=run_process.returncode != 0,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - exec_start
            stdout_str = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode() if exc.stdout else "")
            stderr_str = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode() if exc.stderr else "")
            return ExecutionResult(
                stdout=stdout_str,
                stderr=f"{stderr_str}\nExecution timed out after {timeout} seconds.".strip(),
                exit_code=-1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
                timed_out=True,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - exec_start
            return ExecutionResult(
                stderr=f"Runtime error: {exc}",
                exit_code=1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
            )
        finally:
            class_file = os.path.join(file_dir, f"{class_name}.class")
            if os.path.exists(class_file):
                try:
                    os.remove(class_file)
                except OSError:
                    pass


class JavaScriptRunner(BaseRunner):
    """Executes JavaScript source files using Node.js."""

    def run(self, file_path: str, timeout: float = 15.0) -> ExecutionResult:
        if not shutil.which("node"):
            return ExecutionResult(
                stderr=(
                    "Error: Node.js runtime ('node') not found on system PATH.\n"
                    "Please install Node.js from https://nodejs.org and ensure 'node' is in your PATH."
                ),
                exit_code=127,
                stage="environment",
                has_error=True,
            )

        file_dir = os.path.dirname(os.path.abspath(file_path))
        start_time = time.perf_counter()
        try:
            process = subprocess.run(
                ["node", file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=file_dir,
            )
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
                execution_time=elapsed,
                stage="execution",
                has_error=process.returncode != 0,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start_time
            stdout_str = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode() if exc.stdout else "")
            stderr_str = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode() if exc.stderr else "")
            return ExecutionResult(
                stdout=stdout_str,
                stderr=f"{stderr_str}\nExecution timed out after {timeout} seconds.".strip(),
                exit_code=-1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
                timed_out=True,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                stderr=f"Runtime error: {exc}",
                exit_code=1,
                execution_time=elapsed,
                stage="execution",
                has_error=True,
            )


class ExecutionManager:
    """Coordinates code preparation, runner selection, and execution."""

    RUNNERS: dict[str, type[BaseRunner]] = {
        "python": PythonRunner,
        "c": CRunner,
        "cpp": CppRunner,
        "java": JavaRunner,
        "javascript": JavaScriptRunner,
    }

    EXTENSION_MAP = {
        "python": ".py",
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java",
        "javascript": ".js",
    }

    @classmethod
    def run_code(
        cls,
        code: str,
        file_path: str | None,
        language: str,
        timeout: float = 15.0,
    ) -> ExecutionResult:
        """
        Prepares the source code on disk and dispatches execution to the corresponding runner.
        """
        clean_lang = language.lower().strip()
        runner_cls = cls.RUNNERS.get(clean_lang, PythonRunner)
        runner = runner_cls()

        # Check for empty code
        if not code.strip():
            return ExecutionResult(
                stderr="Execution aborted: Code buffer is empty.",
                exit_code=1,
                stage="environment",
                has_error=True,
            )

        # Prepare source file on disk
        temp_dir = None
        target_file = file_path

        # If unsaved/untitled, or needs temporary sandbox
        if not target_file or not os.path.exists(target_file):
            temp_dir = tempfile.mkdtemp(prefix="dbg_exec_")
            ext = cls.EXTENSION_MAP.get(clean_lang, ".txt")

            # In Java, determine filename from class declaration if possible
            if clean_lang == "java":
                match = re.search(r"\bpublic\s+class\s+([A-Za-z0-9_$]+)", code)
                class_name = match.group(1) if match else "Main"
                target_file = os.path.join(temp_dir, f"{class_name}{ext}")
            else:
                target_file = os.path.join(temp_dir, f"main{ext}")

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(code)
        else:
            # If the file exists on disk, synchronize it with the current buffer
            try:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(code)
            except Exception as exc:
                return ExecutionResult(
                    stderr=f"Could not synchronize file to disk: {exc}",
                    exit_code=1,
                    stage="environment",
                    has_error=True,
                )

        try:
            return runner.run(target_file, timeout=timeout)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
