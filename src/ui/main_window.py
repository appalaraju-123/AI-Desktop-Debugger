"""
Main application window for the AI-Based Intelligent Desktop Debugger.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QPushButton,
    QComboBox,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QKeySequence, QColor
from src.ui.widgets.code_editor import CodeEditor
from src.ui.widgets.output_panel import OutputPanel
from src.ui.widgets.ai_panel import AIPanel
from src.core.validator import CodeValidator
from src.core.execution_worker import ExecutionWorker
from src.core.runner import ExecutionResult
from src.core.error_classifier import ErrorClassifier, ErrorInfo
from src.ai.ai_worker import AIAnalysisWorker
from src.ai.models import AIAnalysisResult
from src.ui.widgets.report_panel import ReportPanel
from src.report.models import DebugReport
from src.report.generator import ReportGenerator


class MainWindow(QMainWindow):
    """
    Main application window.
    Hosts the Code Editor and coordinates future debugging and AI modules.
    """

    FILE_FILTERS = (
        "Supported Source Files (*.py *.java *.c *.cpp *.h *.hpp *.js);;"
        "Python Files (*.py);;"
        "Java Files (*.java);;"
        "C/C++ Files (*.c *.cpp *.h *.hpp);;"
        "JavaScript Files (*.js);;"
        "All Files (*)"
    )

    def __init__(self):
        super().__init__()
        self.editor: CodeEditor | None = None
        self.output_panel: OutputPanel | None = None
        self.ai_panel: AIPanel | None = None
        self.bottom_tab_widget: QTabWidget | None = None
        self.cursor_status_label: QLabel | None = None
        self.current_file_path: str | None = None
        self.execution_worker: ExecutionWorker | None = None
        self.ai_worker: AIAnalysisWorker | None = None
        self.new_action: QAction | None = None
        self.close_file_action: QAction | None = None
        self.run_action: QAction | None = None
        self.ai_explain_action: QAction | None = None
        self.run_btn: QPushButton | None = None
        self.lang_combo: QComboBox | None = None
        self._user_selected_language: str | None = None
        self.last_error_info: ErrorInfo | None = None
        self.last_execution_result: ExecutionResult | None = None
        self.last_report: DebugReport | None = None
        self.report_panel: ReportPanel | None = None
        self.export_report_action: QAction | None = None
        self.view_report_action: QAction | None = None
        self._base_title = "AI-Based Intelligent Desktop Debugger"
        self._init_window()
        self._init_ui()

    def _init_window(self):
        """Configure basic window properties."""
        self.setWindowTitle(self._base_title)
        self.resize(1000, 650)
        self.setMinimumSize(800, 500)

    def _init_ui(self):
        """Build the main layout housing the code editor and output panel."""
        # Menu bar setup
        self._setup_menu_bar()

        # Central container widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Main vertical layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Editor header bar with title and Run button
        header_layout = QHBoxLayout()
        header_label = QLabel("Code Editor")
        header_font = QFont("Segoe UI", 12, QFont.Weight.DemiBold)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: #2c3e50; padding-bottom: 2px;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Language selector dropdown
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        header_layout.addWidget(lang_label)

        self.lang_combo = QComboBox(self)
        self.lang_combo.addItems(["Python", "Java", "C", "C++", "JavaScript"])
        self.lang_combo.setToolTip("Select programming language for execution and syntax highlighting")
        self.lang_combo.setFixedWidth(110)
        self.lang_combo.activated.connect(self._on_user_language_selected)
        header_layout.addWidget(self.lang_combo)

        self.run_btn = QPushButton("▶ Run (F5)")
        self.run_btn.setToolTip("Compile and execute current code (F5)")
        self.run_btn.setStyleSheet("font-weight: bold; padding: 4px 14px;")
        self.run_btn.clicked.connect(self.run_code)
        header_layout.addWidget(self.run_btn)

        layout.addLayout(header_layout)

        # Vertical splitter for Editor (top) and Output / AI Panels (bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Instantiate Code Editor with line numbers
        self.editor = CodeEditor(self)
        self.editor.setPlaceholderText("# Type or paste your code here...")
        splitter.addWidget(self.editor)

        # Bottom tab widget housing Terminal Output and AI Assistant
        self.bottom_tab_widget = QTabWidget(self)
        self.bottom_tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 4px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #252526;
                color: #969696;
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                font-weight: bold;
                border-bottom: 2px solid #7c3aed;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2d2d2d;
                color: #cccccc;
            }
            """
        )

        # Output Panel
        self.output_panel = OutputPanel(self)
        self.output_panel.explain_requested.connect(self.request_ai_analysis)
        self.bottom_tab_widget.addTab(self.output_panel, "Terminal Output")

        # AI Assistant Panel
        self.ai_panel = AIPanel(self)
        self.bottom_tab_widget.addTab(self.ai_panel, "✨ AI Assistant")

        # Debug Report & Performance Analysis Panel (Module 5)
        self.report_panel = ReportPanel(self)
        self.bottom_tab_widget.addTab(self.report_panel, "📊 Debug Report")

        splitter.addWidget(self.bottom_tab_widget)

        # Set default proportions: 65% editor, 35% bottom tabs
        splitter.setSizes([420, 220])
        layout.addWidget(splitter)

        # Track document modifications to indicate unsaved changes in title
        self.editor.document().modificationChanged.connect(self._update_window_title)

        # Setup bottom status bar
        self._setup_status_bar()

    def _setup_menu_bar(self):
        """Builds application menu bar with File operations."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        # New Action
        self.new_action = QAction("&New File", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.setStatusTip("Create a new blank source code file (Ctrl+N)")
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)

        # Open Action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing source code file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Close File Action
        self.close_file_action = QAction("&Close File", self)
        self.close_file_action.setShortcut(QKeySequence("Ctrl+W"))
        self.close_file_action.setStatusTip("Close the current file (Ctrl+W)")
        self.close_file_action.triggered.connect(self.close_file)
        file_menu.addAction(self.close_file_action)

        # Save Action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current document")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As Action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save the current document under a new name")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        # Export Report Action (Module 5)
        self.export_report_action = QAction("&Export Debug Report...", self)
        self.export_report_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.export_report_action.setStatusTip("Export comprehensive debugging and performance report")
        self.export_report_action.triggered.connect(self.export_debug_report)
        file_menu.addAction(self.export_report_action)

        file_menu.addSeparator()

        # Exit Action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Run Menu
        run_menu = menu_bar.addMenu("&Run")

        # Run Action
        self.run_action = QAction("▶ &Run Code", self)
        self.run_action.setShortcut(QKeySequence("F5"))
        self.run_action.setStatusTip("Execute the current code (F5)")
        self.run_action.triggered.connect(self.run_code)
        run_menu.addAction(self.run_action)

        # Tools Menu
        tools_menu = menu_bar.addMenu("&Tools")

        # Validate Action
        validate_action = QAction("&Validate Code", self)
        validate_action.setShortcut(QKeySequence("F7"))
        validate_action.setStatusTip("Validate current code for syntax and structural correctness")
        validate_action.triggered.connect(self.validate_code)
        tools_menu.addAction(validate_action)

        # View Debug Report Action (Module 5)
        self.view_report_action = QAction("📊 &View Debug Report", self)
        self.view_report_action.setShortcut(QKeySequence("F9"))
        self.view_report_action.setStatusTip("View debugging report and performance analysis (F9)")
        self.view_report_action.triggered.connect(self.show_report_tab)
        tools_menu.addAction(self.view_report_action)

        # AI Menu
        ai_menu = menu_bar.addMenu("&AI")

        self.ai_explain_action = QAction("✨ AI &Explain && Fix", self)
        self.ai_explain_action.setShortcut(QKeySequence("F8"))
        self.ai_explain_action.setStatusTip("Generate AI root cause analysis and fix recommendation (F8)")
        self.ai_explain_action.triggered.connect(self.request_ai_analysis)
        ai_menu.addAction(self.ai_explain_action)

    def _setup_status_bar(self):
        """Initializes the status bar with cursor position indicators."""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready")

        # Label on right side of status bar for cursor position
        self.cursor_status_label = QLabel("Ln 1, Col 1")
        self.cursor_status_label.setStyleSheet("color: #555555; padding-right: 8px;")
        status_bar.addPermanentWidget(self.cursor_status_label)

        # Listen to cursor movements in the editor
        if self.editor:
            self.editor.cursorPositionChanged.connect(self._update_cursor_status)

    def _update_cursor_status(self):
        """Updates line and column counters whenever the cursor moves."""
        if not self.editor or not self.cursor_status_label:
            return

        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        total_lines = self.editor.blockCount()

        self.cursor_status_label.setText(f"Ln {line}, Col {col}  |  Total Lines: {total_lines}")

    def _update_window_title(self, *args):
        """Updates the window title to reflect open file and modification status."""
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            mod_flag = " *" if (self.editor and self.editor.document().isModified()) else ""
            self.setWindowTitle(f"{self._base_title} - {file_name}{mod_flag}")
        else:
            mod_flag = " *" if (self.editor and self.editor.document().isModified()) else ""
            if mod_flag:
                self.setWindowTitle(f"{self._base_title} - Untitled{mod_flag}")
            else:
                self.setWindowTitle(self._base_title)

    def _maybe_save_changes(self, action_name: str = "continue") -> bool:
        """
        Checks for unsaved changes in the editor.
        Returns True if safe to proceed (unmodified, saved, or discarded);
        returns False if the operation should be cancelled.
        """
        if not (self.editor and self.editor.document().isModified()):
            return True

        file_label = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            f"The current document has unsaved changes.\n\nDo you want to save changes to '{file_label}' before you {action_name}?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def new_file(self):
        """Creates a new blank document, prompting to save any unsaved changes."""
        if not self._maybe_save_changes(action_name="create a new file"):
            return

        if self.editor:
            self.editor.clear()
            self.editor.document().setModified(False)

        self.current_file_path = None
        self._user_selected_language = None
        self._set_combo_language("Python")
        if self.editor:
            self.editor.set_language("python")

        self.last_error_info = None
        self.last_execution_result = None
        self.last_report = None

        if self.output_panel:
            self.output_panel.clear_output()
        if self.ai_panel:
            self.ai_panel.clear_panel()
        if self.report_panel:
            self.report_panel.clear_panel()

        self._update_window_title()
        self.statusBar().showMessage("New blank file ready", 3000)

    def close_file(self) -> bool:
        """Closes the currently active file, resetting the workspace."""
        if not self._maybe_save_changes(action_name="close the file"):
            return False

        old_name = os.path.basename(self.current_file_path) if self.current_file_path else None

        if self.editor:
            self.editor.clear()
            self.editor.document().setModified(False)

        self.current_file_path = None
        self._user_selected_language = None
        self._set_combo_language("Python")
        if self.editor:
            self.editor.set_language("python")

        self.last_error_info = None
        self.last_execution_result = None
        self.last_report = None

        if self.output_panel:
            self.output_panel.clear_output()
        if self.ai_panel:
            self.ai_panel.clear_panel()
        if self.report_panel:
            self.report_panel.clear_panel()

        self._update_window_title()
        msg = f"Closed {old_name}" if old_name else "File closed"
        self.statusBar().showMessage(msg, 3000)
        return True

    def open_file(self):
        """Prompts the user to select and open a source code file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Source File",
            "",
            self.FILE_FILTERS,
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            QMessageBox.critical(self, "Error Opening File", f"Could not open file:\n{exc}")
            return

        if self.editor:
            self.editor.setPlainText(content)
            self.editor.document().setModified(False)
            self._user_selected_language = None
            lang = CodeValidator.detect_language(file_path)
            self._set_combo_language(lang)
            self.editor.set_language(lang)

        self.current_file_path = file_path
        self._update_window_title()
        self.statusBar().showMessage(f"Opened: {os.path.basename(file_path)}", 3000)

    def save_file(self) -> bool:
        """Saves the editor content to current file path, or prompts Save As if untitled."""
        if not self.current_file_path:
            return self.save_file_as()
        return self._write_to_file(self.current_file_path)

    def save_file_as(self) -> bool:
        """Prompts the user for a destination and saves the editor content."""
        initial_dir = self.current_file_path or ""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Source File As",
            initial_dir,
            self.FILE_FILTERS,
        )
        if not file_path:
            return False

        self.current_file_path = file_path
        if self.editor:
            self._user_selected_language = None
            lang = CodeValidator.detect_language(file_path)
            self._set_combo_language(lang)
            self.editor.set_language(lang)
        return self._write_to_file(file_path)

    def _write_to_file(self, file_path: str) -> bool:
        """Writes current editor content to the specified file path."""
        if not self.editor:
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
        except Exception as exc:
            QMessageBox.critical(self, "Error Saving File", f"Could not save file:\n{exc}")
            return False

        self.editor.document().setModified(False)
        self._update_window_title()
        self.statusBar().showMessage(f"Saved: {os.path.basename(file_path)}", 3000)
        return True

    def _on_user_language_selected(self, index: int):
        """Invoked when user explicitly changes the language dropdown."""
        if not self.lang_combo:
            return
        raw_lang = self.lang_combo.currentText().lower()
        mapped_lang = "cpp" if raw_lang in ("c++", "cpp") else raw_lang
        self._user_selected_language = mapped_lang
        if self.editor:
            self.editor.set_language(mapped_lang)

    def _set_combo_language(self, lang: str):
        """Programmatically synchronizes dropdown with detected language."""
        display_map = {
            "python": "Python",
            "java": "Java",
            "c": "C",
            "cpp": "C++",
            "javascript": "JavaScript",
        }
        target = display_map.get(lang.lower(), "Python")
        if self.lang_combo:
            idx = self.lang_combo.findText(target)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)

    def resolve_language(self, code: str) -> str:
        """
        Resolves target language following the priority:
        1. Explicit user selection from dropdown.
        2. Saved file extension (when no explicit user selection overriding it).
        3. Content-based detection for untitled/unsaved files.
        4. Fall back to Python.
        """
        # Priority 1: Explicit user selection from dropdown
        if self._user_selected_language:
            return self._user_selected_language

        # Priority 2: Saved file extension
        if self.current_file_path and os.path.exists(self.current_file_path):
            return CodeValidator.detect_language(self.current_file_path)

        # Priority 3: Content-based detection for untitled/unsaved files
        detected = CodeValidator.detect_language_from_content(code)
        if detected:
            return detected

        # Priority 4: Fall back to Python
        return "python"

    def validate_code(self):
        """Validates current editor code for syntax and structural integrity."""
        if not self.editor:
            return

        code = self.editor.toPlainText()
        language = self.resolve_language(code)
        self._set_combo_language(language)
        self.editor.set_language(language)

        result = CodeValidator.validate(code, file_path=self.current_file_path, language=language)

        if result.is_valid:
            self.statusBar().showMessage(
                f"✓ Validation Passed ({result.language}): {result.message}", 5000
            )
        else:
            error_line = result.error_line or 1
            error_col = result.error_column or 1
            self.statusBar().showMessage(
                f"✗ [{result.language}] Line {error_line}: {result.message}", 8000
            )
            self.editor.go_to_line(error_line, error_col)

    def run_code(self):
        """Executes the current code in a background thread."""
        if not self.editor:
            return

        if self.execution_worker and self.execution_worker.isRunning():
            self.statusBar().showMessage("Execution already in progress...", 3000)
            return

        code = self.editor.toPlainText()
        if not code.strip():
            self.statusBar().showMessage("Cannot run empty code buffer.", 3000)
            if self.output_panel:
                self.output_panel.clear_output()
                self.output_panel.append_text(
                    "Execution aborted: Code buffer is empty.\n", QColor("#f48771")
                )
            return

        # Auto-save if working with an existing file
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.save_file()

        # Resolve target language using priority rules
        language = self.resolve_language(code)
        self._set_combo_language(language)
        self.editor.set_language(language)

        # Update UI state while running
        if self.run_btn:
            self.run_btn.setEnabled(False)
            self.run_btn.setText("Running...")
        if self.run_action:
            self.run_action.setEnabled(False)

        if self.bottom_tab_widget and self.output_panel:
            self.bottom_tab_widget.setCurrentWidget(self.output_panel)

        if self.output_panel:
            self.output_panel.start_execution(language)

        self.statusBar().showMessage(f"Running {language.capitalize()}...", 4000)

        # Launch background execution worker
        self.execution_worker = ExecutionWorker(
            code=code,
            file_path=self.current_file_path,
            language=language,
            timeout=15.0,
            parent=self,
        )
        self.execution_worker.finished_signal.connect(self._on_execution_finished)
        self.execution_worker.start()

    def _on_execution_finished(self, result: ExecutionResult):
        """Handles completion of the background execution worker."""
        # Restore UI controls
        if self.run_btn:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("▶ Run (F5)")
        if self.run_action:
            self.run_action.setEnabled(True)

        self.last_execution_result = result

        if self.output_panel:
            self.output_panel.display_result(result)

        # Module 3: Error Detection & Classification
        code = self.editor.toPlainText() if self.editor else ""
        language = self.resolve_language(code)
        error_info = ErrorClassifier.classify(result, code, language)
        self.last_error_info = error_info

        if error_info:
            if self.output_panel:
                self.output_panel.display_error_info(error_info)
            if error_info.line_number and self.editor:
                col = error_info.column_number or 1
                self.editor.go_to_line(error_info.line_number, col)

        # Module 5: Generate Debugging & Performance Report
        report = ReportGenerator.build_report(
            result=result,
            error_info=error_info,
            code=code,
            file_path=self.current_file_path,
            language=language,
            ai_analysis=None,
        )
        self.last_report = report
        if self.report_panel:
            self.report_panel.display_report(report)

        if result.timed_out:
            self.statusBar().showMessage(f"Execution timed out ({result.execution_time:.2f}s)", 5000)
        elif result.has_error:
            self.statusBar().showMessage(
                f"Execution failed ({result.stage}) in {result.execution_time:.2f}s", 5000
            )
        else:
            self.statusBar().showMessage(
                f"Execution finished (exit code {result.exit_code}) in {result.execution_time:.2f}s", 5000
            )

        self.execution_worker = None

    def request_ai_analysis(self):
        """Requests AI analysis for the last detected error."""
        if not self.last_error_info:
            QMessageBox.information(
                self,
                "No Error Detected",
                "No runtime or compilation error has been captured yet.\n\n"
                "Run your program (F5) to detect an error before requesting AI analysis.",
            )
            return

        if self.ai_worker and self.ai_worker.isRunning():
            self.statusBar().showMessage("AI analysis already in progress...", 3000)
            return

        # Switch tab to AI Assistant
        if self.bottom_tab_widget and self.ai_panel:
            self.bottom_tab_widget.setCurrentWidget(self.ai_panel)
            self.ai_panel.set_loading()

        self.statusBar().showMessage("Analyzing error with AI diagnostic engine...", 4000)

        code = self.editor.toPlainText() if self.editor else ""

        # Launch AI worker
        self.ai_worker = AIAnalysisWorker(
            code=code,
            error_info=self.last_error_info,
            parent=self,
        )
        self.ai_worker.finished_signal.connect(self._on_ai_analysis_finished)
        self.ai_worker.error_signal.connect(self._on_ai_analysis_error)
        self.ai_worker.start()

    def _on_ai_analysis_finished(self, result: AIAnalysisResult):
        """Handles successful completion of the AI analysis worker."""
        if self.ai_panel:
            self.ai_panel.display_result(result)

        # Module 5: Enrich report with AI diagnosis
        if self.last_report:
            ReportGenerator.attach_ai_analysis(self.last_report, result)
            if self.report_panel:
                self.report_panel.display_report(self.last_report)

        self.statusBar().showMessage("✨ AI analysis and fix recommendation ready.", 5000)
        self.ai_worker = None

    def show_report_tab(self):
        """Switches bottom tab widget to the Debug Report panel (F9)."""
        if self.bottom_tab_widget and self.report_panel:
            self.bottom_tab_widget.setCurrentWidget(self.report_panel)

    def export_debug_report(self):
        """Triggers file export of the current debugging report (Ctrl+Shift+E)."""
        if self.report_panel:
            self.report_panel.export_report()

    def _on_ai_analysis_error(self, error_msg: str):
        """Handles failure during AI analysis."""
        if self.ai_panel:
            self.ai_panel.clear_panel()
        QMessageBox.warning(self, "AI Analysis Error", f"Failed to generate AI analysis:\n{error_msg}")
        self.statusBar().showMessage(f"AI analysis failed: {error_msg}", 5000)
        self.ai_worker = None

