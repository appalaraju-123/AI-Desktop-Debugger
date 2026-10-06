"""
Background QThread worker for executing AI diagnostic analysis asynchronously.
Ensures the PyQt6 user interface remains responsive during AI processing.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from src.core.error_classifier import ErrorInfo
from src.ai.models import AIAnalysisResult
from src.ai.base_provider import BaseAIProvider, MockAIProvider


class AIAnalysisWorker(QThread):
    """
    Executes AI error analysis in a non-blocking background thread.
    Emits finished_signal with the AIAnalysisResult upon completion.
    """

    finished_signal = pyqtSignal(AIAnalysisResult)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        code: str,
        error_info: ErrorInfo,
        provider: BaseAIProvider | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.code = code
        self.error_info = error_info
        self.provider = provider or MockAIProvider()

    def run(self):
        """Worker thread execution routine."""
        try:
            result = self.provider.analyze_error(self.code, self.error_info)
            self.finished_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))
