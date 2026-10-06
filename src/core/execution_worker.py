"""
Background execution worker using QThread to keep the UI fully responsive.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from src.core.runner import ExecutionManager, ExecutionResult


class ExecutionWorker(QThread):
    """
    Executes source code in a background thread to prevent UI freezing.
    Emits finished_signal with the complete ExecutionResult upon completion.
    """

    finished_signal = pyqtSignal(ExecutionResult)

    def __init__(
        self,
        code: str,
        file_path: str | None,
        language: str,
        timeout: float = 15.0,
        parent=None,
    ):
        super().__init__(parent)
        self.code = code
        self.file_path = file_path
        self.language = language
        self.timeout = timeout

    def run(self):
        """Runs the execution workflow in the worker thread."""
        result = ExecutionManager.run_code(
            code=self.code,
            file_path=self.file_path,
            language=self.language,
            timeout=self.timeout,
        )
        self.finished_signal.emit(result)
