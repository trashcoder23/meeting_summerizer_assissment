"""
services/transcriber.py
-----------------------
Converts an audio file into text using the OpenAI Whisper API.

Responsibility:
    ONLY audio → transcript conversion. No summarization logic here.

Usage:
    from services.transcriber import transcribe_audio
    transcript = transcribe_audio("uploads/meeting.mp3")
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file using OpenAI Whisper API.

    Args:
        audio_path: Absolute or relative path to the audio file.
                    Supported formats: mp3, wav, m4a, mp4, webm, ogg.

    Returns:
        Full transcript as a plain string.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If the OPENAI_API_KEY is not set.
        openai.APIError: On API-level failures (propagated to caller).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Please add it to your .env file."
        )

    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",  # returns a plain string
        )

    # response is a plain string when response_format="text"
    return response.strip()
