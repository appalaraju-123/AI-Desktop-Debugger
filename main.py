"""
Application entry point for the AI-Based Intelligent Desktop Debugger.
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Initializes and starts the desktop application."""
    # Create the Qt Application instance
    app = QApplication(sys.argv)
    app.setApplicationName("AI-Based Intelligent Desktop Debugger")

    # Create and display the main application window
    window = MainWindow()
    window.show()

    # Start the Qt event loop and exit with its return code
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
