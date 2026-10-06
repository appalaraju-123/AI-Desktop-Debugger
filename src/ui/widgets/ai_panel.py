"""
AI Diagnostic and Fix Recommendation Panel widget.
Displays root cause analysis, display-only suggested fixes, debugging guidance,
and optimized alternatives in a clean, modern card-based interface.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QFrame,
    QApplication,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from src.ai.models import AIAnalysisResult


class AIPanel(QWidget):
    """
    UI panel presenting structured AI diagnostic analysis and recommendations.
    Sections:
      1. 🔍 Root Cause
      2. 🛠️ Suggested Fix (display-only code block with copy button)
      3. 💡 Debugging Guidance
      4. ⚡ Optimized Solution
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_fix_text = ""
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.setSpacing(4)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 2, 4, 2)

        self.title_label = QLabel("✨ AI Assistant & Diagnostic Recommendations")
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #9d7cd8;")
        header_layout.addWidget(self.title_label)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding-left: 8px;")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear AI diagnostic output")
        self.clear_btn.setFixedSize(55, 22)
        self.clear_btn.clicked.connect(self.clear_panel)
        header_layout.addWidget(self.clear_btn)

        main_layout.addLayout(header_layout)

        # Scroll area for cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
            }
            """
        )

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.cards_layout = QVBoxLayout(self.content_widget)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(12)

        # Placeholder message
        self.placeholder_label = QLabel(
            "No AI analysis generated yet.\n\n"
            "Run your program (F5). If an error occurs, click '✨ Explain with AI' "
            "in the Output panel or press F8 to view an intelligent diagnosis.",
            self.content_widget,
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #666666; font-size: 13px; padding: 40px;")
        self.cards_layout.addWidget(self.placeholder_label)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def set_loading(self, message: str = "Analyzing error with AI diagnostic engine..."):
        """Puts the panel into a busy / loading state."""
        self._clear_cards()
        self.status_label.setText("Analyzing...")
        self.status_label.setStyleSheet("color: #e5c07b; font-size: 11px; padding-left: 8px;")

        loading_label = QLabel(f"⏳ {message}", self.content_widget)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("color: #e5c07b; font-size: 13px; font-weight: bold; padding: 40px;")
        self.cards_layout.addWidget(loading_label)

    def display_result(self, result: AIAnalysisResult):
        """Renders the AIAnalysisResult into structured diagnostic cards."""
        self._clear_cards()
        self.status_label.setText("Analysis Complete")
        self.status_label.setStyleSheet("color: #89d185; font-size: 11px; padding-left: 8px;")
        self._current_fix_text = result.suggested_fix

        # Card 1: 🔍 Root Cause
        root_cause_card = self._create_card(
            title="🔍 Root Cause Analysis",
            title_color="#ff7b72",
        )
        root_layout = root_cause_card.layout()

        rc_text = QLabel(result.root_cause, root_cause_card)
        rc_text.setWordWrap(True)
        rc_text.setStyleSheet("color: #e6edf3; font-size: 12px; line-height: 1.4;")
        root_layout.addWidget(rc_text)
        self.cards_layout.addWidget(root_cause_card)

        # Card 2: 🛠️ Suggested Fix (Display-Only)
        fix_card = self._create_card(
            title="🛠️ Suggested Fix (Manual Review)",
            title_color="#79c0ff",
        )
        fix_layout = fix_card.layout()

        # Explanation of fix
        if result.explanation:
            exp_label = QLabel(result.explanation, fix_card)
            exp_label.setWordWrap(True)
            exp_label.setStyleSheet("color: #8b949e; font-size: 11px; margin-bottom: 4px;")
            fix_layout.addWidget(exp_label)

        # Code block header with copy button
        code_header = QHBoxLayout()
        code_header.addWidget(QLabel("Suggested Code Correction:"))
        code_header.addStretch()

        self.copy_btn = QPushButton("📋 Copy Fix")
        self.copy_btn.setFixedSize(85, 24)
        self.copy_btn.setToolTip("Copy suggested fix snippet to clipboard")
        self.copy_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
            """
        )
        self.copy_btn.clicked.connect(self._copy_suggested_fix)
        code_header.addWidget(self.copy_btn)
        fix_layout.addLayout(code_header)

        # Read-only code text edit
        fix_edit = QPlainTextEdit(fix_card)
        fix_edit.setReadOnly(True)
        fix_edit.setPlainText(result.suggested_fix)
        fix_font = QFont("Consolas", 10)
        fix_font.setStyleHint(QFont.StyleHint.Monospace)
        fix_edit.setFont(fix_font)
        fix_edit.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #0d1117;
                color: #7ee787;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
            }
            """
        )
        # Size proportionally to lines
        line_count = max(3, min(10, len(result.suggested_fix.splitlines())))
        fix_edit.setFixedHeight(line_count * 20 + 20)
        fix_layout.addWidget(fix_edit)

        self.cards_layout.addWidget(fix_card)

        # Card 3: 💡 Debugging Guidance
        if result.debugging_guidance:
            guidance_card = self._create_card(
                title="💡 Debugging Guidance & Prevention",
                title_color="#d2a8ff",
            )
            g_layout = guidance_card.layout()

            guidance_text = ""
            for tip in result.debugging_guidance:
                guidance_text += f"•  {tip}\n"

            g_label = QLabel(guidance_text.strip(), guidance_card)
            g_label.setWordWrap(True)
            g_label.setStyleSheet("color: #c9d1d9; font-size: 12px; line-height: 1.5;")
            g_layout.addWidget(g_label)
            self.cards_layout.addWidget(guidance_card)

        # Card 4: ⚡ Optimized Solution
        if result.optimized_solution:
            opt_card = self._create_card(
                title="⚡ Optimized / Best-Practice Solution",
                title_color="#56d364",
            )
            opt_layout = opt_card.layout()

            opt_edit = QPlainTextEdit(opt_card)
            opt_edit.setReadOnly(True)
            opt_edit.setPlainText(result.optimized_solution)
            opt_edit.setFont(fix_font)
            opt_edit.setStyleSheet(
                """
                QPlainTextEdit {
                    background-color: #0d1117;
                    color: #d2a8ff;
                    border: 1px solid #30363d;
                    border-radius: 4px;
                    padding: 6px;
                }
                """
            )
            opt_lines = max(2, min(8, len(result.optimized_solution.splitlines())))
            opt_edit.setFixedHeight(opt_lines * 20 + 20)
            opt_layout.addWidget(opt_edit)
            self.cards_layout.addWidget(opt_card)

        # Add stretch at the end to keep cards pinned to top
        self.cards_layout.addStretch()

    def _create_card(self, title: str, title_color: str) -> QFrame:
        """Helper to create a visually consistent card container."""
        card = QFrame(self.content_widget)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title_label = QLabel(title, card)
        t_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        title_label.setFont(t_font)
        title_label.setStyleSheet(f"color: {title_color}; border: none; background: transparent;")
        layout.addWidget(title_label)

        return card

    def _copy_suggested_fix(self):
        """Copies the suggested fix code to the system clipboard."""
        if self._current_fix_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._current_fix_text)
            self.copy_btn.setText("✓ Copied!")
            QTimer.singleShot(2000, lambda: self.copy_btn.setText("📋 Copy Fix"))

    def _clear_cards(self):
        """Removes all cards and widgets from the layout."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def clear_panel(self):
        """Resets the panel back to its default placeholder state."""
        self._clear_cards()
        self._current_fix_text = ""
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding-left: 8px;")

        placeholder = QLabel(
            "No AI analysis generated yet.\n\n"
            "Run your program (F5). If an error occurs, click '✨ Explain with AI' "
            "in the Output panel or press F8 to view an intelligent diagnosis.",
            self.content_widget,
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666666; font-size: 13px; padding: 40px;")
        self.cards_layout.addWidget(placeholder)
