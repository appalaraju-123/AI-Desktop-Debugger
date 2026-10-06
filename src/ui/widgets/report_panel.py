"""
Report panel widget for displaying and exporting Debugging and Performance Reports.
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from src.report.models import DebugReport
from src.report.exporter import ReportExporter


class ReportPanel(QWidget):
    """
    UI panel presenting consolidated debugging and performance reports.
    Supports in-app rich HTML viewing, clipboard copy, and multi-format file export.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_report: DebugReport | None = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.setSpacing(4)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 2, 4, 2)

        self.title_label = QLabel("📊 Debugging & Performance Report")
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #79c0ff;")
        header_layout.addWidget(self.title_label)

        # Status badge indicator
        self.badge_label = QLabel("IDLE")
        self.badge_label.setStyleSheet(
            """
            background-color: #30363d;
            color: #8b949e;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 6px;
            """
        )
        header_layout.addWidget(self.badge_label)

        header_layout.addStretch()

        # Copy Markdown button
        self.copy_btn = QPushButton("📋 Copy Markdown")
        self.copy_btn.setToolTip("Copy complete markdown report to clipboard")
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }
            QPushButton:hover:enabled {
                background-color: #30363d;
                color: #58a6ff;
            }
            QPushButton:disabled {
                background-color: #161b22;
                color: #484f58;
                border: 1px solid #21262d;
            }
            """
        )
        self.copy_btn.clicked.connect(self._copy_markdown)
        header_layout.addWidget(self.copy_btn)

        # Export Report button
        self.export_btn = QPushButton("💾 Export Report...")
        self.export_btn.setToolTip("Save report to a Markdown, HTML, or Text file")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #238636;
                color: #ffffff;
                border: 1px solid #2ea043;
                border-radius: 4px;
                padding: 2px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover:enabled {
                background-color: #2ea043;
            }
            QPushButton:disabled {
                background-color: #161b22;
                color: #484f58;
                border: 1px solid #21262d;
            }
            """
        )
        self.export_btn.clicked.connect(self.export_report)
        header_layout.addWidget(self.export_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear current report view")
        self.clear_btn.setFixedSize(55, 22)
        self.clear_btn.clicked.connect(self.clear_panel)
        header_layout.addWidget(self.clear_btn)

        main_layout.addLayout(header_layout)

        # Rich text report viewer
        self.viewer = QTextBrowser(self)
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setStyleSheet(
            """
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
            }
            """
        )
        main_layout.addWidget(self.viewer)

        # Initial placeholder
        self._show_placeholder()

    def _show_placeholder(self):
        """Displays instructions when no execution report has been generated yet."""
        self.badge_label.setText("IDLE")
        self.badge_label.setStyleSheet(
            "background-color: #30363d; color: #8b949e; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;"
        )
        self.copy_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.viewer.setHtml(
            """
            <div style="text-align: center; color: #6e7681; margin-top: 50px; font-family: 'Segoe UI', sans-serif;">
                <h3 style="color: #8b949e; margin-bottom: 8px;">No Execution Report Available Yet</h3>
                <p style="font-size: 13px; line-height: 1.6;">
                    Run your program (<strong>F5</strong>) to generate a comprehensive debugging report and performance analysis.<br>
                    If errors occur, use <strong>Explain with AI (F8)</strong> to automatically enrich the report with intelligent diagnostic recommendations.
                </p>
            </div>
            """
        )

    def display_report(self, report: DebugReport):
        """Renders the DebugReport in the viewer and updates toolbar state."""
        self._current_report = report
        self.copy_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Update status badge
        badge_colors = {
            "SUCCESS": ("#238636", "#ffffff"),
            "RUNTIME_ERROR": ("#da3633", "#ffffff"),
            "COMPILATION_ERROR": ("#d29922", "#000000"),
            "TIMEOUT": ("#bd561d", "#ffffff"),
            "ENVIRONMENT_ERROR": ("#8957e5", "#ffffff"),
        }
        bg, fg = badge_colors.get(report.status, ("#30363d", "#c9d1d9"))
        self.badge_label.setText(report.status)
        self.badge_label.setStyleSheet(
            f"background-color: {bg}; color: {fg}; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;"
        )

        # Render HTML version in viewer
        html_content = ReportExporter.to_html(report)
        self.viewer.setHtml(html_content)

    def clear_panel(self):
        """Clears the displayed report."""
        self._current_report = None
        self._show_placeholder()

    def _copy_markdown(self):
        """Copies the Markdown version of the report to the system clipboard."""
        if not self._current_report:
            return

        md_text = ReportExporter.to_markdown(self._current_report)
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(md_text)

        # Visual feedback on copy button
        original_text = self.copy_btn.text()
        self.copy_btn.setText("✓ Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(original_text))

    def export_report(self):
        """Prompts the user to save the report to disk in Markdown, HTML, or Plain Text format."""
        if not self._current_report:
            QMessageBox.information(
                self,
                "No Report to Export",
                "Please execute code (F5) to generate a debugging report before exporting.",
            )
            return

        base_name = os.path.splitext(self._current_report.file_name)[0]
        # Clean illegal characters for file path
        clean_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_")).strip() or "debug_report"
        default_filename = f"{clean_name}_report.md"

        file_filters = (
            "Markdown Document (*.md);;"
            "HTML Document (*.html);;"
            "Plain Text Document (*.txt)"
        )

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Debugging Report",
            default_filename,
            file_filters,
        )

        if not file_path:
            return

        # Determine serialization based on file extension / filter
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".html" or "HTML" in selected_filter:
            content = ReportExporter.to_html(self._current_report)
            if not file_path.lower().endswith(".html"):
                file_path += ".html"
        elif ext == ".txt" or "Plain Text" in selected_filter:
            content = ReportExporter.to_text(self._current_report)
            if not file_path.lower().endswith(".txt"):
                file_path += ".txt"
        else:
            content = ReportExporter.to_markdown(self._current_report)
            if not file_path.lower().endswith(".md"):
                file_path += ".md"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(
                self,
                "Report Exported",
                f"Debugging report exported successfully to:\n{file_path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export debugging report:\n{exc}",
            )
