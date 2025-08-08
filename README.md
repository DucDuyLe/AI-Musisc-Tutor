# Music Adventures (MusicTheoryTutor)

A Streamlit-based prototype that generates AMEB-aware music-theory MCQs, renders real musical notation and audio, gives lightweight feedback, and lays the groundwork for adaptive difficulty (Elo) and interactive play-and-score practice.

This repo reflects a time-boxed interview build. Phase 1 is complete, Phase 2 is in progress (see Project Status for details).

---

## Quick start

### 1) Requirements
- Python 3.10+
- Windows (tested); macOS/Linux should work with minor path tweaks
- LilyPond 2.24.x installed (for PNG/MIDI rendering)
- An OpenAI API key

### 2) Install
```bash
pip install -r requirements.txt
```

### 3) Configure
Provide your OpenAI key via either option:
- .env at repo root:
  ```env
  OPENAI_API_KEY=YOUR_OPENAI_API_KEY
  ```
- or Streamlit secrets (preferred in prod):
  `.streamlit/secrets.toml`
  ```toml
  OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
  ```

LilyPond: the app auto-detects common Windows install paths; if LilyPond lives elsewhere, update the fallback path in `tools/audio_renderer.py` (method `_find_lilypond`).

### 4) Run the app
```bash
streamlit run app.py
```
Open the browser tab that Streamlit launches.

Demo video: see `Demo.mp4` at the repo root for a 3–5 minute walkthrough of the main features (Home → MCQ → Ear Training → rotation → reset).

### Optional API (programmatic access)
- Start the API:
  ```bash
  python -m uvicorn api:app --reload
  ```
- Make a request (PowerShell):
  ```powershell
  Invoke-RestMethod -Uri 'http://127.0.0.1:8000/generate' -Method Post -ContentType 'application/json' -Body '{"instrument":"Piano","grade":3}' | ConvertTo-Json -Depth 6
  ```
- Response shape:
  ```json
  {
    "notation_image_base64": "...",
    "audio_url": "/media/audio/<id>.wav",
    "explanation": "...",
    "question": "...",
    "options": {"A":"...","B":"...","C":"...","D":"..."},
    "correct": "B"
  }
  ```
- Notes:
  - Exercise type is rotated internally (Comprehensive Theory behavior).
  - Open the audio via the returned `audio_url`.
  - Swagger UI: `http://127.0.0.1:8000/docs`.

---

## What you can do today
- Pick Instrument, Grade, and Exercise Type (e.g., Intervals, Chords, Scales, Ear Training, Harmony, Musical Form, or "Comprehensive Theory" which rotates types).
- Generate AMEB-aware MCQs with:
  - Rendered musical notation (Abjad → LilyPond → PNG)
  - Auto-synthesized audio for many items (LilyPond → MIDI → WAV)
  - Short, encouraging feedback
- Balanced multiple-choice answers (correct letter distribution across A/B/C/D).
- Reduced repetition: the app keeps recent question history and avoids generating the exact same question or the same ear-training answer text back-to-back.
- Clean UI with large controls and two summary cards on Home ("How to start" and "AI agents in this app").

---

## Architecture (high-level)
- `app.py` – Streamlit UI, navigation, session state, and MCQ flow
- `main.py` – Orchestrates the pipeline for notation/audio
- `agents/`
  - `question_generator.py` – AMEB-aware MCQ generation (OpenAI)
  - `question_parser.py` – Regex-first parser with GPT fallback for tricky cases
  - `notation_generator.py` – Creates Abjad code and renders via LilyPond
- `tools/`
  - `abjad_builder.py` – Builds staff objects (scales, chords, intervals, etc.)
  - `image_renderer.py` – PNG export (via LilyPond)
  - `audio_renderer.py` – MIDI → WAV synthesis (instrument-aware)
  - `theory_lookup.py` – Light theory utilities (scales, chords, intervals)
- `curriculum_database.json` – AMEB-aligned data used to guide content

OpenAI usage is centralized and expects a key in env or Streamlit secrets. Hardcoded keys were removed.

---

## Notation & audio pipeline
1) A question is generated (topic/grade aware).
2) It is parsed to structured intent (regex first, GPT fallback when needed).
3) Abjad builds a staff; LilyPond renders to PNG and MIDI.
4) MIDI is converted to WAV for in-browser audio playback (with a synthesized, instrument-flavoured tone model).

If LilyPond isn’t found, rendering will fail gracefully with an error message.

---

## Configuration & environment
- Set `OPENAI_API_KEY` (env or Streamlit secrets).
- LilyPond path: `_find_lilypond()` in `tools/audio_renderer.py` contains common Windows paths and PATH probing.
- Optional Streamlit theming can be added in `.streamlit/config.toml`.

---

## Roadmap (phases)

### ✅ Phase 1 – Core AI Modules (Completed)
- Hybrid parser (regex first, GPT fallback)
- Notation generation with Abjad/LilyPond
- Modular engine + error handling

### 🚧 Phase 2 – Advanced Interactive Features (Current)
- Audio integration (MIDI → WAV) for many question types
- Enhanced MCQ types: rhythm, harmony, ear training, musical form
- UI/UX refinements; larger controls; two home cards (blue theme)
- Session history & de-dup (avoid repeating same questions/answers)
- Planned in Phase 2 but not yet implemented:
  - SQLite data model for attempts and analytics
  - Elo-based adaptive difficulty (player/item ratings)

### 🚀 Phase 3 – Advanced AI (Future)
- Adaptive Difficulty System (Elo)
- Advanced question generation (modulation, counterpoint, jazz harmony)
- AI performance analysis (audio comparison, real-time feedback)

### 🎼 Phase 4 – Interactive Practice (Future)
- 8-song MusicXML pack stored in SQLite
- PDF/MIDI export per song
- In-browser mic capture; pitch/rhythm analysis; score & diagnostics

See Project Status for a more detailed breakdown.

---

## Elo + SQLite plan (design notes)
A compact, production-ready schema to track a single learner (or session-based pseudo-user), per-topic ratings, item ratings, and attempts. Selection picks items near the learner’s rating, with a small explore/review ratio. Elo updates are guess-corrected for 4-option MCQs and can be speed-aware. Suggested initial grade ↔ Elo mapping and safe exploration bands are included in `PROJECT_STATUS_MusicTheoryTutor.md`.

---

## Known limitations
- Ear-training variety is improved but not perfect yet; some families can still cluster without the future Elo/SQLite selector.
- Audio synthesis is a lightweight, CPU-only model; quality varies across instruments.
- LilyPond install path needs to be correct for rendering to succeed.

---

## Development scripts (optional ideas)
- Song pack bootstrap (Phase 4): ingest 8 MusicXML files → SQLite → export cached MIDI/PDF.
- Elo service stub (Phase 2/3): select item, log attempt, update ratings, return next recommendation.

---

## Credits
- Abjad, LilyPond, music21
- librosa, NumPy, SciPy
- Streamlit

This prototype is provided for interview/demo purposes.
