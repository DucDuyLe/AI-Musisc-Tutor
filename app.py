import streamlit as st
import os
from dotenv import load_dotenv
import json
import base64
from io import BytesIO
import inspect
import time
from agents.question_generator import generate_curriculum_aware_question, get_available_topics
from agents.notation_generator import generate_notation_from_question
from main import MusicTheoryEngine
import re

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Smart Music-Theory Tutor",
    page_icon="🎵",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Import modern, readable font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    [data-testid="stAppViewContainer"]{background:#ffffff !important;}
    [data-testid="stHeader"]{background-color: rgba(255,255,255,0) !important;}
    [data-testid="stSidebar"]{background:#f7fbff !important;}
    /* Text color to black */
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 { color:#000000; font-family:'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    [data-testid="stSidebar"] * { color:#000000; }
    /* Default button theme (bluey) */
    .stButton > button { background:#e9f6ff !important; color:#000000 !important; border:1px solid #cde8ff !important; border-radius:10px !important; }
    .stButton > button:hover { background:#dff0ff !important; }
    /* Preserve primary pink start button */
    .start-btn button {background:#ffd7e5 !important; color:#000000 !important; border:1px solid #f5b8cd !important;}
    .start-btn button:hover {background:#fecadd !important;}
    /* Feedback area button blue to match tips box */
    .feedback-area button {background:#e9f6ff !important; color:#000000 !important; border:1px solid #cde8ff !important;}
    .feedback-area button:hover {background:#dff0ff !important;}
    /* Select/Dropdown pastel styling (input appearance) */
    div[data-baseweb="select"] > div{background:#ffe6f0 !important; border-radius:14px !important; border:1px solid #dbe7ff !important; color:#000 !important;}
    div[data-baseweb="select"] > div:hover{box-shadow:0 0 0 2px rgba(98,160,234,0.25) inset !important;}
    /* Force dropdown panel to light pink, with white hover and light-pink selected */
    :root{--dd-pink:#ffe6f0; --dd-hover:#ffffff; --dd-selected:#fecadd;}
    /* Popover panel and listbox (BaseWeb renders in a portal) */
    body div[data-baseweb="popover"] [data-baseweb="menu"],
    body div[data-baseweb="popover"] [role="listbox"],
    body [role="listbox"],
    body [data-baseweb="menu"]{
        background: var(--dd-pink) !important;
        background-color: var(--dd-pink) !important;
        color:#000 !important; border:1px solid #f5b8cd !important;
    }
    /* Also target ul-based listboxes (some builds) and portal root */
    ul[role="listbox"],
    body > div[aria-hidden="true"] ul[role="listbox"]{
        background-color: var(--dd-pink) !important; color:#000 !important; border:1px solid #f5b8cd !important;
    }
    /* Ensure children keep parent background */
    body div[data-baseweb="popover"] [data-baseweb="menu"] *,
    body div[data-baseweb="popover"] [role="listbox"] *{background-color: transparent !important;}
    /* Options */
    body [role="option"], body li[role="option"], ul[role="listbox"] li{color:#000 !important; background-color: var(--dd-pink) !important;}
    body [role="option"]:hover, body li[role="option"]:hover, ul[role="listbox"] li:hover{background: var(--dd-hover) !important;}
    body [role="option"][aria-selected="true"], body [aria-selected="true"]{background: var(--dd-selected) !important;}
    /* Bigger option text */
    body div[data-baseweb="menu"] [role="option"], body div[data-baseweb="menu"] li {font-size: 1.4em !important;}
    /* Question title */
    .question-title{font-size:24px; font-weight:700; margin:6px 0 10px 0;}
    /* Answer result boxes */
    .ansbox{padding:10px 12px; border-radius:10px; background:#e9f6ff; border:1px solid #cde8ff; margin:8px 0; display:inline-block;}
    .ans-correct{background:#eafbe9 !important; border-color:#b8e6b2 !important;}
    .ans-wrong{background:#ffe8e8 !important; border-color:#f2bbbb !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Load environment variables
load_dotenv()

# ---------------- Session State ----------------
if 'route' not in st.session_state:
    st.session_state.route = 'home'  # 'home' | 'mcq' | 'practical'
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = None
if 'show_feedback' not in st.session_state:
    st.session_state.show_feedback = False
if 'current_feedback' not in st.session_state:
    st.session_state.current_feedback = None
if 'notation_data' not in st.session_state:
    st.session_state.notation_data = None
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = None
if 'question_history' not in st.session_state:
    st.session_state.question_history = []
if 'correct_letter_counts' not in st.session_state:
    st.session_state.correct_letter_counts = {"A":0, "B":0, "C":0, "D":0}
if 'fresh_session' not in st.session_state:
    st.session_state.fresh_session = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
# Store selections from Home
if 'instrument' not in st.session_state:
    st.session_state.instrument = 'Piano'
if 'grade_num' not in st.session_state:
    st.session_state.grade_num = 1
if 'exercise_type' not in st.session_state:
    st.session_state.exercise_type = 'Comprehensive Theory'
# Simple UI change log
if 'ui_change_log' not in st.session_state:
    st.session_state.ui_change_log = []

# ---------------- Utilities ----------------

def log_change(msg: str):
    try:
        st.session_state.ui_change_log.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")
    except Exception:
        pass

def get_openai_client():
    """Get/cached OpenAI client. Tries env first; st.secrets if available. Never throws StreamlitSecretNotFoundError upstream."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Access st.secrets safely (may not exist)
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")  # type: ignore[attr-defined]
        except Exception:
            api_key = None
    if not api_key:
        raise Exception("OpenAI API key not found. Set OPENAI_API_KEY in environment or Streamlit secrets.")
    if "openai_client" not in st.session_state:
        st.session_state.openai_client = OpenAI(api_key=api_key)
    return st.session_state.openai_client

# ---------------- Agents ----------------

def notation_generator_agent(question_data, instrument="Piano", use_small_images=True, exercise_type=None):
    """Generate musical notation using the modular system with instrument-specific audio"""
    question_text = question_data.get('question', '')
    if not question_text:
        return None
    try:
        engine = MusicTheoryEngine()
        result = engine.generate_notation(
            question_text,
            instrument=instrument,
            exercise_type=exercise_type,
            question_data=question_data
        )
        if result and result.get('success'):
            image_result = result.get('image', {})
            audio_result = result.get('audio', {})
            if image_result and image_result.get('success'):
                return {
                    'question_image': image_result['image_path'],
                    'answer_image': image_result['image_path'],
                    'lilypond_code': result.get('lilypond_code', ''),
                    'parsed_data': result.get('parsed_data'),
                    'musical_data': result.get('musical_data'),
                    'validation': result.get('validation'),
                    'audio_data': audio_result,
                    'instrument': instrument
                }
            else:
                st.error(f"Failed to generate image: {image_result.get('error', 'Unknown error') if image_result else 'No image result'}")
                return None
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            st.error(f"Failed to generate notation: {error_msg}")
            return None
    except Exception as e:
        st.error(f"Failed to generate notation: {e}")
        return None

def feedback_generator_agent(question_data, user_answer):
    # Try LLM; fall back to static text if no key
    try:
        client = get_openai_client()
    except Exception:
        is_correct = user_answer == question_data.get('correct_answer', '')
        if is_correct:
            return "✅ Correct! Great job."
        return f"❌ Not quite right. The correct answer is {question_data.get('correct_answer','')}."
    is_correct = user_answer == question_data.get('correct_answer', '')
    prompt = f"""
    Provide a brief, encouraging feedback for this music theory MCQ.

    Question: {question_data.get('question', '')}
    User's Answer: {user_answer}
    Correct Answer: {question_data.get('correct_answer', '')}
    Is Correct: {is_correct}

    Requirements (keep it concise):
    - If correct: Congratulate in 1 short sentence.
    - If incorrect: In 1-2 short sentences, say it's not correct, state the correct answer, and briefly explain WHY that answer is correct (music theory reason) or why the chosen answer is wrong.

    Keep it brief and positive.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=50
    )
    return response.choices[0].message.content

def _choose_balanced_correct_letter():
    counts = st.session_state.correct_letter_counts
    # Pick the letter with the lowest count to approach 25% distribution
    return sorted(counts, key=lambda k: counts[k])[0]

def _maybe_rebalance_letters(every: int = 40):
    total = sum(st.session_state.correct_letter_counts.values())
    if total and total % every == 0:
        avg = total / 4.0
        for k in st.session_state.correct_letter_counts:
            st.session_state.correct_letter_counts[k] = int(avg * 0.4)

def _extract_time_signatures(text: str) -> list[str]:
    if not text:
        return []
    try:
        return re.findall(r"\b(\d+\s*/\s*\d+)\b", text)
    except Exception:
        return []

def _extract_tags(qtext: str, exercise_type: str, options: dict | None = None) -> dict:
    tags = {"time_signatures": [], "intervals": [], "keys": [], "scales": [], "chords": []}
    if not qtext:
        return tags
    try:
        # rhythm time signatures
        tags["time_signatures"] = [ts.replace(" ", "") for ts in re.findall(r"\b(\d+\s*/\s*\d+)\b", qtext)]
        # intervals
        tags["intervals"] = [m.lower() for m in re.findall(r"\b(major|minor|perfect)\s+(?:unison|2nd|3rd|4th|5th|6th|7th|octave)\b", qtext, flags=re.I)]
        # keys/tonics with mode
        keys = re.findall(r"\b([A-G][#b]?)\s*(major|minor|harmonic minor|melodic minor)?\b", qtext, flags=re.I)
        tags["keys"] = [" ".join(k).strip().lower() for k in keys if k[0]]
        # scales
        tags["scales"] = [m.lower() for m in re.findall(r"(harmonic minor|melodic minor|major scale|minor scale)", qtext, flags=re.I)]
        # chords (roman numerals, optional 7)
        tags["chords"] = [c.upper() for c in re.findall(r"\b([ivIV]{1,3}7?)\b", qtext)]
    except Exception:
        pass
    return tags

def _append_history(entry: dict, cap: int = 200):
    st.session_state.question_history.append(entry)
    if len(st.session_state.question_history) > cap:
        del st.session_state.question_history[: len(st.session_state.question_history) - cap]

def _recent_topic_streak(target_topic: str, history: list[dict]) -> int:
    if not target_topic or not history:
        return 0
    target = str(target_topic).strip().lower()
    streak = 0
    for h in reversed(history):
        t = str(h.get('topic', '')).strip().lower()
        if t == target:
            streak += 1
        else:
            break
    return streak

def generate_question(instrument, grade, exercise_type=None):
    try:
        # Use history except for the very first question in a fresh session
        use_history = not st.session_state.get('fresh_session', False)
        history: list[dict] = st.session_state.get('question_history', []) if use_history else []

        # Prepare kwargs based on generator signature
        params = set(inspect.signature(generate_curriculum_aware_question).parameters.keys())
        kwargs = {}
        if 'history' in params and use_history:
            # Pass only the recent question texts/topics to guide the model away from repeats
            recent_hist = history[-8:]
            recent_for_prompt = [
                {
                    'question': h.get('question', ''),
                    'topic': h.get('topic', ''),
                    'exercise_type': h.get('exercise_type', '')
                }
                for h in recent_hist if isinstance(h, dict)
            ]
            kwargs['history'] = recent_for_prompt

        # Build recent sets for local de-duplication checks
        recent = history[-8:]
        recent_questions = {str(h.get('question', '')).strip() for h in recent}
        recent_topics = {str(h.get('topic', '')).strip().lower() for h in recent}
        recent_ts = {t.replace(' ', '') for h in recent for t in (h.get('tags', {}).get('time_signatures', []) if isinstance(h, dict) else [])}
        recent_keys = {k for h in recent for k in (h.get('tags', {}).get('keys', []) if isinstance(h, dict) else [])}
        recent_intervals = {(iv.lower() if isinstance(iv, str) else iv) for h in recent for iv in (h.get('tags', {}).get('intervals', []) if isinstance(h, dict) else [])}
        recent_correct_texts = {str(h.get('correct_text','')).strip().lower() for h in recent}

        # Track topic streak to avoid too many in a row
        last_topic = str(history[-1]['topic']).strip().lower() if history and history[-1].get('topic') else ''
        last_topic_streak = _recent_topic_streak(last_topic, history) if last_topic else 0
        max_topic_streak = 4

        # Try a few times to avoid near-duplicate questions/topics
        max_attempts = 5
        last_result = None
        for _ in range(max_attempts):
            result = generate_curriculum_aware_question(instrument, grade, exercise_type, **kwargs) if kwargs else generate_curriculum_aware_question(instrument, grade, exercise_type)
            last_result = result
            if not isinstance(result, dict):
                continue
            qtext = str(result.get('question', '')).strip()
            topic = str(result.get('topic', '')).strip().lower()

            # Hard guards against repeating exact question or very recent topic
            if qtext and qtext in recent_questions:
                continue
            if topic and topic in recent_topics:
                # If the same topic has been used too many times consecutively, skip
                if topic == last_topic and last_topic_streak >= max_topic_streak:
                    continue

            # Tag-based de-dup for common exercise types
            new_tags = _extract_tags(qtext, exercise_type, result.get('options'))
            if exercise_type == 'Rhythm':
                ts_new = {t.replace(' ', '') for t in new_tags.get('time_signatures', [])}
                if ts_new & recent_ts:
                    continue
            if exercise_type in ('Scales', 'Harmony'):
                if set(new_tags.get('keys', [])) & recent_keys:
                    continue
            if exercise_type == 'Intervals':
                iv_new = {(iv.lower() if isinstance(iv, str) else iv) for iv in new_tags.get('intervals', [])}
                if iv_new & recent_intervals:
                    continue
            if exercise_type == 'Ear Training':
                # Ensure the correct answer text differs from recent to avoid same-sounding items
                opts = result.get('options', {}) or {}
                ca = str(result.get('correct_answer','')).strip()
                corr_text = str(opts.get(ca, '')).strip().lower()
                if corr_text and corr_text in recent_correct_texts:
                    continue

            return result

        return last_result
    except Exception as e:
        st.error(f"Error generating question: {e}")
        return None

# ---------------- Actions ----------------

def start_new_mcq_question():
    """Start a fresh MCQ session (optionally wiping history so the agent sees no context)."""
    return _start_or_next_mcq(reset_session=True)

def _start_or_next_mcq(reset_session: bool = False):
    st.session_state.route = 'mcq'

    if reset_session:
        # wipe all context so agent starts clean
        st.session_state.question_history = []
        st.session_state.correct_letter_counts = {"A":0, "B":0, "C":0, "D":0}
        st.session_state.session_id = f"s_{int(time.time())}"
        st.session_state.fresh_session = True

    # reset UI bits
    st.session_state.notation_data = None
    st.session_state.user_answer = None
    st.session_state.show_feedback = False
    st.session_state.current_feedback = None
    st.session_state.audio_cache = None
    st.session_state.question_id = f"q_{int(time.time())}"

    # If comprehensive, rotate here (existing logic)
    chosen_exercise = st.session_state.exercise_type
    if chosen_exercise == "Comprehensive Theory":
        import random
        allowed = ["Intervals", "Chords", "Scales", "Rhythm", "Harmony", "Ear Training", "Musical Form"]
        if isinstance(st.session_state.grade_num, int) and st.session_state.grade_num <= 4:
            allowed.append("Note Reading")
        chosen_exercise = random.choice(allowed)
        st.session_state.exercise_type = chosen_exercise

    # Generate first/next question
    st.session_state.current_question = generate_question(
        st.session_state.instrument,
        st.session_state.grade_num,
        st.session_state.exercise_type,
    )

    # After generation, flip off the fresh flag if it was a fresh session
    st.session_state.fresh_session = False

    # Update trackers + render notation/audio
    if st.session_state.current_question:
        try:
            qtext = st.session_state.current_question.get('question','')
            correct_letter = str(st.session_state.current_question.get('correct_answer','')).strip()
            if correct_letter in st.session_state.correct_letter_counts:
                st.session_state.correct_letter_counts[correct_letter] += 1
            tags = _extract_tags(qtext, st.session_state.exercise_type, st.session_state.current_question.get('options'))
            _append_history({
                'question': qtext,
                'correct_answer': correct_letter,
                'topic': st.session_state.current_question.get('topic'),
                'exercise_type': st.session_state.exercise_type,
                'tags': tags,
                'session_id': st.session_state.session_id
            })
            _maybe_rebalance_letters()
        except Exception:
            pass
        st.session_state.notation_data = notation_generator_agent(
            st.session_state.current_question,
            st.session_state.instrument,
            True,
            st.session_state.exercise_type,
        )

# ---------------- Rendering: MCQ Question/Feedback ----------------

def display_question(question_data):
    if not question_data:
        return
    # Large question text instead of 'Your Question'
    st.markdown(f"<div class='question-title'>{question_data['question']}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📚 Topic: {question_data.get('topic', 'Music Theory')}")
    with col2:
        st.info(f"📊 Difficulty: {question_data.get('difficulty', 'Medium')}")

    st.markdown("**Musical Notation:**")
    current_ex_type = st.session_state.get('exercise_type')
    if current_ex_type == 'Ear Training' and not st.session_state.user_answer:
        st.info("Notation is hidden for ear training. Listen first and answer; notation will be revealed after.")
    elif st.session_state.notation_data and st.session_state.notation_data.get('question_image'):
        notation_path = st.session_state.notation_data['question_image']
        if notation_path.endswith('.png'):
            st.image(notation_path, caption="Musical Notation", use_container_width=True)
        else:
            st.image(notation_path, caption="Question Notation", use_container_width=True)
    else:
        if current_ex_type != 'Ear Training':
            st.info("No notation available for this question.")

    st.markdown("**Audio:**")
    if st.session_state.notation_data and st.session_state.notation_data.get('audio_data'):
        audio_data = st.session_state.notation_data['audio_data']
        if audio_data.get('success') and audio_data.get('audio_base64'):
            import hashlib, base64 as _b64
            audio_base64 = audio_data.get('audio_base64', '')
            audio_bytes = _b64.b64decode(audio_base64)
            with st.container():
                st.audio(audio_bytes, format="audio/wav")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tempo", f"{audio_data.get('tempo', 120)} BPM")
            with col2:
                st.metric("Duration", f"{audio_data.get('duration', 0):.1f}s")
        else:
            st.warning("Audio generation failed")
    else:
        st.info("🎵 Audio feature coming soon!")

    st.markdown("**Select your answer:**")
    # Render answers with immediate visual feedback once answered
    selected = st.session_state.user_answer
    correct_letter = question_data.get('correct_answer')
    def render_option(letter: str, text: str, key: str):
        is_selected = selected == letter
        is_correct = correct_letter == letter
        # When answered: show colored badge, else show button
        if selected:
            css_class = 'ansbox ' + ('ans-correct' if is_correct else ('ans-wrong' if is_selected else ''))
            st.markdown(f"<span class='{css_class}'>{letter}) {text}</span>", unsafe_allow_html=True)
        else:
            if st.button(f"{letter}) {text}", key=key):
                st.session_state.user_answer = letter
                st.session_state.show_feedback = True
                st.session_state.current_feedback = feedback_generator_agent(question_data, letter)
                st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        render_option('A', question_data['options']['A'], 'option_a')
        render_option('B', question_data['options']['B'], 'option_b')
    with col2:
        render_option('C', question_data['options']['C'], 'option_c')
        render_option('D', question_data['options']['D'], 'option_d')

def display_feedback(question_data):
    if not st.session_state.show_feedback or not question_data or not st.session_state.current_feedback:
        return
    st.markdown("---")
    st.subheader("📝 Feedback")
    user_answer = st.session_state.user_answer
    correct_answer = question_data['correct_answer']

    # Result box: green if correct, red if incorrect
    if user_answer == correct_answer:
        st.success("✅ Correct! Well done! You correctly identified the musical concept!")
    else:
        st.error(f"❌ Not quite right. The correct answer is {correct_answer}.")

    # Box 2: Blue — tips
    st.info("Try to visualize the notes on the staff and practice reading music regularly.\n\nContinue with similar questions to strengthen your understanding.")

# ---------------- Pages ----------------

def render_home():
    st.markdown("""
    <style>
    /* Page background & typography */
    .home-container {padding-top: 10px;}
    .hero-title {font-size: 78px; font-weight: 800; letter-spacing: 1px; text-align: center; margin-top: 10px;}
    .hero-sub {text-align: center; color: #4c566a; font-size: 27px; margin-top: 6px;}
    /* Elastic equal-height cards using flexbox */
    .cards {display:flex; flex-wrap: wrap; gap: 34px; margin: 40px 0 24px 0; align-items: stretch;}
    .card {border-radius: 24px; padding: 42px 44px; min-height: 360px; height:auto; display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-start; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border:1px solid rgba(0,0,0,0.03); overflow:hidden; flex:1 1 0;}
    .card.center {min-height: 360px;}
    .card.pink {background: #fdeef3;}
    .card.blue {background: #e9f6ff;}
    .card h4 {margin: 0 0 14px 0; font-size: 36px; font-weight: 800; text-align:center; width: 100%;}
    .card p {margin: 0; font-size: 24px; line-height: 1.6;}
    .card ul {margin: 12px 0 0 24px; padding: 0;}
    .card li {margin: 8px 0; font-size: 24px;}
    .card:hover {transform: translateY(-3px); transition: all .2s ease-in-out; box-shadow: 0 12px 30px rgba(0,0,0,0.09)}
    .start-btn {text-align:center; margin-top: 12px; display:flex; justify-content:center;}
    
    /* Controls: hide 'Setup' header and upscale controls */
    .setup h2 {display:none;}
    .setup label {font-size: 1.8em;}
    .setup [data-baseweb="select"] * {font-size: 1.6em;}
    .setup [data-baseweb="select"] > div {min-height: 56px;}
    .setup .stButton > button {font-size: 1.25em; padding: 1rem 1.25rem;}
    /* Pink themed primary button for start */
    .start-btn button {background:#ffd7e5 !important; color:#000000 !important; border:1px solid #f5b8cd !important;}
    .start-btn button:hover {background:#fecadd !important;}
    @media (max-width: 1100px){ .cards {flex-direction: column;} .card, .card.center {height:auto; min-height: 240px;}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="home-container">', unsafe_allow_html=True)

    # Header / Logo row (restore larger logo)
    col_logo_l, col_logo_c, col_logo_r = st.columns([1,6,1])
    with col_logo_c:
        logo_path_candidates = [
            'assets/logo.png', 'assets/logo.jpeg', 'assets/music_adventures_logo.png', 'logo.png', 'logo.jpeg'
        ]
        shown = False
        for _p in logo_path_candidates:
            if os.path.exists(_p):
                st.image(_p, use_container_width=True)
                shown = True
                break
        if not shown:
            st.markdown('<div class="hero-title">Music Adventures</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-sub">Welcome! Let\'s discover…</div>', unsafe_allow_html=True)

    # Two cards row: How to start (pink, larger) and AI Agents (blue)
    st.markdown('<div class="cards">', unsafe_allow_html=True)
    c_left, c_right = st.columns([1,1])
    with c_left:
        st.markdown(
            '<div class="card blue center">'
            '<h4>How to start</h4>'
            '<p>Follow these steps to begin:</p>'
            '<ul>'
            '<li>Select Instrument and Grade below</li>'
            '<li>Choose an Exercise Type (try "Comprehensive Theory" first)</li>'
            '<li>Click Start MCQ Practice — an AMEB‑aware question with notation and audio will appear</li>'
            '<li>Answer and review the short feedback to improve</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c_right:
        st.markdown(
            '<div class="card blue">'
            '<h4>AI agents in this app</h4>'
            '<p>Three modules work together:</p>'
            '<ul>'
            '<li>Question Generator — AMEB‑aware MCQs by instrument and grade</li>'
            '<li>Notation & Audio Renderer — Abjad/LilyPond notation and audio output</li>'
            '<li>Feedback Coach — concise encouragement and guidance</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Helpful captions under cards (blue box text removed per request)

    # Selection controls under the cards
    st.markdown('<div class="setup">', unsafe_allow_html=True)
    # st.subheader("Setup")  # removed per request
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.instrument = st.selectbox(
            "Instrument",
            ["Piano", "Violin", "Guitar", "Flute", "Clarinet", "Trumpet", "Voice"],
            index=["Piano", "Violin", "Guitar", "Flute", "Clarinet", "Trumpet", "Voice"].index(st.session_state.instrument)
        )
    with col2:
        grade_label = st.selectbox(
            "Grade Level",
            ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", 
             "Associate Diploma", "Licentiate Diploma", "Fellowship Diploma"],
            index=max(0, (st.session_state.grade_num-1) if isinstance(st.session_state.grade_num,int) else 0)
        )
        grade_map = {
            "Grade 1": 1, "Grade 2": 2, "Grade 3": 3, "Grade 4": 4,
            "Grade 5": 5, "Grade 6": 6, "Grade 7": 7, "Grade 8": 8,
            "Associate Diploma": "associate_diploma",
            "Licentiate Diploma": "licentiate_diploma",
            "Fellowship Diploma": "fellowship_diploma"
        }
        st.session_state.grade_num = grade_map[grade_label]
    with col3:
        ex_list = ["Comprehensive Theory", "Harmony", "Ear Training", "Musical Form"]
        ex_value = st.session_state.exercise_type if st.session_state.exercise_type in ex_list else "Comprehensive Theory"
        st.session_state.exercise_type = st.selectbox("Exercise Type", ex_list, index=ex_list.index(ex_value))

    st.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.button("🚀 Start MCQ Practice", type="primary"):
        # Always start a fresh session from Home: resets history and counters
        start_new_mcq_question()
        log_change("Started new MCQ session from Home")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_mcq():
    st.title("🎯 MCQ Practice (Theory)")
    st.caption(f"Instrument: {st.session_state.instrument} · Grade: {st.session_state.grade_num} · Type: {st.session_state.exercise_type}")

    # Generate controls at top
    colg1, colg2 = st.columns([1,3])
    with colg1:
        # Button label changes after the first question is generated
        top_btn_label = "🎯 Generate Question" if st.session_state.current_question is None else "🎵 Generate Next Question"
        if st.button(top_btn_label, type="primary"):
            # If starting a brand new practice from no question yet, reset distribution counters lightly
            if st.session_state.current_question is None and not st.session_state.show_feedback:
                # Do not clear history; keep it to avoid immediate repeats across a run
                pass
            st.session_state.notation_data = None
            st.session_state.user_answer = None
            st.session_state.show_feedback = False
            st.session_state.current_feedback = None
            st.session_state.audio_cache = None
            st.session_state.question_id = f"q_{int(time.time())}"
            chosen_exercise = st.session_state.exercise_type
            if chosen_exercise == "Comprehensive Theory":
                import random
                allowed = ["Intervals", "Chords", "Scales", "Rhythm", "Harmony", "Ear Training", "Musical Form"]
                if isinstance(st.session_state.grade_num, int) and st.session_state.grade_num <= 4:
                    allowed.append("Note Reading")
                chosen_exercise = random.choice(allowed)
                st.session_state.exercise_type = chosen_exercise
            st.session_state.current_question = generate_question(
                st.session_state.instrument,
                st.session_state.grade_num,
                st.session_state.exercise_type,
            )
            if st.session_state.current_question:
                # Update history and letter distribution here as well (top button path)
                try:
                    qtext = st.session_state.current_question.get('question','')
                    correct_letter = str(st.session_state.current_question.get('correct_answer','')).strip()
                    if correct_letter in st.session_state.correct_letter_counts:
                        st.session_state.correct_letter_counts[correct_letter] += 1
                    opts = st.session_state.current_question.get('options', {}) or {}
                    correct_text = opts.get(correct_letter, '')
                    tags = _extract_tags(qtext, st.session_state.exercise_type, opts)
                    _append_history({
                        'question': qtext,
                        'correct_answer': correct_letter,
                        'correct_text': correct_text,
                        'topic': st.session_state.current_question.get('topic'),
                        'exercise_type': st.session_state.exercise_type,
                        'tags': tags
                    })
                    _maybe_rebalance_letters()
                except Exception:
                    pass
                st.session_state.notation_data = notation_generator_agent(
                    st.session_state.current_question,
                    st.session_state.instrument,
                    True,
                    st.session_state.exercise_type,
                )
            st.rerun()

    if st.session_state.current_question:
        display_question(st.session_state.current_question)
        display_feedback(st.session_state.current_question)
    else:
        st.info("Click 'Generate Question' to begin.")


def render_practical():
    st.title("🎼 Practical Practice")
    st.info("Placeholder – Practical exercises will be added here.")

# ---------------- Main ----------------

def main():
    # Sidebar Navigation
    with st.sidebar:
        # Replace title with logo if available
        logo_candidates = ['assets/logo.png','assets/logo.jpeg','logo.png','logo.jpeg']
        shown_logo = False
        for _p in logo_candidates:
            if os.path.exists(_p):
                st.image(_p, use_container_width=True)
                shown_logo = True
                break
        if not shown_logo:
            st.title("🎵 Music Theory Tutor")
        nav = st.radio("Navigate", ["Home", "MCQ Practice", "Practical Practice"], index=["home","mcq","practical"].index(st.session_state.route))
        route_map = {
            "Home": 'home',
            "MCQ Practice": 'mcq',
            "Practical Practice": 'practical'
        }
        if st.session_state.route != route_map[nav]:
            st.session_state.route = route_map[nav]
            log_change(f"Route changed to {st.session_state.route}")
            st.rerun()

    # Route rendering
    if st.session_state.route == 'home':
        render_home()
    elif st.session_state.route == 'mcq':
        render_mcq()
    else:
        render_practical()

if __name__ == "__main__":
    main() 