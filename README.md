# AI-Based Intelligent Desktop Debugger

An intelligent desktop debugging assistant built with Python and PyQt6.

---

## Development Status

- **Phase 1: Project Foundation**: PyQt6 window initialized and verified.
- **Phase 2: Code Editor (Module 1 - Step 1)**: Integrated `CodeEditor` with line numbers, monospaced font, tab stops, and live cursor position indicators.

### Project Structure

```text
AI-Desktop-Debugger/
├── requirements.txt         # Project dependencies (PyQt6)
├── main.py                  # Application entry point
├── src/
│   ├── __init__.py
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py   # PyQt6 MainWindow with CodeEditor layout
│       └── widgets/
│           ├── __init__.py
│           └── code_editor.py # CodeEditor widget with line number gutter
└── README.md                # Documentation and running instructions
```

---

## Getting Started

### 1. Set Up Environment & Install Dependencies

A virtual environment (`.venv`) is already prepared. If you ever need to recreate or activate it:

```bash
# Create virtual environment (if not already created)
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Or activate on Windows Command Prompt
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

Launch the desktop application using the virtual environment's Python:

```bash
.venv\Scripts\python main.py
```
*(Or simply `python main.py` if your `.venv` is activated)*

