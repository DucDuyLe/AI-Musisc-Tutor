import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Use environment or Streamlit secrets for API key; no hardcoded keys

def get_openai_client():
    """Get OpenAI client securely from env or Streamlit secrets"""
    import os
    # Ensure latest .env is loaded even if server started before .env was updated
    try:
        load_dotenv(override=True)
    except Exception:
        pass
    try:
        import streamlit as st
        api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Robust fallback: read .env directly
        try:
            from dotenv import dotenv_values
            cfg = dotenv_values(".env")
            api_key = cfg.get("OPENAI_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)

def load_curriculum_database():
    """Load the comprehensive curriculum database"""
    try:
        with open('curriculum_database.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Curriculum database not found!")
        return None

def get_grade_info(grade, instrument=None):
    """Get comprehensive grade information from curriculum database"""
    db = load_curriculum_database()
    if not db:
        return None
    
    # Handle different grade formats
    if isinstance(grade, str):
        # Handle diploma grades
        grade_key = grade
    elif grade > 0:
        # Handle numeric grades 1-8
        grade_key = f"grade_{grade}"
    else:
        # Handle preliminary
        grade_key = "preliminary"
    
    # Get theory information
    theory_info = db.get('theory_syllabus', {}).get(grade_key, {})
    
    # Get instrument-specific information
    instrument_info = None
    if instrument and instrument in db.get('instrument_syllabi', {}):
        instrument_data = db['instrument_syllabi'][instrument]
        instrument_info = instrument_data.get(grade_key, {})
    
    return {
        'theory': theory_info,
        'instrument': instrument_info,
        'grade_key': grade_key
    }

def get_available_topics(grade):
    """Get available topics for a grade"""
    grade_info = get_grade_info(grade)
    if not grade_info or not grade_info['theory']:
        return []
    
    return grade_info['theory'].get('theory_topics', [])

def generate_curriculum_aware_question(subject, grade, exercise_type=None, history=None, target_correct_letter: Optional[str] = None):
    """Generate a comprehensive curriculum-aware question using AI"""
    
    client = get_openai_client()
    
    # Handle subject type
    if subject.lower() == "music theory":
        # For Music Theory, use theory syllabus only
        grade_info = get_grade_info(grade)
        instrument = None
    else:
        # For instruments, use both theory and instrument-specific data
        grade_info = get_grade_info(grade, subject.lower())
        instrument = subject.lower()
    
    if not grade_info:
        return None

    # Helper: determine numeric grade for rules
    def _grade_num():
        gkey = grade_info['grade_key']
        try:
            if isinstance(grade, int):
                return grade
            if isinstance(gkey, str) and gkey.startswith('grade_'):
                return int(gkey.split('_')[-1])
        except Exception:
            pass
        return None

    grade_num = _grade_num()

    # Build ALLOWED pools per grade/exercise
    def _allowed_pool_text(ex_type: str, gnum: Optional[int]) -> str:
        if gnum is None:
            # fall back to mid-level
            gnum = 5
        if ex_type == "Intervals":
            if gnum >= 7:
                allowed = [
                    "tritone (augmented 4th / diminished 5th)",
                    "minor 7th", "major 7th",
                    "compound intervals: 9th, 10th, 11th",
                    "augmented/diminished 2nd/3rd/6th"
                ]
            elif gnum >= 5:
                allowed = [
                    "minor/major 2nd", "minor/major 3rd", "perfect 4th",
                    "tritone", "perfect 5th", "minor/major 6th",
                    "minor/major 7th", "octave"
                ]
            else:
                allowed = ["m2", "M2", "m3", "M3", "P4", "P5", "P8"]
            return "ALLOWED INTERVALS: " + ", ".join(allowed)

        if ex_type == "Chords":
            if gnum >= 7:
                allowed = [
                    "dominant 7th", "major 7th", "minor 7th",
                    "half-diminished 7th", "diminished 7th"
                ]
            elif gnum >= 5:
                allowed = ["major triad", "minor triad", "diminished triad", "augmented triad"]
            else:
                allowed = ["major triad", "minor triad"]
            return "ALLOWED CHORD QUALITIES: " + ", ".join(allowed)

        if ex_type == "Rhythm":
            if gnum >= 7:
                allowed = ["5/8", "7/8", "9/8", "12/8", "5/4", "7/4"]
            elif gnum >= 5:
                allowed = ["6/8", "9/8", "12/8", "5/4"]
            else:
                allowed = ["2/4", "3/4", "4/4"]
            return "ALLOWED TIME SIGNATURES: " + ", ".join(allowed)

        if ex_type == "Harmony":
            if gnum >= 7:
                allowed = ["secondary dominants", "Neapolitan 6th", "Augmented sixths", "chromatic modulation"]
            elif gnum >= 5:
                allowed = ["modulation to relative/parallel keys", "dominant 7th usage", "cadences"]
            else:
                allowed = ["basic cadences", "I-IV-V progressions"]
            return "ALLOWED HARMONY TOPICS: " + ", ".join(allowed)

        if ex_type == "Musical Form":
            if gnum >= 7:
                allowed = ["rondo", "sonata-allegro (high level)", "theme and variations"]
            elif gnum >= 5:
                allowed = ["ternary", "rondo", "binary (expanded)"]
            else:
                allowed = ["binary", "ternary"]
            return "ALLOWED FORMS: " + ", ".join(allowed)

        if ex_type == "Ear Training":
            # mirror intervals/chords by grade; options omit note names
            if gnum >= 7:
                allowed = ["tritone", "m7", "M7", "compound intervals (9th/10th/11th)",
                           "dominant7", "major7", "minor7", "half-diminished", "diminished7"]
            elif gnum >= 5:
                allowed = ["m2", "M2", "m3", "M3", "P4", "TT", "P5", "m6", "M6", "m7", "M7",
                           "major/minor/diminished/augmented triads"]
            else:
                allowed = ["m2", "M2", "m3", "M3", "P4", "P5", "P8", "major/minor triads"]
            return "ALLOWED EAR TRAINING CLASSES: " + ", ".join(allowed)

        if ex_type == "Note Reading":
            if gnum >= 5:
                return ("ALLOWED NOTE READING (advanced): Use ledger-line notes and/or accidentals; "
                        "avoid basic line/space prompts.")
            return "ALLOWED NOTE READING: Basic treble/bass staff positions."

        if ex_type == "Scales":
            if gnum >= 7:
                allowed = ["harmonic minor", "melodic minor", "modes", "chromatic"]
            elif gnum >= 5:
                allowed = ["major", "natural minor", "harmonic minor", "melodic minor"]
            else:
                allowed = ["major", "natural minor"]
            return "ALLOWED SCALES: " + ", ".join(allowed)

        return ""

    # Map exercise types to question types
    exercise_type_mapping = {
        "Intervals": "interval",
        "Chords": "chord", 
        "Scales": "scale",
        "Rhythm": "rhythm",
        "Harmony": "harmony",
        "Ear Training": "ear_training",
        "Musical Form": "musical_form",
        "Note Reading": "note_identification"
    }
    
    # Get the question type from exercise type
    question_type = exercise_type_mapping.get(exercise_type, "interval")
    
    # Build comprehensive context
    context = f"""
    AMEB {grade_info['grade_key'].upper()} CURRICULUM CONTEXT:
    
    THEORY TOPICS: {grade_info['theory'].get('theory_topics', [])}
    PRACTICAL SKILLS: {grade_info['theory'].get('practical_skills', [])}
    EXAM STRUCTURE: {grade_info['theory'].get('exam_structure', {})}
    """
    
    if instrument and grade_info['instrument']:
        context += f"""
    INSTRUMENT-SPECIFIC ({instrument.upper()}):
    PERFORMANCE PIECES: {grade_info['instrument'].get('performance_pieces', [])}
    TECHNICAL WORK: {grade_info['instrument'].get('technical_work', {})}
    EQUIPMENT: {grade_info['instrument'].get('equipment', {})}
    INSTRUMENT EXAM STRUCTURE: {grade_info['instrument'].get('exam_structure', {})}
    """
    
    # Add exercise type focus
    if exercise_type:
        context += f"\nEXERCISE TYPE: {exercise_type}"
        context += f"\nQUESTION TYPE: {question_type}"
        context += f"\nIMPORTANT: Generate a question specifically about {exercise_type.lower()} concepts."
        allowed_text = _allowed_pool_text(exercise_type, grade_num)
        if allowed_text:
            context += f"\n{allowed_text}"
            context += "\nCRITICAL: Choose ONLY from the ALLOWED list above based on the selected grade."
        # Grade-aware difficulty for ear training
        if exercise_type == "Ear Training":
            # Determine numeric grade if possible
            gkey = grade_info['grade_key']
            gnum = None
            try:
                if isinstance(gkey, str) and gkey.startswith('grade_'):
                    gnum = int(gkey.split('_')[-1])
            except Exception:
                gnum = None
            if gnum is None and isinstance(grade, int):
                gnum = grade
            if gnum is not None:
                if gnum >= 7:
                    context += ("\nEAR TRAINING DIFFICULTY (Grade 7-8): "
                                "use compound intervals (9th/10th/11th), tritone, and seventh-chord qualities "
                                "(dominant 7th, major 7th, minor 7th, half-diminished, diminished 7th). "
                                "Avoid basic triads unless mixing difficulty. Rotate items for variety.")
                elif gnum >= 5:
                    context += ("\nEAR TRAINING DIFFICULTY (Grade 5-6): "
                                "use perfect/major/minor intervals up to the octave and triad qualities "
                                "(major, minor, diminished, augmented). Include occasional tritone.")
                else:
                    context += ("\nEAR TRAINING DIFFICULTY (Grades 1-4): "
                                "focus on stepwise and simple intervals (m2/M2, m3/M3, P4, P5, P8) and major/minor triads.")
        # Grade-aware difficulty for intervals (written)
        if exercise_type == "Intervals":
            gkey = grade_info['grade_key']
            gnum = None
            try:
                if isinstance(gkey, str) and gkey.startswith('grade_'):
                    gnum = int(gkey.split('_')[-1])
            except Exception:
                gnum = None
            if gnum is None and isinstance(grade, int):
                gnum = grade
            if gnum is not None:
                if gnum >= 7:
                    context += ("\nINTERVAL DIFFICULTY (Grade 7-8): Use advanced intervals only — include tritone (augmented 4th/diminished 5th), major/minor 7ths, major/minor 9ths/10ths/11ths (compound), augmented/diminished 2nds/3rds/6ths. Avoid basic intervals like M2/M3/P4/P5 unless mixing difficulty. Include accidentals and enharmonic spellings when appropriate.")
                elif gnum >= 5:
                    context += ("\nINTERVAL DIFFICULTY (Grade 5-6): Use full set up to octave with accidentals (m2/M2, m3/M3, P4, tritone, P5, m6/M6, m7/M7).")
                else:
                    context += ("\nINTERVAL DIFFICULTY (Grades 1-4): Focus on simple diatonic intervals up to the 6th; avoid chromatic alterations.")

    # Determine question focus
    if subject.lower() == "music theory":
        focus = "pure music theory concepts"
        subject_context = "Focus on comprehensive music theory including harmony, analysis, composition, and advanced theoretical concepts."
    else:
        focus = f"{instrument} performance and theory"
        subject_context = f"Include {instrument}-specific techniques and requirements while covering relevant theory concepts."
    
    # Add history context to reduce repetition
    history = history or []
    def _summarize(h):
        try:
            if isinstance(h, dict):
                q = h.get('question', '')
                ca = h.get('correct_answer', '')
                topic = h.get('topic', '')
                return f"Q: {q} | Correct: {ca} | Topic: {topic}"
            return str(h)
        except Exception:
            return str(h)
    recent = history[-8:]
    history_block = ("\nRECENT_QUESTIONS_TO_AVOID (do not repeat wording, note choices, or exact concepts):\n"
                     + "\n".join([f"- {_summarize(h)}" for h in recent])) if recent else ""

    prompt = f"""
    You are an expert AMEB English music theory teacher. Generate a comprehensive MCQ question with EXACTLY 1 correct answer and 3 wrong answers.

    Generate an AMEB-compliant music theory MCQ question for {subject} {grade_info['grade_key']}.
    
    {context}
    
    SUBJECT FOCUS: {subject_context}
    
    CRITICAL EXERCISE TYPE REQUIREMENT:
    - EXERCISE TYPE: {exercise_type}
    - QUESTION TYPE: {question_type}
    - You MUST generate a question specifically about {exercise_type.lower()} concepts
    - The question should be appropriate for {grade_info['grade_key']} level
    - Focus on {exercise_type.lower()} skills and knowledge
    
    SPECIFIC EXERCISE TYPE REQUIREMENTS:
    - For "Ear Training": Generate questions about AUDIO RECOGNITION (intervals, chords, scales, rhythms)
      - Do NOT include specific note letters anywhere in the question OR options
      - INTERVAL tasks: ask for the interval class (e.g., Major third, Perfect fifth). Options must be interval classes only
      - CHORD tasks: ask for the CHORD QUALITY only (Major, Minor, Diminished, Augmented). Options must be qualities only (no roots)
      - SCALE tasks: ask for the SCALE TYPE only (Major, Natural minor, Harmonic minor, Melodic minor, Mode). Options must be scale types only
      - RHYTHM tasks: ask for the time-feel/pattern classification (simple/compound, beat groupings); no note values required
      - Ensure VARIETY across runs; avoid repeating the same interval/chord quality consecutively
    - For "Note Reading": Generate questions about NOTE IDENTIFICATION on staff
    - For "Intervals": Generate questions about INTERVAL RECOGNITION between notes
    - For "Chords": Generate questions about CHORD IDENTIFICATION and construction
    - For "Scales": Generate questions about SCALE RECOGNITION and construction
    - For "Rhythm": Generate questions about RHYTHMIC PATTERNS and time signatures
    - For "Harmony": Generate questions about CHORD PROGRESSIONS and harmonic function
    - For "Musical Form": Generate questions about MUSICAL STRUCTURE and form analysis
    
    ENHANCED QUESTION TYPES TO INCLUDE:
    - RHYTHM: Time signatures, beat counting, syncopation, rhythmic patterns
    - HARMONY: Chord progressions, voice leading, dominant sevenths, harmonic function
    - EAR TRAINING: Audio-based interval/chord/scale/rhythm recognition (grade-appropriate as specified above)
    - MUSICAL FORM: Phrase structure, sections, repetition patterns, motifs
    
    CRITICAL MCQ REQUIREMENTS:
    - You MUST create EXACTLY 4 options: A, B, C, D
    - You MUST have EXACTLY 1 correct answer and 3 wrong answers
    - The correct answer MUST be the actual musical answer to the question
    - The 3 wrong answers MUST be plausible but incorrect musical answers
    - All options must be musically valid but only one can be correct
    - CRITICAL: The correct answer MUST be included in the options
    - Rotate content so repeated questions do not always use the same notes (avoid always C–E for intervals)
    - For note identification: if correct is "G", wrong answers could be "F", "A", "B"
    - For intervals: if correct is "Major third", wrong answers could be "Minor third", "Perfect fourth", "Perfect fifth"
    - For chords: if correct is "C major", wrong answers could be "D major", "F major", "G major"
    - For scales: if asking about harmonic minor, the correct answer MUST be the raised 7th note (e.g., "A#" for B harmonic minor)
    - For scale questions: if correct is "A#", wrong answers could be "A", "B", "C#"
    - For rhythm: if correct is "4/4", wrong answers could be "3/4", "2/4", "6/8"
    - For harmony: if correct is "I-IV-V", wrong answers could be "I-V-vi", "ii-V-I", "I-vi-IV"
    - For ear training: present only audio and options; DO NOT reveal notes in question text; follow the grade-appropriate difficulty rules above
    - For written intervals: follow the grade-appropriate interval difficulty rules above
    - For form: if correct is "AABA", wrong answers could be "ABAB", "AABB", "ABAC"
    
    CURRICULUM REQUIREMENTS:
    - You MUST use topics from the provided {grade_info['grade_key']} curriculum ONLY
    - For fellowship_diploma: Focus on original research, advanced compositional techniques, complex counterpoint (triple/quadruple fugue), contemporary/cross-cultural analysis, unconventional orchestration, non-standard notation
    - For licentiate_diploma: Focus on advanced chromatic/post-tonal harmony, complex counterpoint (double fugue), 20th/21st-century analysis, advanced orchestration, contemporary ensembles
    - For associate_diploma: Focus on comprehensive chromatic harmony, advanced modulation, complex counterpoint (canon, invertible counterpoint, fugue), large-scale form analysis, full orchestration
    - For Grade 8: Focus on advanced chromatic harmony, enharmonic modulation, extended tertian chords (9th, 11th, 13th), altered dominants, complex modulations, double/triple counterpoint, complete fugues, advanced orchestration, 20th-century analysis
    - For Grade 7: Focus on chromatic harmony (Neapolitan 6th, augmented 6th), secondary dominants, modulation to remote keys, diminished 7th chords, three-part counterpoint, fugal exposition, Romantic analysis, orchestration basics
    - For Grade 6: Focus on chord iii, passing 6/4 chords, dominant 7th chords, accented passing notes, suspensions, Tierce de Picardie, two-part counterpoint, vocal composition with modulation, sonata form, set works
    - For Grade 5: Focus on advanced intervals, complex modulation, advanced time signatures, SATB harmonization, Baroque suites, orchestral instruments
    - For Grade 4: Focus on harmonic minor scales, double sharps/flats, diatonic intervals with qualities, modulation, SATB harmonization, advanced time signatures (6/4, 12/8), Baroque suites
    - For Grade 3: Focus on minor scales, compound time, triads, basic modulation, simple harmonization
    - For Grade 2: Focus on major scales, basic intervals, simple time signatures, basic chords
    - For Grade 1: Focus on basic note reading, simple rhythms, basic musical terms
    - DO NOT use basic note identification (treble clef lines/spaces) for Grade 3+ - this is Grade 1-2 content
    - Create questions that are COMPLETELY UNDERSTANDABLE STANDALONE
    - Include all necessary context and information in the question text
    - Use language appropriate for {grade_info['grade_key']} level
    - Include proper musical terminology from the curriculum
    - Make it engaging and educational with detailed context
    - Ensure it's grade-appropriate difficulty
    - Focus on {focus}
    - Use topics from the provided curriculum data
    - ALWAYS end the question with: "Refer to the notation image below for visual reference."
    - DO NOT include notation_description - the notation will be generated from the question text
    
    PARSABLE QUESTION FORMATS (Use these exact formats for easier parsing):
    - For intervals: "What is the interval between [NOTE1] and [NOTE2]?"
    - For chords: "What is the [ROMAN_NUMERAL] chord in [KEY] [MODE]?" (e.g., "What is the I chord in C major?")
    - For scales: "What is the [KEY] [MODE] scale?" (e.g., "What is the C major scale?")
    - For time signatures: "What is the time signature [SIGNATURE]?" (e.g., "What is the time signature 3/4?")
    - For note identification: "What note is on the [POSITION] of the [CLEF] clef?" (e.g., "What note is on the second line of the treble clef?")
    - For key signatures: "What is the key signature of [KEY] [MODE]?" (e.g., "What is the key signature of D major?")
    - For ear training: "Listen to the audio and identify the interval" (no note names in the question)
    - For musical form: "What musical form is this piece?" (e.g., "What musical form is this piece?")
    
    RESPONSE FORMAT (JSON only):
    {{
        "question": "Complete standalone question text that includes all necessary context and ends with 'Refer to the notation image below for visual reference.'",
        "options": {{
            "A": "EXACTLY 1 correct musical answer",
            "B": "EXACTLY 1 wrong but plausible musical answer", 
            "C": "EXACTLY 1 wrong but plausible musical answer",
            "D": "EXACTLY 1 wrong but plausible musical answer"
        }},
        "correct_answer": "A/B/C/D (the letter of the correct answer)",
        "explanation": "Detailed explanation using curriculum concepts",
        "topic": "Specific topic from curriculum",
        "notation_description": "REMOVED - notation will be generated from question text",
        "difficulty": "easy/medium/hard",
        "grade_appropriate": true,
        "curriculum_reference": "Specific curriculum concept referenced"
    }}
    """
    # Append instruction to avoid repeats
    prompt += history_block
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AMEB English music theory teacher. Generate comprehensive MCQ questions with EXACTLY 1 correct answer and 3 wrong answers. Always ensure the correct answer is the actual musical answer to the question."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Clean the response - remove markdown code blocks if present
        raw_msg = response.choices[0].message
        raw_response = (raw_msg.content if hasattr(raw_msg, 'content') else raw_msg) or ""
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Try strict JSON load; if it fails, attempt to fix common issues
        try:
            result = json.loads(cleaned_response)
        except Exception:
            # Heuristic fix: trim content to first/last braces
            try:
                start = cleaned_response.find('{')
                end = cleaned_response.rfind('}')
                if start != -1 and end != -1:
                    result = json.loads(cleaned_response[start:end+1])
                else:
                    raise
            except Exception:
                raise
        
        # Normalize/validate structure
        if 'options' not in result or not isinstance(result['options'], dict):
            result['options'] = {}
        # Ensure A-D keys exist (fill with placeholders if missing to avoid KeyErrors downstream)
        for key in ["A","B","C","D"]:
            result['options'].setdefault(key, "")
        # Normalize correct_answer letter
        ca = str(result.get('correct_answer', '')).strip().upper()
        if len(ca) > 1:
            # Accept formats like "Option A" or "A)"
            for letter in ["A","B","C","D"]:
                if letter in ca:
                    ca = letter
                    break
        if ca not in ["A","B","C","D"]:
            # fallback default
            ca = "A"
        result['correct_answer'] = ca
        
        # Optional post-processing to balance correct answer letters
        try:
            if target_correct_letter and target_correct_letter in ["A","B","C","D"]:
                options = result.get('options', {})
                current_letter = str(result.get('correct_answer', '')).strip()
                if current_letter in options and target_correct_letter in ["A","B","C","D"]:
                    if current_letter != target_correct_letter:
                        # Reassign letters so that the correct option moves to target_correct_letter
                        correct_text = options.get(current_letter)
                        # Build list of wrong texts in original A-D order excluding the correct current letter
                        order = ["A","B","C","D"]
                        wrong_letters = [l for l in order if l != current_letter]
                        wrong_texts = [options.get(l) for l in wrong_letters]
                        # Create new mapping assigning correct to target, and fill others in remaining letter order
                        remaining_letters = [l for l in order if l != target_correct_letter]
                        new_options = {}
                        new_options[target_correct_letter] = correct_text
                        # Fill remaining letters with wrong texts in order
                        for l, txt in zip(remaining_letters, wrong_texts):
                            new_options[l] = txt
                        result['options'] = new_options
                        result['correct_answer'] = target_correct_letter
            else:
                # No target provided: rotate correct letter pseudo-randomly to avoid bias
                options = result.get('options', {})
                current_letter = str(result.get('correct_answer', '')).strip()
                order = ["A","B","C","D"]
                if current_letter in order and len(options) == 4:
                    import random, time
                    random.seed(time.time())
                    target = random.choice(order)
                    if target != current_letter:
                        correct_text = options.get(current_letter)
                        wrong_letters = [l for l in order if l != current_letter]
                        wrong_texts = [options.get(l) for l in wrong_letters]
                        remaining_letters = [l for l in order if l != target]
                        new_options = {target: correct_text}
                        for l, txt in zip(remaining_letters, wrong_texts):
                            new_options[l] = txt
                        result['options'] = new_options
                        result['correct_answer'] = target
        except Exception:
            # If anything goes wrong, fall back to original result
            pass
        
        return result
        
    except Exception as e:
        print(f"Error generating curriculum-aware question: {e}")
        return None

def get_curriculum_stats():
    """Get statistics about the curriculum database"""
    db = load_curriculum_database()
    if not db:
        return None
    
    return db.get('metadata', {})

if __name__ == "__main__":
    # Simple test to verify the module loads correctly
    print("✅ Question generator module loaded successfully!")
    print("📚 Ready to generate curriculum-aware questions!") 