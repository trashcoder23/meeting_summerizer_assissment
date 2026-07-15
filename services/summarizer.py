"""
services/summarizer.py
----------------------
Generates structured meeting summaries using Google Gemini 2.5 Flash.

Uses the new `google-genai` SDK (google.genai), which replaced the
deprecated `google-generativeai` (google.generativeai) package.

Implements hierarchical summarization:
  - Short transcripts  → single Gemini call → final JSON
  - Long transcripts   → summarize each chunk → combine → final Gemini call

Usage:
    from services.summarizer import summarize
    result = summarize(transcript)
    # result = {"summary": "...", "action_items": ["...", "..."]}
"""

import os
import json
import re

from google import genai
from dotenv import load_dotenv

from services.chunker import needs_chunking, split_transcript
from prompts import CHUNK_SUMMARY_PROMPT, FINAL_SUMMARY_PROMPT

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
_MODEL_NAME = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Initialize and return the Gemini client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Please add it to your .env file."
        )
    return genai.Client(api_key=api_key)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the text response.

    Args:
        prompt: The full prompt string.

    Returns:
        Raw text response from the model.

    Raises:
        RuntimeError: If the model returns an empty or blocked response.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response. "
            "The content may have been blocked by safety filters."
        )
    return response.text.strip()


def _parse_json_response(raw: str) -> dict:
    """
    Robustly parse a JSON object from a Gemini response string.

    Gemini sometimes wraps JSON in markdown code fences (```json ... ```).
    This strips those fences before parsing.

    Args:
        raw: Raw text response from Gemini.

    Returns:
        Parsed dict with keys "summary" and "action_items".

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: try to extract a JSON object using regex
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    raise ValueError(
        f"Could not parse a valid JSON response from Gemini.\n"
        f"Raw response:\n{raw}"
    )


def _summarize_chunk(chunk: str) -> str:
    """
    Produce a plain-text summary of a single transcript chunk.

    Args:
        chunk: One segment of the full transcript.

    Returns:
        A concise paragraph summarizing the key points.
    """
    prompt = CHUNK_SUMMARY_PROMPT.format(chunk=chunk)
    return _call_gemini(prompt)


def _generate_final_summary(chunk_summaries: list[str]) -> dict:
    """
    Combine chunk summaries into a final structured output via Gemini.

    Args:
        chunk_summaries: List of plain-text summaries, one per transcript chunk.

    Returns:
        Dict with keys:
            "summary"      - Executive summary string
            "action_items" - List of action item strings
    """
    combined = "\n\n---\n\n".join(
        f"Section {i + 1}:\n{s}" for i, s in enumerate(chunk_summaries)
    )
    prompt = FINAL_SUMMARY_PROMPT.format(combined_summaries=combined)
    raw = _call_gemini(prompt)
    return _parse_json_response(raw)


# ── Public API ─────────────────────────────────────────────────────────────────

def summarize(transcript: str) -> dict:
    """
    Generate a structured summary from a meeting transcript.

    Automatically chooses between:
      - Direct summarization (short transcripts)
      - Hierarchical summarization (long transcripts)

    Args:
        transcript: Full meeting transcript as a plain string.

    Returns:
        Dict with keys:
            "summary"      - Executive summary string
            "action_items" - List of action item strings
    """
    if needs_chunking(transcript):
        # Hierarchical path: chunk → summarize each → final merge
        chunks = split_transcript(transcript)
        chunk_summaries = [_summarize_chunk(chunk) for chunk in chunks]
        return _generate_final_summary(chunk_summaries)
    else:
        # Direct path: send full transcript straight to Gemini
        return _generate_final_summary([transcript])
