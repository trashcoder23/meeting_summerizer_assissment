"""
services/storage.py
-------------------
Saves meeting summary results as timestamped JSON files and
loads past outputs for the history view.

Output format:
    outputs/meeting_YYYYMMDD_HHMMSS.json

Usage:
    from services.storage import save_output, load_all_outputs
    path = save_output(filename, transcript, summary, action_items)
    history = load_all_outputs()
"""

import json
import os
from datetime import datetime

OUTPUTS_DIR = "outputs"


def _ensure_outputs_dir() -> None:
    """Create the outputs directory if it does not exist."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def save_output(
    filename: str,
    transcript: str,
    summary: str,
    action_items: list[str],
) -> str:
    """
    Save the meeting summary result as a JSON file.

    Args:
        filename:     Original uploaded audio filename.
        transcript:   Full meeting transcript.
        summary:      Executive summary string.
        action_items: List of action item strings.

    Returns:
        Absolute path to the saved JSON file.
    """
    _ensure_outputs_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"meeting_{timestamp}.json"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)

    data = {
        "filename": filename,
        "created_at": datetime.now().isoformat(),
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def load_all_outputs() -> list[dict]:
    """
    Load all past meeting summary JSON files from the outputs directory.

    Returns:
        List of dicts (parsed JSON), sorted newest-first.
        Returns an empty list if the outputs directory does not exist
        or contains no valid JSON files.
    """
    _ensure_outputs_dir()

    results = []
    for fname in sorted(os.listdir(OUTPUTS_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(OUTPUTS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_output_file"] = fname  # attach filename for display
                results.append(data)
        except (json.JSONDecodeError, OSError):
            # Skip corrupted or unreadable files silently
            continue

    return results
