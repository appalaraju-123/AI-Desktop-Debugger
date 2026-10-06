"""
Abstract AI provider interface and deterministic MockAIProvider implementation.
Enables pluggable integration with future LLM providers (Gemini, OpenAI, Ollama).
"""

from abc import ABC, abstractmethod
import re
from src.core.error_classifier import ErrorInfo
from src.ai.models import AIAnalysisResult


class BaseAIProvider(ABC):
    """Abstract base class defining the contract for AI analysis providers."""

    @abstractmethod
    def analyze_error(self, code: str, error_info: ErrorInfo) -> AIAnalysisResult:
        """Analyzes the given code and error diagnostic information."""
        pass


class MockAIProvider(BaseAIProvider):
    """
    Deterministic mock AI provider for testing the end-to-end Module 4 pipeline
    without requiring external API keys or network connectivity.
    Generates tailored, realistic explanations and fixes based on ErrorInfo.
    """

    def analyze_error(self, code: str, error_info: ErrorInfo) -> AIAnalysisResult:
        err_type = (error_info.error_type or "").strip()
        loc_str = f"line {error_info.line_number}" if error_info.line_number else "the error location"
        ctx = error_info.code_context.strip() if error_info.code_context else ""

        # 1. IndexError (e.g., Python / JS)
        if "IndexError" in err_type or "bounds" in error_info.message.lower():
            # Try to extract variable and index from context e.g. numbers[5]
            var_match = re.search(r"([A-Za-z0-9_]+)\[(.*?)\]", ctx)
            var_name = var_match.group(1) if var_match else "collection"
            idx_name = var_match.group(2) if var_match else "index"

            return AIAnalysisResult(
                root_cause=(
                    f"The program attempted to access an element at index '{idx_name}' in '{var_name}', "
                    f"which exceeds the valid boundary of the list. In {error_info.language}, indices are 0-based, "
                    f"meaning valid indices range from 0 to len({var_name}) - 1."
                ),
                suggested_fix=(
                    f"# Check that the index is within bounds before accessing:\n"
                    f"if len({var_name}) > {idx_name}:\n"
                    f"    print({var_name}[{idx_name}])\n"
                    f"else:\n"
                    f"    print(f'Error: Index {idx_name} is out of bounds for {var_name} (length {{len({var_name})}}).')"
                ),
                explanation=(
                    f"By verifying that '{idx_name}' is strictly less than len({var_name}), "
                    f"the program safely handles out-of-bounds scenarios without crashing with an unhandled exception."
                ),
                debugging_guidance=[
                    f"Verify the length of '{var_name}' using len({var_name}) before indexing.",
                    "Remember that a list with N items has valid indices from 0 up to N - 1.",
                    "If iterating through elements, prefer a direct for-each loop instead of indexing.",
                    "Wrap risky indexing in a try...except IndexError block when working with dynamic input.",
                ],
                optimized_solution=(
                    f"# Idiomatic alternative: iterate through elements directly without explicit indexing\n"
                    f"for item in {var_name}:\n"
                    f"    print(item)"
                ),
            )

        # 2. ZeroDivisionError
        elif "ZeroDivision" in err_type or "divide by zero" in error_info.message.lower() or "/ by zero" in error_info.message:
            return AIAnalysisResult(
                root_cause=(
                    f"A division or modulo operation on {loc_str} attempted to divide by zero. "
                    "Division by zero is mathematically undefined and triggers a fatal runtime exception."
                ),
                suggested_fix=(
                    "# Guard against a zero divisor before dividing:\n"
                    "divisor = b  # your divisor variable\n"
                    "if divisor != 0:\n"
                    "    result = a / divisor\n"
                    "else:\n"
                    "    result = 0.0  # Safe fallback or raise a handled error"
                ),
                explanation=(
                    "Checking that the denominator is not zero prior to division prevents the runtime crash "
                    "and provides an explicit fallback value or message."
                ),
                debugging_guidance=[
                    "Validate user input and divisor variables before performing division or modulo operations.",
                    "Inspect the calculation path that computed the divisor to ensure it does not unintentionally produce zero.",
                    "Use math.isclose(divisor, 0.0) when comparing floating-point numbers.",
                ],
                optimized_solution=(
                    "# Clean defensive fallback function\n"
                    "def safe_divide(numerator, denominator, default=0.0):\n"
                    "    return numerator / denominator if denominator != 0 else default"
                ),
            )

        # 3. Java IncompatibleTypes / TypeMismatch
        elif "IncompatibleTypes" in err_type or "cannot be converted" in error_info.message:
            return AIAnalysisResult(
                root_cause=(
                    f"A type mismatch occurred on {loc_str}. The compiler encountered a value whose type "
                    "cannot be implicitly converted to the destination variable's declared type."
                ),
                suggested_fix=(
                    "// Ensure the value matches the variable's declared type, or parse/convert explicitly:\n"
                    "// If converting a String to an integer:\n"
                    "int value = Integer.parseInt(\"123\");\n\n"
                    "// Or declare the variable with the matching type:\n"
                    "String text = \"hello\";"
                ),
                explanation=(
                    f"In statically typed languages like {error_info.language}, types must match or be explicitly converted. "
                    "Using wrapper parsing methods like Integer.parseInt() or matching variable types ensures type safety."
                ),
                debugging_guidance=[
                    "Check the variable's declared type against the return type of the assigned expression.",
                    "Use appropriate parsing methods (e.g. Integer.parseInt, Double.parseDouble) when converting strings.",
                    "Ensure method signatures match expected parameter types.",
                ],
                optimized_solution=(
                    "// Use try-catch when parsing strings that may contain invalid numbers:\n"
                    "try {\n"
                    "    int num = Integer.parseInt(strInput);\n"
                    "} catch (NumberFormatException e) {\n"
                    "    System.err.println(\"Invalid number format: \" + e.getMessage());\n"
                    "}"
                ),
            )

        # 4. NullPointerException
        elif "NullPointer" in err_type or "null" in error_info.message.lower():
            return AIAnalysisResult(
                root_cause=(
                    f"A NullPointerException occurred on {loc_str}. The code attempted to invoke a method, "
                    "access a field, or index into an object reference that currently points to null."
                ),
                suggested_fix=(
                    "// Add a null-check before dereferencing the object:\n"
                    "if (obj != null) {\n"
                    "    obj.performAction();\n"
                    "} else {\n"
                    "    System.out.println(\"Warning: Reference is null.\");\n"
                    "}"
                ),
                explanation=(
                    "Guarding references with a null check prevents invoking methods on uninstantiated objects."
                ),
                debugging_guidance=[
                    "Trace the origin of the object to see where it was supposed to be initialized.",
                    "In modern Java, consider using Optional<T> to represent potentially absent values.",
                    "Use objects with sensible defaults instead of leaving references set to null.",
                ],
                optimized_solution=(
                    "// Modern Java Optional pattern:\n"
                    "Optional.ofNullable(obj).ifPresent(o -> o.performAction());"
                ),
            )

        # 5. SyntaxError
        elif "SyntaxError" in err_type or "syntax" in error_info.error_category.lower():
            return AIAnalysisResult(
                root_cause=(
                    f"The {error_info.language} parser encountered a syntax error on {loc_str}. "
                    f"Details: {error_info.message}. This is typically caused by a missing colon, bracket, "
                    "semicolon, or malformed statement."
                ),
                suggested_fix=(
                    f"# Check the syntax around {loc_str}:\n"
                    f"# Context: {ctx}\n"
                    "# Ensure all opening parentheses, quotes, and block colons have valid matches."
                ),
                explanation=(
                    "Correcting the malformed token aligns the code with the language's grammar rules."
                ),
                debugging_guidance=[
                    f"Carefully examine the characters immediately before and after {loc_str}.",
                    "Check for unclosed parentheses, missing commas between arguments, or missing colons/semicolons.",
                    "Review indentation if using Python.",
                ],
                optimized_solution=(
                    "# Always use an editor with syntax validation (F7) to catch grammar errors early."
                ),
            )

        # 6. Logical / Assertion Errors
        elif "Assertion" in err_type or "Logical" in error_info.error_category:
            return AIAnalysisResult(
                root_cause=(
                    f"A logical assertion failed on {loc_str}. The assertion condition evaluated to false, "
                    "indicating that a program invariant or expected test condition was violated."
                ),
                suggested_fix=(
                    f"# Inspect the values participating in the assertion on {loc_str}:\n"
                    f"# Context: {ctx}\n"
                    "# Verify intermediate calculations to identify why the expected condition failed."
                ),
                explanation=(
                    "Assertions act as contracts in code. Resolving the logical flaw in the preceding "
                    "algorithm restores the expected invariant."
                ),
                debugging_guidance=[
                    "Print or log intermediate values before the assert statement to inspect runtime state.",
                    "Check boundary conditions and edge cases in the logic.",
                    "Ensure test expectations match the intended business logic.",
                ],
                optimized_solution=(
                    "# Include descriptive error messages in assertions:\n"
                    "assert actual_value == expected_value, f'Expected {expected_value}, but got {actual_value}'"
                ),
            )

        # 7. Generic Fallback
        else:
            return AIAnalysisResult(
                root_cause=(
                    f"The program halted with a {error_info.error_category} ({err_type or 'Error'}) on {loc_str}. "
                    f"Diagnostic message: {error_info.message}."
                ),
                suggested_fix=(
                    f"# Review and adjust the statement at {loc_str}:\n"
                    f"# Code context: {ctx}\n"
                    "# Verify arguments, types, and error handling for this operation."
                ),
                explanation=(
                    f"Addressing the underlying condition reported in '{error_info.message}' "
                    "allows execution to complete normally."
                ),
                debugging_guidance=[
                    f"Inspect the traceback or compiler message around {loc_str}.",
                    "Ensure all dependencies, imports, and variables are properly initialized.",
                    "Run validation (F7) to verify structural syntax before executing.",
                ],
                optimized_solution=(
                    "# Consider wrapping critical operations in defensive error-handling blocks."
                ),
            )
