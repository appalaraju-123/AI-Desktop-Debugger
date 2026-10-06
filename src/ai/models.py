"""
Data models for AI-based analysis and fix recommendation.
"""

from dataclasses import dataclass, field


@dataclass
class AIAnalysisResult:
    """Encapsulates the structured AI diagnosis and recommended fix."""

    root_cause: str  # 1. Plain-language root cause explanation
    suggested_fix: str  # 2. Corrected code snippet (display-only)
    explanation: str  # Why the fix works
    debugging_guidance: list[str] = field(default_factory=list)  # 3. Actionable debugging tips
    optimized_solution: str = ""  # 4. Alternative/idiomatic solution
    raw_response: str = ""  # Full raw response text for reference
