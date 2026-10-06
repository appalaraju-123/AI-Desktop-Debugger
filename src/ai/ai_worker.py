"""
Background QThread worker for executing AI diagnostic analysis asynchronously.
Ensures the PyQt6 user interface remains responsive during AI processing.
"""

import os
from dotenv import load_dotenv
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.error_classifier import ErrorInfo
from src.ai.models import AIAnalysisResult
from src.ai.base_provider import BaseAIProvider, MockAIProvider
from src.ai.gemini_provider import GeminiProvider


def _resolve_default_provider() -> BaseAIProvider:
    """
    Selects GeminiProvider if GEMINI_API_KEY is available in the environment;
    otherwise gracefully falls back to MockAIProvider.
    """
    load_dotenv()
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if api_key:
        try:
            return GeminiProvider(api_key=api_key)
        except Exception:
            return MockAIProvider()
    return MockAIProvider()


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
        self.provider = provider if provider is not None else _resolve_default_provider()

    def run(self):
        """Worker thread execution routine."""
        try:
            result = self.provider.analyze_error(self.code, self.error_info)
            self.finished_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))
