"""
services/chunker.py
-------------------
Splits large meeting transcripts into manageable chunks for hierarchical
summarization.

Why chunking?
    LLMs have context window limits. Very long meetings (1+ hours) produce
    transcripts that exceed those limits. Chunking allows us to summarize
    each section and then combine the section summaries into a final output.

Strategy:
    1. Split transcript by sentence boundaries (". ", "? ", "! ").
    2. Accumulate sentences into a chunk until the word count exceeds the
       threshold (default: 2500 words).
    3. Never break mid-sentence.

Usage:
    from services.chunker import split_transcript, needs_chunking

    if needs_chunking(transcript):
        chunks = split_transcript(transcript)
    else:
        chunks = [transcript]
"""

import re

# ── Configuration ──────────────────────────────────────────────────────────────
# Whisper transcripts average ~130 words/minute of speech.
# Gemini Flash has a large context window, but we keep chunks conservative
# (~2500 words) for reliable, focused summaries.
CHUNK_WORD_LIMIT = 2500
SMALL_TRANSCRIPT_THRESHOLD = 2500  # transcripts below this go directly to Gemini


def needs_chunking(transcript: str) -> bool:
    """
    Returns True if the transcript exceeds the small-transcript threshold
    and should be split into chunks before summarization.
    """
    word_count = len(transcript.split())
    return word_count > SMALL_TRANSCRIPT_THRESHOLD


def split_transcript(transcript: str, chunk_word_limit: int = CHUNK_WORD_LIMIT) -> list[str]:
    """
    Split a transcript into chunks, respecting sentence boundaries.

    Args:
        transcript:       The full meeting transcript as a plain string.
        chunk_word_limit: Maximum words per chunk (default: 2500).

    Returns:
        A list of transcript chunk strings. Each chunk is a coherent
        segment of the original text with no mid-sentence breaks.
    """
    # Split on sentence-ending punctuation followed by whitespace.
    # We keep the delimiter attached to the preceding sentence.
    sentences = re.split(r"(?<=[.!?])\s+", transcript.strip())

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_word_count: int = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())

        # If adding this sentence would exceed the limit, flush current chunk.
        if current_word_count + sentence_word_count > chunk_word_limit and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0

        current_chunk.append(sentence)
        current_word_count += sentence_word_count

    # Flush any remaining sentences as the last chunk.
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
