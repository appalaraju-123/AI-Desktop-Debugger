"""
Multi-language syntax highlighter widget using QSyntaxHighlighter.
Supports Python, Java, C, C++, and JavaScript with dark and light theme palettes.
"""

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class CodeHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter supporting Python, Java, C, C++, and JavaScript.
    Applies formatting rules for keywords, types, strings, comments, numbers,
    and preprocessor directives.
    """

    STATE_NORMAL = 0
    STATE_BLOCK_COMMENT = 1
    STATE_TRIPLE_DOUBLE = 2
    STATE_TRIPLE_SINGLE = 3

    def __init__(self, parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.is_dark = is_dark
        self.current_language = "python"

        # Format mappings
        self.formats: dict[str, QTextCharFormat] = {}
        self._init_formats()

        # Compile language rules
        self.rules: dict[str, list[tuple[QRegularExpression, QTextCharFormat]]] = {}
        self._build_all_rules()

    def set_theme(self, is_dark: bool):
        """Updates color palette according to editor background lightness."""
        if self.is_dark != is_dark:
            self.is_dark = is_dark
            self._init_formats()
            self._build_all_rules()
            self.rehighlight()

    def set_language(self, language: str):
        """Switches the active syntax highlighting language and rehighlights."""
        clean_lang = language.lower().strip()
        if clean_lang in ("c", "cpp", "c++", ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx"):
            target = "cpp" if "++" in clean_lang or "pp" in clean_lang or "xx" in clean_lang else "c"
        elif clean_lang in ("java", ".java"):
            target = "java"
        elif clean_lang in ("javascript", "js", ".js"):
            target = "javascript"
        else:
            target = "python"

        if self.current_language != target:
            self.current_language = target
            self.rehighlight()

    def _init_formats(self):
        """Defines styling formats with high-contrast colors for dark and light modes."""
        if self.is_dark:
            keyword_color = QColor("#569cd6")     # Soft blue
            type_color = QColor("#4ec9b0")        # Teal
            string_color = QColor("#ce9178")      # Warm peach / orange
            number_color = QColor("#b5cea8")      # Light mint green
            comment_color = QColor("#6a9955")     # Olive green
            preprocessor_color = QColor("#c586c0")# Purple
            function_color = QColor("#dcdcaa")    # Soft yellow
        else:
            keyword_color = QColor("#0000ff")     # Pure blue
            type_color = QColor("#267f99")        # Dark teal
            string_color = QColor("#a31515")      # Dark red
            number_color = QColor("#098658")      # Forest green
            comment_color = QColor("#008000")     # Green
            preprocessor_color = QColor("#af00db")# Purple
            function_color = QColor("#795e26")    # Gold/brown

        # Keyword format
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(keyword_color)
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        self.formats["keyword"] = kw_fmt

        # Type format
        type_fmt = QTextCharFormat()
        type_fmt.setForeground(type_color)
        type_fmt.setFontWeight(QFont.Weight.DemiBold)
        self.formats["type"] = type_fmt

        # String format
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(string_color)
        self.formats["string"] = str_fmt

        # Number format
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(number_color)
        self.formats["number"] = num_fmt

        # Comment format
        comm_fmt = QTextCharFormat()
        comm_fmt.setForeground(comment_color)
        comm_fmt.setFontItalic(True)
        self.formats["comment"] = comm_fmt

        # Preprocessor format
        prep_fmt = QTextCharFormat()
        prep_fmt.setForeground(preprocessor_color)
        self.formats["preprocessor"] = prep_fmt

        # Function format
        func_fmt = QTextCharFormat()
        func_fmt.setForeground(function_color)
        self.formats["function"] = func_fmt

    def _build_all_rules(self):
        """Constructs regex rules for each supported language."""
        self.rules["python"] = self._build_python_rules()
        self.rules["c"] = self._build_c_rules()
        self.rules["cpp"] = self._build_cpp_rules()
        self.rules["java"] = self._build_java_rules()
        self.rules["javascript"] = self._build_javascript_rules()

    def _build_python_rules(self) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        rules = []

        keywords = [
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
            "or", "pass", "raise", "return", "try", "while", "with", "yield"
        ]
        types = [
            "True", "False", "None", "self", "cls", "int", "float", "str", "bool",
            "list", "dict", "set", "tuple", "bytes", "object", "type"
        ]

        # Numbers
        rules.append((QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b"), self.formats["number"]))
        rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), self.formats["number"]))

        # Keywords
        for kw in keywords:
            rules.append((QRegularExpression(rf"\b{kw}\b"), self.formats["keyword"]))

        # Built-in types / constants
        for t in types:
            rules.append((QRegularExpression(rf"\b{t}\b"), self.formats["type"]))

        # Decorators (@decorator)
        rules.append((QRegularExpression(r"@[A-Za-z0-9_]+"), self.formats["preprocessor"]))

        # Functions
        rules.append((QRegularExpression(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()"), self.formats["function"]))

        # Strings (single-line)
        rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.formats["string"]))
        rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.formats["string"]))

        # Single-line comment (#)
        rules.append((QRegularExpression(r"#[^\n]*"), self.formats["comment"]))

        return rules

    def _build_c_rules(self) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        rules = []

        keywords = [
            "auto", "break", "case", "const", "continue", "default", "do",
            "else", "enum", "extern", "for", "goto", "if", "inline",
            "register", "restrict", "return", "sizeof", "static", "struct",
            "switch", "typedef", "union", "volatile", "while"
        ]
        types = [
            "void", "char", "short", "int", "long", "float", "double", "signed",
            "unsigned", "size_t", "ssize_t", "int8_t", "int16_t", "int32_t",
            "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t", "bool",
            "true", "false", "NULL", "FILE"
        ]

        # Numbers
        rules.append((QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?[fFlLuU]?\b"), self.formats["number"]))
        rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+[uUlL]*\b"), self.formats["number"]))

        # Preprocessor directives
        rules.append((QRegularExpression(r"^\s*#\s*[a-zA-Z_]+[^\n]*"), self.formats["preprocessor"]))

        # Keywords
        for kw in keywords:
            rules.append((QRegularExpression(rf"\b{kw}\b"), self.formats["keyword"]))

        # Types
        for t in types:
            rules.append((QRegularExpression(rf"\b{t}\b"), self.formats["type"]))

        # Function calls
        rules.append((QRegularExpression(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()"), self.formats["function"]))

        # Strings & chars
        rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.formats["string"]))
        rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.formats["string"]))

        # Single line comment
        rules.append((QRegularExpression(r"//[^\n]*"), self.formats["comment"]))

        return rules

    def _build_cpp_rules(self) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        rules = self._build_c_rules()

        cpp_keywords = [
            "alignas", "alignof", "and", "and_eq", "asm", "bitand", "bitor",
            "catch", "class", "compl", "concept", "consteval", "constexpr",
            "constinit", "const_cast", "co_await", "co_return", "co_yield",
            "decltype", "delete", "dynamic_cast", "explicit", "export",
            "friend", "mutable", "namespace", "new", "noexcept", "not",
            "not_eq", "nullptr", "operator", "or", "or_eq", "override",
            "private", "protected", "public", "reinterpret_cast", "requires",
            "static_assert", "static_cast", "template", "this", "thread_local",
            "throw", "try", "typeid", "typename", "using", "virtual", "xor", "xor_eq"
        ]
        cpp_types = [
            "std", "string", "string_view", "vector", "map", "unordered_map",
            "set", "unordered_set", "pair", "tuple", "unique_ptr", "shared_ptr",
            "weak_ptr", "cout", "cin", "cerr", "endl"
        ]

        for kw in cpp_keywords:
            rules.append((QRegularExpression(rf"\b{kw}\b"), self.formats["keyword"]))

        for t in cpp_types:
            rules.append((QRegularExpression(rf"\b{t}\b"), self.formats["type"]))

        return rules

    def _build_java_rules(self) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        rules = []

        keywords = [
            "abstract", "assert", "break", "case", "catch", "class", "const",
            "continue", "default", "do", "else", "enum", "extends", "final",
            "finally", "for", "goto", "if", "implements", "import", "instanceof",
            "interface", "native", "new", "package", "private", "protected",
            "public", "return", "static", "strictfp", "super", "switch",
            "synchronized", "this", "throw", "throws", "transient", "try",
            "volatile", "while", "record", "sealed", "non-sealed", "permits", "yield"
        ]
        types = [
            "boolean", "byte", "char", "short", "int", "long", "float", "double",
            "void", "true", "false", "null", "String", "Integer", "Double",
            "Boolean", "Long", "Float", "Character", "Byte", "Short", "Object",
            "System", "List", "ArrayList", "Map", "HashMap", "Set", "HashSet"
        ]

        # Numbers
        rules.append((QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?[fFdDlL]?\b"), self.formats["number"]))
        rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+[lL]?\b"), self.formats["number"]))

        # Annotations (@Override, etc.)
        rules.append((QRegularExpression(r"@[A-Za-z0-9_]+"), self.formats["preprocessor"]))

        # Keywords
        for kw in keywords:
            rules.append((QRegularExpression(rf"\b{kw}\b"), self.formats["keyword"]))

        # Types
        for t in types:
            rules.append((QRegularExpression(rf"\b{t}\b"), self.formats["type"]))

        # Function calls
        rules.append((QRegularExpression(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()"), self.formats["function"]))

        # Strings & chars
        rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.formats["string"]))
        rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.formats["string"]))

        # Single line comment
        rules.append((QRegularExpression(r"//[^\n]*"), self.formats["comment"]))

        return rules

    def _build_javascript_rules(self) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        rules = []

        keywords = [
            "async", "await", "break", "case", "catch", "class", "const",
            "continue", "debugger", "default", "delete", "do", "else", "export",
            "extends", "finally", "for", "function", "if", "import", "in",
            "instanceof", "let", "new", "return", "super", "switch", "this",
            "throw", "try", "typeof", "var", "void", "while", "with", "yield"
        ]
        types = [
            "true", "false", "null", "undefined", "NaN", "Infinity",
            "console", "document", "window", "Array", "Object", "String",
            "Number", "Boolean", "Promise", "JSON", "Math", "Date", "RegExp",
            "Map", "Set", "Symbol"
        ]

        # Numbers
        rules.append((QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b"), self.formats["number"]))
        rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), self.formats["number"]))

        # Keywords
        for kw in keywords:
            rules.append((QRegularExpression(rf"\b{kw}\b"), self.formats["keyword"]))

        # Types
        for t in types:
            rules.append((QRegularExpression(rf"\b{t}\b"), self.formats["type"]))

        # Function calls
        rules.append((QRegularExpression(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*(?=\()"), self.formats["function"]))

        # Strings (single, double, template)
        rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.formats["string"]))
        rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.formats["string"]))
        rules.append((QRegularExpression(r"`[^`\\]*(\\.[^`\\]*)*`"), self.formats["string"]))

        # Single line comment
        rules.append((QRegularExpression(r"//[^\n]*"), self.formats["comment"]))

        return rules

    def highlightBlock(self, text: str):
        """Applies formatting rules and multi-line block tracking to the given text block."""
        active_rules = self.rules.get(self.current_language, self.rules["python"])

        # 1. Apply token patterns
        for pattern, fmt in active_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # 2. Multi-line comments / blocks
        if self.current_language == "python":
            self._highlight_multiline(text, '"""', self.STATE_TRIPLE_DOUBLE, self.formats["string"])
            self._highlight_multiline(text, "'''", self.STATE_TRIPLE_SINGLE, self.formats["string"])
        else:
            self._highlight_c_style_multiline(text)

    def _highlight_c_style_multiline(self, text: str):
        """Highlights /* ... */ multi-line comments in C, C++, Java, and JavaScript."""
        start_pattern = QRegularExpression(r"/\*")
        end_pattern = QRegularExpression(r"\*/")

        self.setCurrentBlockState(self.STATE_NORMAL)
        start_index = 0

        if self.previousBlockState() == self.STATE_BLOCK_COMMENT:
            start_index = 0
        else:
            match = start_pattern.match(text)
            start_index = match.capturedStart() if match.hasMatch() else -1

        while start_index >= 0:
            end_match = end_pattern.match(text, start_index + 2)
            end_index = end_match.capturedStart() if end_match.hasMatch() else -1

            if end_index == -1:
                self.setCurrentBlockState(self.STATE_BLOCK_COMMENT)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()

            self.setFormat(start_index, comment_length, self.formats["comment"])

            match = start_pattern.match(text, start_index + comment_length)
            start_index = match.capturedStart() if match.hasMatch() else -1

    def _highlight_multiline(self, text: str, delimiter: str, state_val: int, fmt: QTextCharFormat):
        """Highlights multi-line triple quoted strings in Python."""
        delim_pattern = QRegularExpression(QRegularExpression.escape(delimiter))

        start_index = 0
        if self.previousBlockState() == state_val:
            start_index = 0
        else:
            match = delim_pattern.match(text)
            start_index = match.capturedStart() if match.hasMatch() else -1

        while start_index >= 0:
            end_match = delim_pattern.match(text, start_index + len(delimiter))
            end_index = end_match.capturedStart() if end_match.hasMatch() else -1

            if end_index == -1:
                self.setCurrentBlockState(state_val)
                length = len(text) - start_index
            else:
                length = end_index - start_index + end_match.capturedLength()
                self.setCurrentBlockState(self.STATE_NORMAL)

            self.setFormat(start_index, length, fmt)

            match = delim_pattern.match(text, start_index + length)
            start_index = match.capturedStart() if match.hasMatch() else -1
