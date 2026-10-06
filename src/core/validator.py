"""
Static code validation engine for the AI-Based Intelligent Desktop Debugger.
Provides syntax and structural checks across Python, Java, C, C++, and JavaScript.
"""

from dataclasses import dataclass
import os
import ast
import re


@dataclass
class ValidationResult:
    """Encapsulates the result of a code validation check."""

    is_valid: bool
    language: str
    message: str
    error_line: int | None = None
    error_column: int | None = None


class CodeValidator:
    """
    Validates source code for syntax correctness and structural integrity.
    Supports Python (AST-based) and structural validation (brackets, literals,
    preprocessor directives, and declarations) for C, C++, Java, and JavaScript.
    """

    LANGUAGE_MAP = {
        ".py": "python",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".js": "javascript",
    }

    LANGUAGE_DISPLAY_NAMES = {
        "python": "Python",
        "java": "Java",
        "c": "C",
        "cpp": "C++",
        "javascript": "JavaScript",
    }

    BRACKET_PAIRS = {
        ")": "(",
        "}": "{",
        "]": "[",
    }

    MATCHING_CLOSING = {
        "(": ")",
        "{": "}",
        "[": "]",
    }

    @classmethod
    def detect_language_from_content(cls, code: str) -> str | None:
        """
        Detects programming language by inspecting code content for distinct syntax signatures.
        Returns the detected language identifier or None if inconclusive.
        """
        if not code or not code.strip():
            return None

        # Strip comments so commented keywords don't trigger false positives
        clean_code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        clean_code = re.sub(r"//.*", "", clean_code)
        clean_code = re.sub(r"#[^\n]*", "", clean_code)

        # 1. Java signatures
        if re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+[A-Za-z0-9_$]+", clean_code):
            return "java"
        if re.search(r"\bSystem\.(out|err)\.(println|print|printf)\b", clean_code):
            return "java"
        if re.search(r"\bpublic\s+static\s+void\s+main\b", clean_code):
            return "java"
        if re.search(r"\bimport\s+java\.[a-z0-9_.]+", clean_code):
            return "java"

        # 2. C++ signatures
        if re.search(r"#\s*include\s*<(iostream|vector|string|map|unordered_map|memory|algorithm)>", clean_code):
            return "cpp"
        if re.search(r"\busing\s+namespace\s+std\s*;", clean_code):
            return "cpp"
        if re.search(r"\bstd::(cout|cin|cerr|endl|string|vector)\b", clean_code):
            return "cpp"
        if re.search(r"\bcout\s*<<|\bcin\s*>>", clean_code):
            return "cpp"

        # 3. C signatures
        if re.search(r"#\s*include\s*<(stdio|stdlib|string|math|stdbool|unistd)\.h>", clean_code):
            return "c"
        if re.search(r"\b(printf|scanf)\s*\(", clean_code) and re.search(r"\bint\s+main\s*\(", clean_code):
            return "c"

        # 4. JavaScript signatures
        if re.search(r"\bconsole\.(log|error|warn|info|debug)\s*\(", clean_code):
            return "javascript"
        if re.search(r"\b(const|let|var)\s+[A-Za-z0-9_$]+\s*=\s*(function|\([^)]*\)\s*=>)", clean_code):
            return "javascript"
        if re.search(r"\bdocument\.(getElementById|querySelector)\b", clean_code):
            return "javascript"

        # 5. Python signatures
        if re.search(r"\bdef\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s*:", clean_code):
            return "python"
        if re.search(r"\bif\s+__name__\s*==\s*['\"]__main__['\"]\s*:", clean_code):
            return "python"
        if re.search(r"^\s*from\s+[A-Za-z0-9_.]+\s+import\s+", clean_code, flags=re.MULTILINE):
            return "python"

        return None

    @classmethod
    def detect_language(
        cls,
        file_path: str | None,
        code: str | None = None,
        default: str = "python",
    ) -> str:
        """
        Determines programming language.
        If file_path exists, uses extension.
        If file_path is missing/untitled, inspects code content.
        Falls back to default if inconclusive.
        """
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in cls.LANGUAGE_MAP:
                return cls.LANGUAGE_MAP[ext]

        if code:
            detected = cls.detect_language_from_content(code)
            if detected:
                return detected

        return default

    @classmethod
    def validate(
        cls,
        code: str,
        file_path: str | None = None,
        language: str | None = None,
    ) -> ValidationResult:
        """
        Validates source code according to the target language.
        If language is not specified, it is inferred from file_path or code content.
        """
        lang = (language or cls.detect_language(file_path, code=code)).lower()
        display_name = cls.LANGUAGE_DISPLAY_NAMES.get(lang, lang.capitalize())

        # Check for empty or whitespace-only code
        if not code.strip():
            return ValidationResult(
                is_valid=False,
                language=display_name,
                message="Code buffer is empty.",
                error_line=1,
                error_column=1,
            )

        if lang == "python":
            return cls._validate_python(code)
        elif lang in ("c", "cpp"):
            return cls._validate_c_cpp(code, display_name)
        elif lang == "java":
            return cls._validate_java(code, file_path)
        elif lang == "javascript":
            return cls._validate_structural(code, display_name)
        else:
            # Fallback to general structural bracket/literal validation
            return cls._validate_structural(code, display_name)

    @classmethod
    def _validate_python(cls, code: str) -> ValidationResult:
        """Validates Python code using the standard AST parser."""
        try:
            ast.parse(code)
            return ValidationResult(
                is_valid=True,
                language="Python",
                message="Syntax check passed successfully.",
            )
        except SyntaxError as exc:
            line = exc.lineno or 1
            col = exc.offset or 1
            msg = exc.msg or "Invalid syntax"
            return ValidationResult(
                is_valid=False,
                language="Python",
                message=f"SyntaxError: {msg}",
                error_line=line,
                error_column=col,
            )

    @classmethod
    def _validate_structural(
        cls, code: str, language_name: str
    ) -> ValidationResult:
        """
        Performs lexical and structural analysis:
        - Balanced parentheses, brackets, and curly braces.
        - Proper closure of string and character literals.
        - Proper closure of block comments (/* ... */).
        """
        bracket_stack = []  # stores tuples of (char, line, col)
        in_string = None  # None, '"', or "'"
        string_start = (1, 1)
        in_single_comment = False
        in_block_comment = False
        block_comment_start = (1, 1)

        line = 1
        col = 0
        i = 0
        n = len(code)

        while i < n:
            ch = code[i]
            col += 1

            if ch == "\n":
                if in_single_comment:
                    in_single_comment = False
                elif in_string and in_string != "`":  # JS template literals allow newlines
                    # Unterminated string literal on this line
                    return ValidationResult(
                        is_valid=False,
                        language=language_name,
                        message=f"Unterminated string literal starting at line {string_start[0]}, column {string_start[1]}.",
                        error_line=string_start[0],
                        error_column=string_start[1],
                    )
                line += 1
                col = 0
                i += 1
                continue

            # Skip single-line comment contents
            if in_single_comment:
                i += 1
                continue

            # Check block comment ending
            if in_block_comment:
                if ch == "*" and i + 1 < n and code[i + 1] == "/":
                    in_block_comment = False
                    i += 2
                    col += 1
                    continue
                i += 1
                continue

            # Check string literal handling
            if in_string:
                # Check for escaped characters
                if ch == "\\" and i + 1 < n:
                    i += 2
                    col += 1
                    continue
                if ch == in_string:
                    in_string = None
                i += 1
                continue

            # Check start of comments
            if ch == "/" and i + 1 < n:
                next_ch = code[i + 1]
                if next_ch == "/":
                    in_single_comment = True
                    i += 2
                    col += 1
                    continue
                elif next_ch == "*":
                    in_block_comment = True
                    block_comment_start = (line, col)
                    i += 2
                    col += 1
                    continue

            # Check start of string or character literal
            if ch in ('"', "'", "`"):
                in_string = ch
                string_start = (line, col)
                i += 1
                continue

            # Check brackets
            if ch in ("(", "{", "["):
                bracket_stack.append((ch, line, col))
            elif ch in (")", "}", "]"):
                expected_open = cls.BRACKET_PAIRS[ch]
                if not bracket_stack:
                    return ValidationResult(
                        is_valid=False,
                        language=language_name,
                        message=f"Unexpected closing '{ch}' with no matching opening bracket.",
                        error_line=line,
                        error_column=col,
                    )
                open_ch, open_line, open_col = bracket_stack.pop()
                if open_ch != expected_open:
                    expected_close = cls.MATCHING_CLOSING[open_ch]
                    return ValidationResult(
                        is_valid=False,
                        language=language_name,
                        message=f"Mismatched bracket: expected '{expected_close}' for '{open_ch}' opened at line {open_line}, column {open_col}, but found '{ch}'.",
                        error_line=line,
                        error_column=col,
                    )

            i += 1

        # Check unclosed block comment
        if in_block_comment:
            return ValidationResult(
                is_valid=False,
                language=language_name,
                message=f"Unclosed block comment '/*' starting at line {block_comment_start[0]}, column {block_comment_start[1]}.",
                error_line=block_comment_start[0],
                error_column=block_comment_start[1],
            )

        # Check unclosed string literal
        if in_string:
            return ValidationResult(
                is_valid=False,
                language=language_name,
                message=f"Unterminated string literal starting at line {string_start[0]}, column {string_start[1]}.",
                error_line=string_start[0],
                error_column=string_start[1],
            )

        # Check unclosed brackets
        if bracket_stack:
            open_ch, open_line, open_col = bracket_stack[-1]
            expected_close = cls.MATCHING_CLOSING[open_ch]
            return ValidationResult(
                is_valid=False,
                language=language_name,
                message=f"Unclosed '{open_ch}' opened at line {open_line}, column {open_col}. Expected closing '{expected_close}'.",
                error_line=open_line,
                error_column=open_col,
            )

        return ValidationResult(
            is_valid=True,
            language=language_name,
            message="Structural validation passed successfully.",
        )

    @classmethod
    def _validate_c_cpp(cls, code: str, language_name: str) -> ValidationResult:
        """Validates C/C++ structural syntax and preprocessor balancing."""
        # 1. Base structural validation
        base_res = cls._validate_structural(code, language_name)
        if not base_res.is_valid:
            return base_res

        # 2. Check preprocessor directive balancing (#if, #ifdef, #ifndef vs #endif)
        prep_stack = []  # stores (directive, line_no)
        lines = code.splitlines()

        for idx, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            if stripped.startswith("#"):
                match = re.match(r"^#\s*([a-zA-Z]+)", stripped)
                if match:
                    directive = match.group(1)
                    if directive in ("if", "ifdef", "ifndef"):
                        prep_stack.append((directive, idx))
                    elif directive == "endif":
                        if not prep_stack:
                            return ValidationResult(
                                is_valid=False,
                                language=language_name,
                                message=f"Extraneous '#endif' preprocessor directive on line {idx} without matching '#if'.",
                                error_line=idx,
                                error_column=1,
                            )
                        prep_stack.pop()

        if prep_stack:
            directive, line_no = prep_stack[-1]
            return ValidationResult(
                is_valid=False,
                language=language_name,
                message=f"Unclosed preprocessor directive '#{directive}' starting at line {line_no}. Expected matching '#endif'.",
                error_line=line_no,
                error_column=1,
            )

        return ValidationResult(
            is_valid=True,
            language=language_name,
            message=f"{language_name} syntax and structure passed successfully.",
        )

    @classmethod
    def _validate_java(cls, code: str, file_path: str | None) -> ValidationResult:
        """Validates Java structural syntax and type naming conventions."""
        # 1. Base structural validation
        base_res = cls._validate_structural(code, "Java")
        if not base_res.is_valid:
            return base_res

        # 2. Strip comments for keyword inspection
        clean_code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        clean_code = re.sub(r"//.*", "", clean_code)

        # Check that code contains at least one class, interface, enum, or record
        type_pattern = re.compile(
            r"\b(class|interface|enum|record)\b\s+([A-Za-z0-9_$]+)"
        )
        types_found = type_pattern.findall(clean_code)

        if not types_found:
            return ValidationResult(
                is_valid=False,
                language="Java",
                message="Java file must contain at least one class, interface, enum, or record declaration.",
                error_line=1,
                error_column=1,
            )

        # 3. Check public type against file name if saved
        if file_path and file_path.lower().endswith(".java"):
            file_base = os.path.splitext(os.path.basename(file_path))[0]
            public_pattern = re.compile(
                r"\bpublic\s+(?:final\s+|abstract\s+)?(class|interface|enum|record)\b\s+([A-Za-z0-9_$]+)"
            )
            public_match = public_pattern.search(clean_code)
            if public_match:
                public_name = public_match.group(2)
                if public_name != file_base:
                    # Find line of public declaration
                    match_pos = public_match.start()
                    line_no = code[:match_pos].count("\n") + 1
                    return ValidationResult(
                        is_valid=False,
                        language="Java",
                        message=f"The public type '{public_name}' must be defined in its own file named '{public_name}.java' (current file: '{os.path.basename(file_path)}').",
                        error_line=line_no,
                        error_column=1,
                    )

        return ValidationResult(
            is_valid=True,
            language="Java",
            message="Java syntax and structure passed successfully.",
        )
