# Project Status – Music Adventures (MusicTheoryTutor)

Last updated: today

---

## Phase summary

- ✅ Phase 1 – Core AI Modules (Completed)
  - Hybrid parser (regex first, GPT fallback)
  - Notation generation: Abjad → LilyPond (PNG, MIDI)
  - Modular engine (`main.py`) with error handling and basic caching

- 🚧 Phase 2 – Advanced Interactive Features (Current)
  - Implemented
    - Audio integration (MIDI → WAV) for many question types
    - Enhanced MCQ types: rhythm, harmony, ear training, musical form
    - UI/UX: two main blue cards on Home; larger controls; dropdown theming
    - Answer distribution balancing (correct letter not always A)
    - Session history + de-dup to reduce repeats, including ear‑training correct‑text de‑dup
  - Pending (in this phase)
    - SQLite logging of attempts and analytics
    - Elo‑based difficulty selection
    - Minor polish on ear‑training variety


- 🎼 Phase 3 – Interactive Practice (Planned)
  - 8‑song MusicXML pack in SQLite + cached MIDI/PDF
  - Mic capture (webRTC) + pitch/rhythm analysis; performance scoring

---

## What works today
- Streamlit app with MCQ generation and feedback
- Real notation & audio rendering
- Basic ear‑training support (intervals, some chords/scales) with variety guards
- UI consistent with interview requirements (blue theme; larger controls)

## Known issues / gaps
- Ear‑training can still repeat families if the generator clusters—SQLite+Elo selection will mitigate
- Audio synthesis quality is lightweight; future improvement: FluidSynth for higher fidelity
- LilyPond path must be present; missing installs produce a friendly error

---

## Phase 2 extensions: Elo + SQLite (design, ready to implement)

### Minimal schema
```
learners(id, handle, rating, rd, created_at)
topics(id, name)
learner_topic_ratings(learner_id, topic_id, rating, rd)
items(id, topic_id, grade, rating, rd, active, meta_json)
attempts(id, learner_id, item_id, correct, response_ms, started_at)
```

### Selection policy
- 70%: nearest in rating within ±60 Elo (per topic if available)
- 20%: explore slightly harder (~ +100)
- 10%: review slightly easier (~ −100)
- Rotate/bias towards weak topics (lowest per‑topic rating)

### Elo update
- Guess‑corrected score for 4‑choice MCQ: `S_adj = (S − 0.25) / 0.75`
- Player K scales with RD and (optionally) response time
- Item K ≈ one‑third of player K
- Update both global and per‑topic ratings

### Elo ↔ AMEB mapping (initial)
- 900–1050 → Grade 1
- 1050–1150 → Grade 2
- 1150–1250 → Grade 3
- 1250–1350 → Grade 4
- 1350–1450 → Grade 5
- 1450–1550 → Grade 6

Use anchor items per grade to stabilize the scale.

---

## Phase 3 blueprint (interactive practice)
- Store 8 MusicXML melodies in SQLite; export PDF/MIDI with music21/MuseScore
- Record via `streamlit-webrtc`; save WAV to DB
- Compare user audio to score MIDI with librosa (pyin + simple DTW)
- Metrics: pitch accuracy, rhythm accuracy, overall score; store diagnostics

---

## Next steps (suggested)
1) Add SQLite models and attempt logging
2) Implement Elo selector + updates (global + per topic)
3) Add a tiny “Practice” page stub for the 8‑song pack (list → view → record → score)
4) Incrementally improve ear‑training synthesis and content diversity
