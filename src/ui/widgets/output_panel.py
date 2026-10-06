"""
Terminal output panel widget for displaying compilation and execution results.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.runner import ExecutionResult
from src.core.error_classifier import ErrorInfo


class OutputPanel(QWidget):
    """
    Console output widget displaying standard output, standard error,
    and process execution statistics.
    """

    explain_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Constructs output header and terminal console text edit."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 2, 4, 2)

        self.title_label = QLabel("Output Console")
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(self.title_label)

        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 11px; padding-left: 8px;")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        self.explain_btn = QPushButton("✨ Explain with AI")
        self.explain_btn.setToolTip("Analyze detected error with AI (F8)")
        self.explain_btn.setEnabled(False)
        self.explain_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2b213a;
                color: #d2a8ff;
                border: 1px solid #7c3aed;
                border-radius: 4px;
                padding: 2px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover:enabled {
                background-color: #3b2d52;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #1f1f1f;
                color: #555555;
                border: 1px solid #333333;
            }
            """
        )
        self.explain_btn.clicked.connect(self.explain_requested.emit)
        header_layout.addWidget(self.explain_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear console output")
        self.clear_btn.setFixedSize(55, 22)
        self.clear_btn.clicked.connect(self.clear_output)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # Terminal text area
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)

        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)

        # Terminal styling
        self.text_edit.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
            }
            """
        )
        layout.addWidget(self.text_edit)

    def clear_output(self):
        """Clears all text in the console."""
        self.text_edit.clear()
        self.status_label.setText("Idle")
        self.explain_btn.setEnabled(False)

    def append_text(self, text: str, color: QColor):
        """Appends colored text to the console viewport."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.insertText(text, fmt)

        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def start_execution(self, language: str):
        """Prepares console for a new execution run."""
        self.clear_output()
        self.explain_btn.setEnabled(False)
        self.status_label.setText(f"Running ({language.capitalize()})...")
        self.append_text(f"[Running {language.capitalize()}...]\n", QColor("#3794ff"))

    def display_result(self, result: ExecutionResult):
        """Formats and displays the complete execution result."""
        # 1. Print Standard Output
        if result.stdout:
            self.append_text(result.stdout, QColor("#d4d4d4"))
            if not result.stdout.endswith("\n"):
                self.append_text("\n", QColor("#d4d4d4"))

        # 2. Print Standard Error
        if result.stderr:
            self.append_text(result.stderr, QColor("#f48771"))
            if not result.stderr.endswith("\n"):
                self.append_text("\n", QColor("#f48771"))

        # 3. Print Process Completion Banner
        if result.timed_out:
            self.status_label.setText("Timed out")
            self.append_text(
                f"\n--- [Execution timed out after {result.execution_time:.3f}s] ---\n",
                QColor("#f48771"),
            )
        elif result.has_error:
            self.status_label.setText(f"Failed ({result.stage})")
            self.append_text(
                f"\n--- [Process exited with code {result.exit_code} ({result.stage} error, {result.execution_time:.3f}s)] ---\n",
                QColor("#e5c07b"),
            )
        else:
            self.status_label.setText("Success")
            self.append_text(
                f"\n--- [Process finished with exit code {result.exit_code} in {result.execution_time:.3f}s] ---\n",
                QColor("#89d185"),
            )

    def display_error_info(self, error_info: ErrorInfo):
        """Displays structured diagnostic and classification information in the output console."""
        self.explain_btn.setEnabled(True)
        loc_str = f"Line {error_info.line_number}" if error_info.line_number else "Location unknown"
        if error_info.column_number:
            loc_str += f", Col {error_info.column_number}"

        banner = (
            f"\n┌──────────────────────── [ERROR CLASSIFIED] ────────────────────────\n"
            f"│ Language:  {error_info.language}\n"
            f"│ Category:  {error_info.error_category}\n"
            f"│ Type:      {error_info.error_type}\n"
            f"│ Severity:  {error_info.severity}\n"
            f"│ Location:  {loc_str}\n"
            f"│ Message:   {error_info.message}\n"
        )
        if error_info.code_context:
            banner += f"│ Context:   {error_info.code_context}\n"
        banner += f"└────────────────────────────────────────────────────────────────────\n"

        severity_colors = {
            "Critical": QColor("#ff5370"),
            "High": QColor("#f48771"),
            "Medium": QColor("#e5c07b"),
            "Low": QColor("#61afef"),
        }
        color = severity_colors.get(error_info.severity, QColor("#f48771"))
        self.append_text(banner, color)
