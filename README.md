# 🎙️ Meeting Summarizer

> An AI-powered meeting intelligence tool that transcribes audio recordings and generates structured summaries with action items.

---

## ✨ Features

- 🎤 **Audio Transcription** — Upload MP3, WAV, or M4A files; Whisper converts them to text
- 🤖 **AI Summarization** — Google Gemini 2.5 Flash generates concise executive summaries
- ✅ **Action Item Extraction** — Pulls out concrete tasks and commitments from the meeting
- 📊 **Hierarchical Summarization** — Long meetings are chunked and summarized in sections, then merged
- 💾 **JSON Export** — Every result is saved locally and available for download
- 📂 **History Sidebar** — Browse all past summaries from the sidebar

---

## 🏗️ Architecture

```
User → Upload Audio
         ↓
    Streamlit UI (app.py)
         ↓
    Save to uploads/
         ↓
    Whisper API → Full Transcript
         ↓
    ┌────────────────────────────┐
    │  Is transcript > 2500 words? │
    └────────────────────────────┘
         ↓ No                  ↓ Yes
    Direct Gemini        Chunk Transcript
    Summarization              ↓
         ↓            Summarize Each Chunk
         └──────────────────┐
                            ↓
                    Gemini Final Summary
                            ↓
              { summary, action_items }
                            ↓
                    Save to outputs/
                            ↓
                     Display in UI
```

---

## 📁 Project Structure

```
meeting_summarizer/
│
├── app.py                     # Streamlit frontend
│
├── services/
│   ├── __init__.py
│   ├── transcriber.py         # OpenAI Whisper API integration
│   ├── chunker.py             # Transcript splitting logic
│   ├── summarizer.py          # Gemini summarization (direct + hierarchical)
│   └── storage.py             # JSON output persistence
│
├── uploads/                   # Temp audio files (gitignored)
├── outputs/                   # Generated JSON summaries (gitignored)
├── sample_audio/              # Sample audio files for testing
│
├── prompts.py                 # LLM prompt templates
├── requirements.txt
├── .env.example               # API key template
├── .env                       # Your secrets (gitignored)
└── README.md
```

---

## 🚀 Setup

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
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
OPENAI_API_KEY=sk-...          # https://platform.openai.com/api-keys
GOOGLE_API_KEY=AIza...         # https://aistudio.google.com/app/apikey
```

### 5. Run the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Testing

Upload any `.mp3`, `.wav`, or `.m4a` file. Sample audio files can be placed in `sample_audio/`.

A few options for test audio:
- Record a short meeting using your phone
- Use a free sample from [freesound.org](https://freesound.org)
- Convert a YouTube video using yt-dlp

---

## 📄 Output Format

Each processed meeting is saved as a JSON file in `outputs/`:

```json
{
  "filename": "weekly_meeting.mp3",
  "created_at": "2026-07-15T19:42:00",
  "transcript": "Full meeting transcript...",
  "summary": "Executive summary of the meeting...",
  "action_items": [
    "Prepare deployment plan by Friday",
    "Review API documentation",
    "Schedule follow-up meeting with the client"
  ]
}
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| Speech-to-Text | [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) |
| Summarization | [Google Gemini 2.5 Flash](https://ai.google.dev/) |
| Language | Python 3.11+ |
| Storage | Local JSON files |
| Config | python-dotenv |

---

## 🔑 API Keys

| Key | Where to Get |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `GOOGLE_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

---

## 📝 Notes

- Whisper API supports files up to **25 MB**. For larger files, consider compressing the audio first.
- Gemini 2.5 Flash is used for cost-efficiency and speed.
- The chunking threshold is set to **2500 words** (~19 minutes of speech at average pace).

---

*Built with ❤️ using Streamlit, OpenAI Whisper, and Google Gemini.*
