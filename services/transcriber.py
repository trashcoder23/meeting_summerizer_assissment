"""
services/transcriber.py
-----------------------
Converts an audio file into text using the Google Cloud Speech-to-Text API v1.

Why chunking?
    The synchronous Speech-to-Text endpoint only accepts audio up to 60 seconds.
    Meeting recordings are much longer, so we:
      1. Convert the audio to 16 kHz mono WAV (required format)
      2. Split it into ~50-second chunks using pydub
      3. Transcribe each chunk individually
      4. Concatenate all partial transcripts into one full transcript

Authentication:
    Uses a plain API key (GOOGLE_SPEECH_API_KEY) via query parameter.
    No service account or ADC needed.

Usage:
    from services.transcriber import transcribe_audio
    transcript = transcribe_audio("uploads/meeting.mp3")
"""

import os
import base64
import tempfile
import requests
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
_SPEECH_API_URL = "https://speech.googleapis.com/v1/speech:recognize"
_CHUNK_DURATION_MS = 50_000   # 50 seconds — safely under the 60 s API limit
_SAMPLE_RATE_HZ = 16_000      # 16 kHz — optimal for speech recognition


# ── Internal helpers ───────────────────────────────────────────────────────────

def _convert_to_wav(audio_path: str) -> str:
    """
    Convert any supported audio file to a 16 kHz mono WAV.

    Google Speech-to-Text requires LINEAR16 encoding. pydub handles the
    conversion from mp3, m4a, wav, etc.

    Args:
        audio_path: Path to the source audio file.

    Returns:
        Path to a temporary WAV file (caller must delete it).
    """
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1).set_frame_rate(_SAMPLE_RATE_HZ)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio.export(tmp.name, format="wav")
    tmp.close()
    return tmp.name


def _split_audio(wav_path: str) -> list[AudioSegment]:
    """
    Split a WAV file into fixed-duration chunks.

    Args:
        wav_path: Path to a converted WAV file.

    Returns:
        List of AudioSegment chunks, each at most _CHUNK_DURATION_MS long.
    """
    audio = AudioSegment.from_wav(wav_path)
    chunks = []
    for start_ms in range(0, len(audio), _CHUNK_DURATION_MS):
        chunks.append(audio[start_ms: start_ms + _CHUNK_DURATION_MS])
    return chunks


def _transcribe_chunk(chunk: AudioSegment, api_key: str) -> str:
    """
    Send one audio chunk to the Google Speech-to-Text API and return its transcript.

    Args:
        chunk:   AudioSegment of at most 50 seconds.
        api_key: Google Cloud API key with Speech-to-Text enabled.

    Returns:
        Transcript string for this chunk (may be empty if no speech detected).

    Raises:
        requests.HTTPError: On non-2xx API responses.
        RuntimeError: If the API returns an unexpected response structure.
    """
    # Export chunk to a temporary WAV file and read it as bytes
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    chunk.export(tmp.name, format="wav")
    tmp.close()

    try:
        with open(tmp.name, "rb") as f:
            audio_bytes = f.read()
    finally:
        os.unlink(tmp.name)

    # Base64-encode the raw audio bytes for the JSON payload
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": _SAMPLE_RATE_HZ,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True,
            "model": "latest_long",  # best accuracy for meeting/conversation audio
        },
        "audio": {
            "content": audio_b64,
        },
    }

    response = requests.post(
        f"{_SPEECH_API_URL}?key={api_key}",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()

    # Each "result" holds one utterance; take the top alternative
    parts = []
    for result in data.get("results", []):
        alternatives = result.get("alternatives", [])
        if alternatives:
            parts.append(alternatives[0].get("transcript", ""))

    return " ".join(parts)


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using Google Cloud Speech-to-Text.

    Handles any length of audio by splitting it into 50-second chunks,
    transcribing each, and concatenating the results.

    Args:
        audio_path: Path to the audio file (mp3, wav, m4a supported).

    Returns:
        Full transcript as a plain string.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If GOOGLE_SPEECH_API_KEY is not set in the environment.
        requests.HTTPError: On Speech-to-Text API errors (propagated to caller).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    api_key = os.getenv("GOOGLE_SPEECH_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_SPEECH_API_KEY is not set. "
            "Please add it to your .env file."
        )

    # Step 1: Convert to 16 kHz mono WAV
    wav_path = _convert_to_wav(audio_path)

    try:
        # Step 2: Split into 50-second chunks
        chunks = _split_audio(wav_path)

        # Step 3: Transcribe each chunk and collect results
        transcript_parts = []
        for chunk in chunks:
            text = _transcribe_chunk(chunk, api_key)
            if text.strip():
                transcript_parts.append(text.strip())

        return " ".join(transcript_parts)

    finally:
        # Always clean up the temporary WAV file
        if os.path.exists(wav_path):
            os.unlink(wav_path)
