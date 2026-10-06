"""
Structured prompt construction for AI diagnostics and fix recommendations.
Prepares system and user prompts adhering to LLM formatting standards.
"""

from src.core.error_classifier import ErrorInfo


class PromptBuilder:
    """Builds structured prompt messages for LLM-based error diagnostics."""

    SYSTEM_PROMPT = (
        "You are an expert software engineer and debugger. Your job is to analyze programming "
        "errors, explain their root cause in simple language, provide a precise fix, offer debugging "
        "guidance, and suggest an optimized solution."
    )

    @classmethod
    def build_diagnostic_prompt(cls, code: str, error_info: ErrorInfo) -> str:
        """Constructs a comprehensive, structured diagnostic prompt from ErrorInfo."""
        loc_str = f"Line {error_info.line_number}" if error_info.line_number else "Unknown"
        if error_info.column_number:
            loc_str += f", Column {error_info.column_number}"

        prompt = (
            f"Please analyze the following {error_info.language} program error:\n\n"
            f"=== ERROR DETAILS ===\n"
            f"Language: {error_info.language}\n"
            f"Category: {error_info.error_category}\n"
            f"Type: {error_info.error_type}\n"
            f"Location: {loc_str}\n"
            f"Severity: {error_info.severity}\n"
            f"Message: {error_info.message}\n"
        )
        if error_info.code_context:
            prompt += f"Failing Code Snippet: {error_info.code_context}\n"

        prompt += (
            f"\n=== FULL SOURCE CODE ===\n"
            f"```{error_info.language.lower()}\n"
            f"{code}\n"
            f"```\n\n"
        )

        if error_info.raw_details:
            prompt += (
                f"=== COMPILER / RUNTIME TRACE ===\n"
                f"{error_info.raw_details}\n\n"
            )

        prompt += (
            "=== REQUIRED OUTPUT SECTIONS ===\n"
            "1. Root Cause: Plain-language explanation of why the failure occurred.\n"
            "2. Suggested Fix: Minimal corrected code snippet that resolves the error.\n"
            "3. Debugging Guidance: Actionable tips and preventative checks.\n"
            "4. Optimized Solution: Best-practice or idiomatic approach.\n"
        )
        return prompt
