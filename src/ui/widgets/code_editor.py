"""
Code editor widget with line number gutter and monospaced typography.
"""

from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont, QFontMetrics
from src.ui.widgets.syntax_highlighter import CodeHighlighter


class LineNumberArea(QWidget):
    """
    Side gutter widget dedicated to rendering line numbers.
    It tracks the scroll position and line blocks of its parent CodeEditor.
    """

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        """Determines the required width of the gutter."""
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """Delegates painting of line numbers back to the editor."""
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """
    A lightweight, robust code editor widget.
    Provides line numbering, monospaced font rendering, and current line highlighting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Gutter widget for line numbers
        self.line_number_area = LineNumberArea(self)

        self._setup_editor_font()
        self._setup_signals()

        # Initial geometry and highlight
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Syntax highlighter
        is_dark = self.palette().base().color().lightness() < 128
        self.highlighter = CodeHighlighter(self.document(), is_dark=is_dark)

    def _setup_editor_font(self):
        """Applies a clean monospaced font and sets standard 4-space tabs."""
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Tab key inserts equivalent of 4 spaces
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * font_metrics.horizontalAdvance(" "))

    def _setup_signals(self):
        """Connects Qt signals to keep the line number gutter synchronized."""
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

    def line_number_area_width(self) -> int:
        """Calculates gutter width based on the total number of lines."""
        digits = max(1, len(str(self.blockCount())))
        # Padding (20px) + width of the digits
        width = 20 + self.fontMetrics().horizontalAdvance("9") * digits
        return width

    def update_line_number_area_width(self, _):
        """Adjusts the viewport margin to make room for the line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int):
        """Repaints or scrolls the line number gutter during text editing or scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Repositions the gutter whenever the editor window is resized."""
        super().resizeEvent(event)
        contents_rect = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(contents_rect.left(), contents_rect.top(), self.line_number_area_width(), contents_rect.height())
        )

    def highlight_current_line(self):
        """Applies a subtle highlight to the line currently under the cursor."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            base_color = self.palette().base().color()
            if base_color.lightness() < 128:
                line_color = base_color.lighter(120)
            else:
                line_color = QColor("#f4f6f8")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def go_to_line(self, line_number: int, column: int = 1):
        """Moves cursor to the given line and column (1-indexed) and centers the viewport."""
        block = self.document().findBlockByNumber(max(0, line_number - 1))
        if block.isValid():
            cursor = self.textCursor()
            pos = block.position() + max(0, column - 1)
            cursor.setPosition(min(pos, self.document().characterCount() - 1))
            self.setTextCursor(cursor)
            self.centerCursor()
            self.setFocus()

    def set_language(self, language: str):
        """Switches the syntax highlighting language for this editor."""
        if hasattr(self, "highlighter") and self.highlighter:
            self.highlighter.set_language(language)

    def line_number_area_paint_event(self, event):
        """Renders the actual line number text inside the gutter."""
        painter = QPainter(self.line_number_area)
        base_color = self.palette().base().color()
        if base_color.lightness() < 128:
            gutter_bg = self.palette().window().color()
            gutter_fg = QColor("#858585")
        else:
            gutter_bg = QColor("#f0f0f2")
            gutter_fg = QColor("#7f8c8d")

        # Background color for the line number column
        painter.fillRect(event.rect(), gutter_bg)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number_text = str(block_number + 1)
                painter.setPen(gutter_fg)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number_text,
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
