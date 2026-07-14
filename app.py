"""
app.py
------
Streamlit frontend for the Meeting Summarizer.

Run with:
    streamlit run app.py
"""

import os
import json
import shutil
import tempfile
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from services.transcriber import transcribe_audio
from services.summarizer import summarize
from services.storage import save_output, load_all_outputs

load_dotenv()

# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Background ── */
    .stApp {
        background-color: #0f1117;
        color: #e8eaf0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #2a2f3e;
    }

    /* ── Header hero ── */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .hero-header h1 {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #7c9fff 0%, #a78bfa 60%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.3rem;
    }
    .hero-header p {
        color: #8b92a8;
        font-size: 1rem;
        font-weight: 400;
        margin: 0;
    }

    /* ── Cards ── */
    .card {
        background: #1a1f2e;
        border: 1px solid #2a2f3e;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #7c9fff;
        margin-bottom: 0.75rem;
    }

    /* ── Transcript box ── */
    .transcript-box {
        background: #12161f;
        border: 1px solid #2a2f3e;
        border-radius: 8px;
        padding: 1.2rem;
        max-height: 420px;
        overflow-y: auto;
        font-size: 0.875rem;
        line-height: 1.75;
        color: #c8ccd8;
        white-space: pre-wrap;
    }
    .transcript-box::-webkit-scrollbar { width: 6px; }
    .transcript-box::-webkit-scrollbar-track { background: #12161f; }
    .transcript-box::-webkit-scrollbar-thumb { background: #2a2f3e; border-radius: 3px; }

    /* ── Summary text ── */
    .summary-text {
        font-size: 0.95rem;
        line-height: 1.8;
        color: #d4d8e8;
    }

    /* ── Action item pills ── */
    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.65rem 0.85rem;
        background: #0f1117;
        border: 1px solid #2a2f3e;
        border-left: 3px solid #7c9fff;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
        color: #c8ccd8;
        line-height: 1.5;
    }
    .action-icon {
        color: #7c9fff;
        font-size: 0.85rem;
        margin-top: 1px;
        flex-shrink: 0;
    }

    /* ── Upload zone ── */
    [data-testid="stFileUploader"] {
        background: #1a1f2e;
        border: 2px dashed #2a3550;
        border-radius: 12px;
        padding: 1rem;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #7c9fff;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c9fff, #a78bfa);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.88;
    }

    /* ── Section divider ── */
    .section-divider {
        border: none;
        border-top: 1px solid #2a2f3e;
        margin: 1.5rem 0;
    }

    /* ── Stat badge ── */
    .stat-badge {
        display: inline-block;
        background: #1a1f2e;
        border: 1px solid #2a2f3e;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.78rem;
        color: #8b92a8;
        margin-right: 0.5rem;
    }

    /* ── History item ── */
    .history-item {
        background: #1a1f2e;
        border: 1px solid #2a2f3e;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: border-color 0.15s;
    }
    .history-item:hover { border-color: #7c9fff; }
    .history-item .filename {
        font-size: 0.85rem;
        font-weight: 600;
        color: #d4d8e8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .history-item .timestamp {
        font-size: 0.72rem;
        color: #5c6378;
        margin-top: 0.2rem;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 2rem 1rem 1rem;
        color: #5c6378;
        font-size: 0.78rem;
    }
    .footer span {
        color: #7c9fff;
        font-weight: 500;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

UPLOAD_DIR = "uploads"

def _ensure_dirs() -> None:
    """Ensure uploads/ and outputs/ directories exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs("outputs", exist_ok=True)


def _save_uploaded_file(uploaded_file) -> str:
    """Save the Streamlit UploadedFile to uploads/ and return its path."""
    _ensure_dirs()
    dest = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest


def _word_count(text: str) -> int:
    return len(text.split())


def _format_timestamp(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 1rem 0 0.5rem;">
            <div style="font-size:1.3rem;font-weight:700;color:#e8eaf0;">🎙️ Meeting Summarizer</div>
            <div style="font-size:0.78rem;color:#5c6378;margin-top:0.2rem;">AI-Powered Meeting Intelligence</div>
        </div>
        <hr style="border:none;border-top:1px solid #2a2f3e;margin:0.75rem 0 1.25rem;">
        """,
        unsafe_allow_html=True,
    )

    # ── About ──
    with st.expander("ℹ️ About", expanded=False):
        st.markdown(
            """
            Upload a meeting recording and get:
            - ✅ Full transcript
            - ✅ Executive summary
            - ✅ Actionable items
            - ✅ Downloadable JSON report

            Long meetings are handled via **hierarchical summarization** —
            the transcript is split into sections, each summarized individually,
            then merged into one final output.
            """,
        )

    # ── Tech stack ──
    with st.expander("⚙️ Tech Stack", expanded=False):
        st.markdown(
            """
            | Layer | Tool |
            |---|---|
            | Frontend | Streamlit |
            | Transcription | OpenAI Whisper |
            | Summarization | Google Gemini 2.5 Flash |
            | Storage | Local JSON |
            | Language | Python 3.11+ |
            """
        )

    st.markdown(
        "<hr style='border:none;border-top:1px solid #2a2f3e;margin:1rem 0;'>",
        unsafe_allow_html=True,
    )

    # ── History ──
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#5c6378;margin-bottom:0.75rem;'>📂 Past Summaries</div>",
        unsafe_allow_html=True,
    )
    history = load_all_outputs()
    if not history:
        st.markdown(
            "<div style='font-size:0.82rem;color:#5c6378;'>No summaries yet. Upload a recording to get started.</div>",
            unsafe_allow_html=True,
        )
    else:
        for item in history[:10]:  # show latest 10
            label = item.get("filename", item.get("_output_file", "Unknown"))
            ts = _format_timestamp(item.get("created_at", ""))
            st.markdown(
                f"""
                <div class="history-item">
                    <div class="filename">🎵 {label}</div>
                    <div class="timestamp">🕐 {ts}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── Main content ───────────────────────────────────────────────────────────────

# Hero header
st.markdown(
    """
    <div class="hero-header">
        <h1>🎙️ Meeting Summarizer</h1>
        <p>Upload a meeting recording · Get a transcript, summary & action items in seconds</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Upload section ──
col_upload, col_gap = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        label="Upload Meeting Recording",
        type=["mp3", "wav", "m4a"],
        help="Supported formats: MP3, WAV, M4A. Max size: 25 MB (Whisper API limit).",
        label_visibility="visible",
    )

if uploaded_file is not None:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.markdown(
        f"""
        <div style="display:flex;gap:0.5rem;align-items:center;margin:0.5rem 0 1.25rem;">
            <span class="stat-badge">📁 {uploaded_file.name}</span>
            <span class="stat-badge">💾 {file_size_mb:.1f} MB</span>
            <span class="stat-badge">🎵 {uploaded_file.type}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Generate button ──
    generate_clicked = st.button(
        "🚀 Generate Summary",
        type="primary",
        use_container_width=True,
    )

    if generate_clicked:
        # ── Pipeline execution ──
        result_data = {}
        error_occurred = False

        try:
            # Step 1: Save audio
            with st.spinner("💾 Saving audio file..."):
                audio_path = _save_uploaded_file(uploaded_file)

            # Step 2: Transcribe
            with st.spinner("🎙️ Transcribing audio with Whisper..."):
                transcript = transcribe_audio(audio_path)

            if not transcript.strip():
                st.error("⚠️ Whisper returned an empty transcript. The audio may be silent or too short.")
                error_occurred = True
            else:
                # Step 3: Summarize
                word_count = _word_count(transcript)
                mode = "hierarchical" if word_count > 2500 else "direct"

                spinner_msg = (
                    f"🧩 Chunking transcript ({word_count:,} words) and summarizing with Gemini..."
                    if mode == "hierarchical"
                    else f"🤖 Summarizing transcript ({word_count:,} words) with Gemini..."
                )

                with st.spinner(spinner_msg):
                    summary_result = summarize(transcript)

                summary_text = summary_result.get("summary", "")
                action_items = summary_result.get("action_items", [])

                # Step 4: Save JSON
                with st.spinner("💾 Saving results..."):
                    output_path = save_output(
                        filename=uploaded_file.name,
                        transcript=transcript,
                        summary=summary_text,
                        action_items=action_items,
                    )

                # Prepare download data
                result_data = {
                    "filename": uploaded_file.name,
                    "created_at": datetime.now().isoformat(),
                    "transcript": transcript,
                    "summary": summary_text,
                    "action_items": action_items,
                }

        except FileNotFoundError as e:
            st.error(f"❌ File error: {e}")
            error_occurred = True
        except ValueError as e:
            st.error(f"❌ Configuration error: {e}")
            error_occurred = True
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            error_occurred = True

        # ── Results display ──
        if not error_occurred and result_data:
            st.markdown(
                "<hr class='section-divider'>",
                unsafe_allow_html=True,
            )

            # Success banner
            col_s1, col_s2, col_s3 = st.columns(3)
            word_count = _word_count(result_data["transcript"])
            with col_s1:
                st.metric("📝 Words Transcribed", f"{word_count:,}")
            with col_s2:
                st.metric("🎯 Action Items", len(result_data["action_items"]))
            with col_s3:
                st.metric("💾 Saved to", "outputs/")

            st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

            # Two-column results layout
            col_left, col_right = st.columns([1, 1], gap="large")

            # ── Left: Transcript ──
            with col_left:
                st.markdown(
                    "<div class='card-title'>📄 Full Transcript</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='transcript-box'>{result_data['transcript']}</div>",
                    unsafe_allow_html=True,
                )

            # ── Right: Summary + Action Items ──
            with col_right:
                # Summary card
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="card-title">📋 Meeting Summary</div>
                        <div class="summary-text">{result_data['summary']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Action items
                st.markdown(
                    "<div class='card-title' style='margin-top:1rem;'>✅ Action Items</div>",
                    unsafe_allow_html=True,
                )
                if result_data["action_items"]:
                    for item in result_data["action_items"]:
                        st.markdown(
                            f"""
                            <div class="action-item">
                                <span class="action-icon">▸</span>
                                <span>{item}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        "<div style='color:#5c6378;font-size:0.85rem;'>No action items detected.</div>",
                        unsafe_allow_html=True,
                    )

            # ── Download ──
            st.markdown(
                "<hr class='section-divider'>",
                unsafe_allow_html=True,
            )
            json_str = json.dumps(result_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="⬇️ Download JSON Report",
                data=json_str.encode("utf-8"),
                file_name=f"meeting_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

else:
    # ── Empty state placeholder ──
    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;color:#3a3f52;">
            <div style="font-size:3.5rem;margin-bottom:1rem;">🎤</div>
            <div style="font-size:1.1rem;font-weight:500;color:#4a5168;">Upload a meeting recording to get started</div>
            <div style="font-size:0.85rem;color:#3a3f52;margin-top:0.5rem;">MP3 · WAV · M4A supported</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer ──
st.markdown(
    """
    <div class="footer">
        Built with <span>Streamlit</span> · <span>OpenAI Whisper</span> · <span>Google Gemini 2.5 Flash</span>
    </div>
    """,
    unsafe_allow_html=True,
)
