# AI-Based Intelligent Desktop Debugger

An intelligent, multi-language desktop debugging assistant and code execution environment built with **Python**, **PyQt6**, and **Google Gemini AI**.

The application combines a code editor, multi-language compiler/execution engine, static syntax validator, automated error classifier, AI-powered diagnostic engine, and exportable performance/debug reporting into a desktop IDE.

---

## 🚀 Development Status

All five planned architecture modules are **completed, integrated, and verified**:

- [x] **Module 1: Modern Multi-Language Code Editor** — Monospace editing, syntax highlighting, line numbers gutter, cursor position tracking, and file I/O.
- [x] **Module 2: Compilation, Execution & Static Validation Engine** — Subprocess execution for 5 languages, 15s timeout protection, non-blocking Qt background worker, and static syntax validation.
- [x] **Module 3: Error Detection & Classification Engine** — Regex-based compiler and runtime traceback analysis, category and severity classification, and automatic cursor navigation to error locations.
- [x] **Module 4: AI Diagnostic Assistant & Google Gemini Integration** — Pluggable provider architecture with live Google Gemini (`google-genai`) structured outputs and a `MockAIProvider` fallback when Gemini is unavailable.
- [x] **Module 5: Debugging Report & Performance Analysis** — Process execution-time evaluation, interactive report viewer, and multi-format export (Markdown, HTML, Plain Text).

---

## ✨ Key Features & Modules

### 1. Modern Multi-Language Code Editor (Module 1)
- Custom monospace editor with tab stop spacing (4 spaces) and smooth scrolling.
- Line number gutter with active-line indicators.
- Real-time syntax highlighters for Python, Java, C, C++, and JavaScript.
- Status bar tracking cursor coordinates (`Ln X, Col Y`), total lines, character count, encoding, and detected language.
- Full file operations: New (`Ctrl+N`), Open (`Ctrl+O`), Save (`Ctrl+S`), and Save As (`Ctrl+Shift+S`).

### 2. Multi-Language Execution & Static Validation (Module 2)
- **Background Execution Worker (`F5`)**: Non-blocking `QThread` execution prevents UI freezing during compilation and execution cycles.
- **Process Safeguards**: Automatic process termination on timeout (15s default limit).
- **Static Syntax Validation (`F7`)**: Instant AST-based validation for Python and structural integrity checks (brackets, directives, declarations) for C, C++, Java, and JavaScript before execution.
- **Tabbed Console**: Dual-tab bottom output panel for raw standard output/error and parsed structured diagnostics.

### 3. Error Detection & Classification (Module 3)
- Automatically parses execution failures, compiler diagnostics, and uncaught exceptions.
- **6 Verified Error Categories** (from `ErrorClassifier`):
  1. `Compilation Error`
  2. `Syntax Error`
  3. `Runtime Error`
  4. `Logical Error`
  5. `Timeout Error`
  6. `Environment Error`
- **Severity Ratings**: Critical, High, Medium, and Low.
- Extracts failing line/column coordinates, source context snippets, and detailed compiler traces.
- **Editor Navigation**: Automatically navigates the cursor to and centers on the failing line and column in the code editor.

### 4. AI Diagnostic Assistant & Gemini Integration (Module 4)
- **Official Google GenAI SDK (`google-genai`)**: Connects directly to Gemini models (defaulting to `gemini-2.5-flash` with resilient fallback support).
- **Enforced Structured Schema**: Uses structured JSON output using a Pydantic schema to ensure responses directly map to:
  1. 🔍 **Root Cause Analysis**: Plain-language explanation of why the failure occurred.
  2. 🛠️ **Suggested Fix**: Minimal corrected code snippet with one-click copy.
  3. 💡 **Debugging Guidance**: Actionable tips and preventative checks.
  4. ⚡ **Optimized Solution**: Best-practice or idiomatic implementation.
- **Smart Provider Selection**: Automatically detects `GEMINI_API_KEY` from `.env`; seamlessly falls back to `MockAIProvider` when no Gemini API key is configured or Gemini provider initialization fails.
- **Shortcut (`F8`)**: One-click AI diagnosis for detected errors.

### 5. Debugging Reports & Performance Analysis (Module 5)
- **Interactive Report Viewer (`F9`)**: Displays execution summary, environment info, performance metrics, error diagnosis, and AI fix recommendations.
- **Performance Evaluation**: Wall-clock execution timing and speed rating (Fast, Moderate, Slow, Timeout).
- **Multi-Format Export (`Ctrl+Shift+E`)**: One-click export to:
  - 📄 **Markdown (`.md`)**: GitHub-flavored formatted report.
  - 🌐 **HTML (`.html`)**: Self-contained, styled document ready for browser viewing or sharing.
  - 📝 **Plain Text (`.txt`)**: Clean text log.

---

## 🌐 Supported Programming Languages

| Language | Extensions | Static Validation | Compiler / Runtime |
| :--- | :--- | :--- | :--- |
| **Python** | `.py` | AST Validation | Active Python Interpreter |
| **C** | `.c`, `.h` | Structural / Directives | `gcc` |
| **C++** | `.cpp`, `.hpp` | Structural / Brackets | `g++` |
| **Java** | `.java` | Structural / Declarations | `javac` & `java` |
| **JavaScript** | `.js` | Structural / Syntax | `node` |

*Note: For C, C++, Java, and JavaScript execution, the respective system compilers/runtimes (`gcc`, `g++`, `javac`/`java`, `node`) must be installed and accessible in your system `PATH`.*

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `F5` | **Run Program** (Compile & Execute) |
| `F7` | **Validate Syntax** (Static structural check) |
| `F8` | **AI Analysis** (Diagnose error with Gemini) |
| `F9` | **View Debug Report** |
| `Ctrl + Shift + E` | **Export Debug Report** |
| `Ctrl + N` | **New File** |
| `Ctrl + O` | Open File |
| `Ctrl + S` | Save File |
| `Ctrl + Shift + S` | Save As |
| `Ctrl + Q` | Exit Application |

---

## 📁 Project Structure

```text
AI-Desktop-Debugger/
├── .env                     # Local environment secrets (GEMINI_API_KEY) [git-ignored]
├── .gitignore               # Ignored files, cache, and virtual environment
├── requirements.txt         # Project dependencies
├── main.py                  # Application entry point
├── README.md                # Documentation and running instructions
└── src/
    ├── __init__.py
    ├── core/                # Core execution & diagnosis engines
    │   ├── __init__.py
    │   ├── runner.py        # Multi-language compilers & runners (Python, C, C++, Java, JS)
    │   ├── validator.py     # Static syntax & structural integrity validator
    │   ├── error_classifier.py # Traceback parser & error category/severity classifier
    │   └── execution_worker.py # Background QThread for non-blocking execution
    ├── ai/                  # AI diagnostic assistants & providers
    │   ├── __init__.py
    │   ├── models.py        # AIAnalysisResult data models
    │   ├── prompt_builder.py# Structured diagnostic prompt builder
    │   ├── base_provider.py # BaseAIProvider interface & deterministic MockAIProvider
    │   ├── gemini_provider.py # Live Gemini LLM provider (google-genai SDK)
    │   └── ai_worker.py     # Background QThread for asynchronous AI analysis
    ├── report/              # Performance analysis & report generation
    │   ├── __init__.py
    │   ├── models.py        # DebugReport and PerformanceMetrics data models
    │   ├── generator.py     # Report synthesis & performance evaluation
    │   └── exporter.py      # Markdown, HTML, and Text report exporters
    └── ui/                  # PyQt6 user interface components
        ├── __init__.py
        ├── main_window.py   # Main window layout, actions, menus, and coordination
        └── widgets/
            ├── __init__.py
            ├── code_editor.py        # Monospace editor with line gutter
            ├── syntax_highlighter.py # Multi-language syntax highlighters
            ├── output_panel.py       # Console output & structured diagnostics tabs
            ├── ai_panel.py           # AI assistant card-based recommendation panel
            └── report_panel.py       # Debugging report & performance viewer
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed.
- *(Optional)* Compilers/runtimes for other languages if executing them locally:
  - GCC / G++ (e.g., MinGW-w64 on Windows)
  - JDK 17+ (`javac`, `java`)
  - Node.js (`node`)

### 2. Set Up Virtual Environment & Dependencies

A virtual environment (`.venv`) can be initialized as follows:

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Or activate on Windows Command Prompt
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Gemini API Key

The application reads the Gemini API key from a `.env` file in the project root:

1. Create or open `.env` in the project root:
   ```env
   # Gemini API Configuration
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
2. Replace `your_gemini_api_key_here` with your Google AI Studio API key.
3. *Note: If `GEMINI_API_KEY` is not set or empty, the application will automatically fall back to the built-in offline `MockAIProvider`.*

---

## ▶️ Running the Application

Launch the desktop application using the virtual environment's Python:

```bash
# Using virtual environment path directly
.venv\Scripts\python main.py

# Or if your virtual environment is already activated:
python main.py
```
