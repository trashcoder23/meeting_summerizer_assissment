"""
services/transcriber.py
-----------------------
Converts an audio file into text using the Google Cloud Speech-to-Text API v1.

Pipeline:
  1. Find ffmpeg (winget install or PATH)
  2. Use ffmpeg subprocess directly to convert audio → 16kHz mono WAV
  3. Split WAV into 50-second chunks with pydub
  4. Send each chunk to Speech-to-Text API
  5. Concatenate transcripts

Usage:
    from services.transcriber import transcribe_audio
    transcript = transcribe_audio("uploads/meeting.mp3")
"""

import os
import glob
import shutil
import base64
import tempfile
import subprocess
import requests
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
_SPEECH_API_URL = "https://speech.googleapis.com/v1/speech:recognize"
_CHUNK_DURATION_MS = 50_000   # 50 s — safely under the 60 s API limit
_SAMPLE_RATE_HZ = 16_000      # 16 kHz — required by Speech-to-Text


def _find_ffmpeg() -> str:
    """Return the absolute path to ffmpeg.exe, searching PATH then winget."""
    # 1. Env var override
    env = os.getenv("FFMPEG_PATH")
    if env and os.path.isfile(env):
        return env

    # 2. System PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 3. Winget default install location
    winget_base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.isdir(winget_base):
        matches = glob.glob(os.path.join(winget_base, "**", "ffmpeg.exe"), recursive=True)
        if matches:
            return matches[0]

    raise RuntimeError(
        "ffmpeg not found.\n"
        "Install it with:  winget install Gyan.FFmpeg\n"
        "Or set FFMPEG_PATH in your .env file."
    )


# Resolve once at import time
_FFMPEG = _find_ffmpeg()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _convert_to_wav(audio_path: str) -> str:
    """
    Convert audio to 16 kHz mono WAV using ffmpeg subprocess directly.
    Returns path to a temp WAV file (caller must delete it).
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    result = subprocess.run(
        [_FFMPEG, "-y", "-i", audio_path,
         "-ar", str(_SAMPLE_RATE_HZ),
         "-ac", "1",
         tmp.name],
        capture_output=True,
        timeout=300,
    )

    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(
            f"ffmpeg conversion failed:\n{result.stderr.decode(errors='replace')}"
        )

    return tmp.name


def _split_wav(wav_path: str) -> list[AudioSegment]:
    """Split a WAV into 50-second chunks using pydub."""
    audio = AudioSegment.from_wav(wav_path)
    return [
        audio[start: start + _CHUNK_DURATION_MS]
        for start in range(0, len(audio), _CHUNK_DURATION_MS)
    ]


def _transcribe_chunk(chunk: AudioSegment, api_key: str) -> str:
    """Send one audio chunk to Google Speech-to-Text and return its transcript."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    chunk.export(tmp.name, format="wav")
    tmp.close()

    try:
        with open(tmp.name, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    finally:
        os.unlink(tmp.name)

    payload = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": _SAMPLE_RATE_HZ,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True,
            "model": "latest_long",
        },
        "audio": {"content": audio_b64},
    }

    response = requests.post(
        f"{_SPEECH_API_URL}?key={api_key}",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    parts = []
    for result in response.json().get("results", []):
        alts = result.get("alternatives", [])
        if alts:
            parts.append(alts[0].get("transcript", ""))

    return " ".join(parts)


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file using Google Cloud Speech-to-Text.

    Args:
        audio_path: Path to mp3, wav, or m4a file.

    Returns:
        Full transcript string.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    api_key = os.getenv("GOOGLE_SPEECH_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_SPEECH_API_KEY is not set in your .env file.")

    wav_path = _convert_to_wav(audio_path)

    try:
        chunks = _split_wav(wav_path)
        parts = [
            text for chunk in chunks
            if (text := _transcribe_chunk(chunk, api_key).strip())
        ]
        return " ".join(parts)
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)
