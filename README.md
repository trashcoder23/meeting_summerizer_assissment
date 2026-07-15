# 🎙️ Meeting Summarizer

> **AI-powered meeting intelligence** — Upload a recording, get a full transcript, executive summary, and action items in seconds.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## 📌 Overview

Meeting Summarizer is a Streamlit web application that automates the most tedious part of meetings — taking notes. Upload any meeting audio file and the app will:

1. **Transcribe** the recording using Google Cloud Speech-to-Text
2. **Summarize** the discussion using Google Gemini 2.5 Flash
3. **Extract action items** — concrete tasks and commitments
4. **Save everything** as a structured JSON file for future reference

Long meetings are handled via **hierarchical summarization** — the transcript is automatically split into sections, each section is summarized independently, then all section summaries are merged into one final cohesive output. This ensures accuracy and reliability regardless of meeting length.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎤 **Audio Upload** | Supports MP3, WAV, M4A formats |
| 📝 **Full Transcript** | Complete word-for-word transcription |
| 📋 **Executive Summary** | Concise summary under 250 words |
| ✅ **Action Items** | Extracted tasks and commitments |
| 🧩 **Hierarchical Summarization** | Handles long meetings reliably |
| 💾 **JSON Export** | Download structured report |
| 📂 **History Sidebar** | Browse all past summaries |
| 🌙 **Dark UI** | Clean, professional dark interface |

---

## 🏗️ Architecture

```
User Uploads Audio
        │
        ▼
  Streamlit UI
        │
        ▼
 Save to uploads/
        │
        ▼
  ffmpeg converts to
  16kHz mono WAV
        │
        ▼
 Split into 50s chunks
        │
        ▼
 Google Speech-to-Text API
 (each chunk → transcript)
        │
        ▼
  Full Transcript
        │
   ┌────┴────┐
   │         │
≤2500      >2500
 words      words
   │         │
   ▼         ▼
 Direct   Chunk &
 Gemini   Summarize
   │      Each Part
   └────┬────┘
        │
        ▼
  Gemini Final Summary
        │
        ▼
  { summary, action_items }
        │
        ▼
  Save to outputs/
        │
        ▼
  Display in UI
```

### Why Hierarchical Summarization?

Meeting transcripts can be thousands of words long. Sending everything to an LLM at once risks:
- Exceeding context limits
- Losing detail from earlier parts of the meeting
- Higher latency and cost

Instead, we chunk the transcript → summarize each chunk → merge all chunk summaries → produce one final structured output. This is more scalable, reliable, and produces better quality results.

---

## 📁 Project Structure

```
meeting_summarizer/
│
├── app.py                  # Streamlit frontend (UI, routing, pipeline)
│
├── services/
│   ├── __init__.py
│   ├── transcriber.py      # Google Speech-to-Text + ffmpeg audio conversion
│   ├── chunker.py          # Sentence-boundary transcript splitting
│   ├── summarizer.py       # Google Gemini summarization (direct + hierarchical)
│   └── storage.py          # JSON output persistence and history loading
│
├── uploads/                # Temporary audio files (gitignored)
├── outputs/                # Generated JSON summaries (gitignored)
├── sample_audio/           # Sample audio files for testing
│
├── prompts.py              # Centralized LLM prompt templates
├── requirements.txt        # Python dependencies
├── .env.example            # API key template (commit this, not .env)
├── .env                    # Your actual secrets (gitignored)
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.11+
- ffmpeg installed ([winget install Gyan.FFmpeg](https://winget.run/pkg/Gyan/FFmpeg) on Windows)
- Google AI API key (for Gemini)
- Google Cloud API key (for Speech-to-Text)

### 1. Clone the Repository

```bash
git clone https://github.com/trashcoder23/meeting_summerizer_assissment.git
cd meeting_summerizer_assissment
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS/Linux
```

Edit `.env` and fill in your keys:

```env
GOOGLE_API_KEY=AIza...           # Gemini — https://aistudio.google.com/app/apikey
GOOGLE_SPEECH_API_KEY=AIza...    # Speech-to-Text — https://console.cloud.google.com/apis/credentials
```

> **Note:** For `GOOGLE_SPEECH_API_KEY`, go to Google Cloud Console → APIs & Services → Credentials, create an API key, and enable the **Cloud Speech-to-Text API** on your project.

### 5. Run the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Usage

1. Open the app in your browser
2. Click **Upload Meeting Recording** and select an `.mp3`, `.wav`, or `.m4a` file
3. Click **🚀 Generate Summary**
4. Wait for transcription and summarization to complete
5. View the **full transcript** (left column) and **summary + action items** (right column)
6. Click **⬇️ Download JSON Report** to save the structured output
7. Past summaries appear in the **sidebar** for quick reference

---

## 📄 JSON Output Format

Every processed meeting is saved to `outputs/` as a timestamped JSON file:

```json
{
  "filename": "weekly_standup.mp3",
  "created_at": "2026-07-15T19:42:00",
  "transcript": "Good morning everyone. Today we'll be discussing...",
  "summary": "The team discussed the upcoming product launch scheduled for Q3...",
  "action_items": [
    "Prepare deployment checklist by Friday — assigned to Ravi",
    "Review API documentation and share feedback",
    "Schedule client demo for next week"
  ]
}
```

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | [Streamlit](https://streamlit.io) | Web UI |
| Audio Conversion | [ffmpeg](https://ffmpeg.org) | Convert any audio → 16kHz WAV |
| Audio Chunking | [pydub](https://github.com/jiaaro/pydub) | Split WAV into 50s segments |
| Speech-to-Text | [Google Cloud Speech-to-Text v1](https://cloud.google.com/speech-to-text) | Audio → Transcript |
| LLM Summarization | [Google Gemini 2.5 Flash](https://ai.google.dev) | Transcript → Summary + Actions |
| Storage | Local JSON files | Persist outputs |
| Configuration | [python-dotenv](https://pypi.org/project/python-dotenv/) | Environment management |
| Language | Python 3.11+ | — |

---

## 🔑 API Keys Reference

| Key | Source | Used For |
|---|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) | Gemini 2.5 Flash summarization |
| `GOOGLE_SPEECH_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) | Speech-to-Text transcription |

---

## 🧠 Design Decisions

**Why Google Speech-to-Text over Whisper?**
Keeps the entire stack within the Google ecosystem. No OpenAI dependency required.

**Why hierarchical summarization instead of RAG?**
RAG adds unnecessary complexity for this use case. Hierarchical summarization (chunk → summarize → merge) achieves the same goal — handling long transcripts reliably — with far less infrastructure.

**Why ffmpeg directly instead of relying on pydub?**
pydub wraps ffmpeg but relies on it being on system PATH for format detection (ffprobe). Calling ffmpeg as a subprocess with the full resolved path is more robust, especially on Windows where PATH management is inconsistent.

**Why local JSON storage instead of a database?**
This is an assessment project. Local JSON keeps it simple, dependency-free, and easy to inspect. The storage layer is abstracted behind `services/storage.py` so swapping to a database later requires changing only that file.

---

## 📝 Notes

- The Google Speech-to-Text synchronous API supports audio up to **60 seconds**. The app automatically handles longer recordings by splitting them into 50-second chunks.
- Maximum recommended file size: **~50 MB** (very long meetings). For anything larger, compress the audio first.
- The chunking threshold for hierarchical summarization is **2,500 words** (~19 minutes of average speech).

---

*Built with ❤️ using Streamlit · Google Speech-to-Text · Google Gemini 2.5 Flash*
