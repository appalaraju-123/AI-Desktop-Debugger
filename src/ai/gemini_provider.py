"""
Gemini AI provider implementation using the official google-genai SDK.
Connects the AI-Based Intelligent Desktop Debugger to Google Gemini LLMs.
"""

import json
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.ai.base_provider import BaseAIProvider
from src.ai.models import AIAnalysisResult
from src.ai.prompt_builder import PromptBuilder
from src.core.error_classifier import ErrorInfo


class GeminiAnalysisSchema(BaseModel):
    """Structured response schema for Gemini error analysis."""

    root_cause: str = Field(description="Plain-language explanation of why the failure occurred.")
    suggested_fix: str = Field(description="Minimal corrected code snippet that resolves the error.")
    explanation: str = Field(description="Detailed explanation of why the suggested fix works.")
    debugging_guidance: list[str] = Field(
        default_factory=list,
        description="Actionable debugging tips, preventative checks, and next steps.",
    )
    optimized_solution: str = Field(
        default="",
        description="Alternative, idiomatic, or best-practice implementation.",
    )


class GeminiProvider(BaseAIProvider):
    """
    Real Gemini AI analysis provider implementing the BaseAIProvider interface.
    Uses the official google-genai SDK to generate diagnoses and fixes.
    """

    DEFAULT_MODEL = "gemini-2.5-flash"
    FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        Initializes the GeminiProvider.

        Args:
            api_key: Optional Gemini API key. If omitted, loaded from GEMINI_API_KEY env var.
            model: Gemini model identifier, defaults to 'gemini-2.5-flash'.
        """
        # Ensure environment variables from .env are loaded
        load_dotenv()

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please provide an API key or configure GEMINI_API_KEY in your .env file."
            )

        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    def analyze_error(self, code: str, error_info: ErrorInfo) -> AIAnalysisResult:
        """
        Analyzes code and error diagnostics using the Gemini API and converts
        the response into a structured AIAnalysisResult.
        """
        prompt = PromptBuilder.build_diagnostic_prompt(code, error_info)

        config = types.GenerateContentConfig(
            system_instruction=PromptBuilder.SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=GeminiAnalysisSchema,
            temperature=0.2,
        )

        response = self._generate_with_fallback(prompt, config)
        return self._convert_to_analysis_result(response)

    def _generate_with_fallback(
        self,
        prompt: str,
        config: types.GenerateContentConfig,
    ):
        """
        Attempts generation with self.model (gemini-2.5-flash). If the model is
        retired or unavailable for new users (404) or experiencing temporary overload (503),
        gracefully falls back to active alternative flash models.
        """
        models_to_try = [self.model]
        for fb in self.FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error: Exception | None = None
        for model_name in models_to_try:
            try:
                return self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                # If model is unavailable (404, retirement, or 503 overload), try next candidate
                if "404" in err_str or "no longer available" in err_str or "503" in err_str:
                    continue
                # For auth errors (400, 401, 403), do not retry across models
                raise exc

        if last_error:
            raise last_error
        raise RuntimeError("No response received from Gemini API.")

    def _convert_to_analysis_result(self, response) -> AIAnalysisResult:
        """Parses the Gemini response into an AIAnalysisResult instance."""
        raw_text = getattr(response, "text", "") or ""
        clean_text = raw_text.strip()

        # Strip markdown fences if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text).strip()

        try:
            data = json.loads(clean_text)
            root_cause = str(data.get("root_cause", "")).strip()
            suggested_fix = str(data.get("suggested_fix", "")).strip()
            explanation = str(data.get("explanation", "")).strip()
            guidance = data.get("debugging_guidance", [])
            if isinstance(guidance, list):
                debugging_guidance = [str(item).strip() for item in guidance if item]
            elif isinstance(guidance, str):
                debugging_guidance = [g.strip() for g in guidance.split("\n") if g.strip()]
            else:
                debugging_guidance = []

            optimized_solution = str(data.get("optimized_solution", "")).strip()

            return AIAnalysisResult(
                root_cause=root_cause,
                suggested_fix=suggested_fix,
                explanation=explanation,
                debugging_guidance=debugging_guidance,
                optimized_solution=optimized_solution,
                raw_response=raw_text,
            )
        except Exception:
            # Fallback if response is plain text or unparseable JSON
            return AIAnalysisResult(
                root_cause="Gemini diagnostic feedback received.",
                suggested_fix=clean_text,
                explanation="AI-generated diagnosis and recommendations.",
                debugging_guidance=[],
                optimized_solution="",
                raw_response=raw_text,
            )
