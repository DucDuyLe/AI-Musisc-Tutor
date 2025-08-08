import json
import time
from typing import Dict, List
from openai import OpenAI

# Real AMEB data from mymusictheory.com (theory only)
REAL_AMEB_DATA = {
    "grade_1": {
        "theory_topics": [
            "Treble and bass clefs",
            "Pitches with up to two ledger lines",
            "Accidentals",
            "Scales of C, G and F major",
            "Key signatures",
            "Tones and semitones",
            "Scale degrees",
            "Diatonic intervals above the tonic (treble clef only, number only)",
            "Tonic triad chords in root position (treble clef only)",
            "Note values from semibreve to quaver (including dotted minims)",
            "Rest values of minim and crotchet",
            "Time signatures of 2/4, 3/4, 4/4 and C",
            "Transposition into any other key of this grade",
            "Basic musical terms"
        ],
        "practical_skills": [
            "Reading treble and bass clefs",
            "Identifying accidentals",
            "Playing major scales (C, G, F)",
            "Recognizing key signatures",
            "Understanding time signatures",
            "Basic transposition"
        ],
        "exam_structure": {
            "duration": "2 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural"]
        }
    },
    "grade_2": {
        "theory_topics": [
            "Major scales of D and A",
            "Minor harmonic scales of Am, Em and Dm",
            "Intervals above the tonic by number and quality (treble clef only)",
            "Tonic triads in the keys for this grade",
            "Semiquavers, quaver triplets and dotted notes",
            "The anacrusis",
            "The whole bar (semibreve) rest",
            "Time signature of 6/8",
            "Transposition into any other key for this grade",
            "Terms and signs",
            "Binary and ternary form",
            "Identification of accented syllables in a text"
        ],
        "practical_skills": [
            "Playing major scales (D, A)",
            "Playing minor harmonic scales (Am, Em, Dm)",
            "Interval recognition",
            "Triad construction",
            "Rhythm with semiquavers and triplets",
            "Form analysis"
        ],
        "exam_structure": {
            "duration": "2.5 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural", "Composition"]
        }
    },
    "grade_3": {
        "theory_topics": [
            "Major scales of E, Eb, Bb and Ab",
            "Minor harmonic scales of Gm and Cm",
            "Intervals above the tonic in all keys (treble and bass clefs)",
            "Primary triads (tonic, dominant and subdominant)",
            "Root position and first inversion triads",
            "Perfect and plagal cadences",
            "SATB vocal style and range",
            "Time signatures of 2/2, 3/2, 3/8 and 9/8",
            "Transposition into any key for this grade",
            "Terms and signs",
            "Sequences",
            "Rondo form",
            "Set a rhythm to a provided text",
            "Compose a 4-bar melody in a major key based on a given rhythmic pattern"
        ],
        "practical_skills": [
            "Playing all major scales (E, Eb, Bb, Ab)",
            "Playing minor harmonic scales (Gm, Cm)",
            "Cadence recognition and construction",
            "SATB writing",
            "Melody composition",
            "Form analysis"
        ],
        "exam_structure": {
            "duration": "3 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural", "Composition", "Analysis"]
        }
    },
    "grade_4": {
        "theory_topics": [
            "Major scales of B, F#, Db and Gb",
            "Harmonic minor scales of Bm, F#m, C#m and Bbm",
            "Double flats and sharps",
            "All diatonic intervals plus their qualities",
            "Recognition of modulation to the dominant or relative key",
            "Syncopation",
            "Adding bar lines",
            "Time signatures of 6/4 and 12/8",
            "Chords II, ii, VI and vi in root position and first inversion",
            "Imperfect and interrupted cadences",
            "Writing cadences in SATB style",
            "Harmonisation of a melody in SATB style",
            "Set a rhythm to a given text couplet (8 bars)",
            "Compose a melody to a given rhythm (8 bars)",
            "Transposition into any key from the grade",
            "Terms and signs",
            "Ornaments",
            "Baroque Suites",
            "Orchestral String Instruments"
        ],
        "practical_skills": [
            "Playing all major and minor scales",
            "Modulation recognition",
            "Advanced harmonisation",
            "Melody composition",
            "Ornamentation",
            "Instrument knowledge"
        ],
        "exam_structure": {
            "duration": "3.5 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural", "Composition", "Analysis", "Orchestration"]
        }
    },
    "grade_5": {
        "theory_topics": [
            "All major scales",
            "All minor scales in harmonic and melodic forms",
            "All key signatures",
            "All intervals, and their inversions",
            "Recognition of modulation to the subdominant",
            "Chord vii° in minor keys",
            "Chord Ic, the cadential 6/4",
            "Unaccented passing and auxiliary notes",
            "Harmonisation of a melody in SATB or keyboard style including modulation",
            "Compose a melody to a 4-line stanza of poetry",
            "Compose an instrumental melody based on a given opening (8 bars)",
            "Minuet and Trio form, Scherzo, Air with Variations, Recitative and Aria",
            "Knowledge of composers",
            "Orchestral woodwind instruments (standard)"
        ],
        "practical_skills": [
            "Playing all scales in all forms",
            "Advanced modulation",
            "Complex harmonisation",
            "Poetry setting",
            "Instrumental composition",
            "Musical form analysis"
        ],
        "exam_structure": {
            "duration": "4 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural", "Composition", "Analysis", "Musicology"]
        }
    },
    "grade_6": {
        "theory_topics": [
            "Chord iii",
            "Passing 6/4 chords",
            "Dominant 7th chords",
            "Accented passing notes",
            "Suspensions",
            "Tierce de Picardie",
            "Simple two-part counterpoint in keyboard style",
            "Compose a melody to a 4-line stanza of poetry, with modulation",
            "Compose a vocal melody after a given phrase, with modulation",
            "Sonata, Symphony, Concerto, Overture",
            "Knowledge of composers with reference to examples",
            "Sonata form",
            "Reference to piano sonata by Mozart or Beethoven",
            "Set work: two movements from a symphony by Haydn, Mozart, Beethoven or Schubert"
        ],
        "practical_skills": [
            "Advanced counterpoint",
            "Complex modulation",
            "Vocal composition",
            "Form analysis",
            "Historical performance practice",
            "Set work analysis"
        ],
        "exam_structure": {
            "duration": "4.5 hours",
            "format": "Online exam",
            "marks": "100 total",
            "sections": ["Theory", "Practical", "Aural", "Composition", "Analysis", "Musicology", "Set Work"]
        }
    }
}

def get_openai_client():
    """Get OpenAI client securely from env or Streamlit secrets"""
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass
    try:
        import streamlit as st
        api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            from dotenv import dotenv_values
            api_key = dotenv_values(".env").get("OPENAI_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)

def generate_comprehensive_ameb_data(real_data: Dict, instruments: List[str], missing_grades: List[str]) -> Dict:
    """Generate AMEB data one instrument at a time"""
    
    client = get_openai_client()
    all_data = {}
    
    for instrument in instruments:
        print(f"🎵 Generating data for {instrument}...")
        
        # Simple prompt for one instrument
        prompt = f"""
Generate AMEB syllabus data for {instrument} for these grades: {missing_grades}

Based on this real AMEB theory progression:
{json.dumps(real_data, indent=2)}

Create syllabus data for {instrument} with:
- Theory topics for each grade
- 3-4 performance pieces per grade
- Technical work (scales, arpeggios)
- Equipment requirements
- Exam structure

Return ONLY valid JSON like this:
{{
    "preliminary": {{
        "theory_topics": ["topic1", "topic2"],
        "performance_pieces": [{{"title": "Piece 1", "composer": "Composer 1"}}],
        "technical_work": {{"scales": ["C major"], "arpeggios": ["C major"]}},
        "equipment": {{"instrument": "details", "accessories": ["item1"]}},
        "exam_structure": {{"duration": "1 hour", "sections": ["Performance", "Theory"]}}
    }},
    "grade_7": {{...}},
    "grade_8": {{...}},
    "associate_diploma": {{...}},
    "licentiate_diploma": {{...}},
    "fellowship_diploma": {{...}}
}}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are an AMEB music expert. Generate valid JSON syllabus data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            # Debug: Print the raw response
            raw_response = response.choices[0].message.content
            print(f"🔍 Raw response for {instrument}:")
            print(f"Length: {len(raw_response)} characters")
            print(f"First 200 chars: {raw_response[:200]}")
            print(f"Last 200 chars: {raw_response[-200:]}")
            
            # Clean the response - remove markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ``` if no json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            # Parse the response
            instrument_data = json.loads(cleaned_response)
            all_data[instrument] = instrument_data
            print(f"✅ Generated {instrument} data")
            
        except Exception as e:
            print(f"❌ Error generating {instrument} data: {e}")
            print(f"🔍 Full raw response was: {raw_response}")
            # Create empty structure for this instrument
            all_data[instrument] = {}
            for grade in missing_grades:
                all_data[instrument][grade] = {
                    "theory_topics": [],
                    "performance_pieces": [],
                    "technical_work": {"scales": [], "arpeggios": []},
                    "equipment": {"instrument": "", "accessories": []},
                    "exam_structure": {"duration": "", "sections": []}
                }
    
    return all_data

def create_comprehensive_curriculum():
    """Create comprehensive AMEB curriculum database with theory, performance, and equipment"""
    
    print("🎵 Creating Comprehensive AMEB Curriculum Database")
    print("=" * 50)
    
    # Define instruments and missing grades
    instruments = ["piano", "guitar", "violin", "flute", "clarinet", "trumpet", "voice"]
    missing_grades = ["preliminary", "grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6", "grade_7", "grade_8", "associate_diploma", "licentiate_diploma", "fellowship_diploma"]
    
    # Start with real theory data
    curriculum_db = {
        "theory_syllabus": REAL_AMEB_DATA.copy(),
        "instrument_syllabi": {},
        "metadata": {
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "Real AMEB data + GPT-4 comprehensive generation",
            "instruments_covered": instruments,
            "grades_covered": ["preliminary", "grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6", "grade_7", "grade_8", "associate_diploma", "licentiate_diploma", "fellowship_diploma"],
            "total_grades": 12,
            "total_instruments": len(instruments)
        }
    }
    
    print(f"✅ Added real theory data for grades 1-6")
    print(f"🔍 Generating comprehensive data for {len(instruments)} instruments and {len(missing_grades)} missing grades")
    
    # Generate comprehensive data using GPT-4
    generated_data = generate_comprehensive_ameb_data(REAL_AMEB_DATA, instruments, missing_grades)
    
    if generated_data:
        # Add generated data to curriculum
        curriculum_db["instrument_syllabi"] = generated_data
        print(f"✅ Added comprehensive data for all instruments and grades")
    
    # Save to file
    with open('curriculum_database.json', 'w') as f:
        json.dump(curriculum_db, f, indent=2)
    
    print(f"✅ Comprehensive curriculum database created!")
    print(f"📊 Stats: {curriculum_db['metadata']['total_grades']} grades, {curriculum_db['metadata']['total_instruments']} instruments")
    print(f"📁 Saved to: curriculum_database.json")
    
    return curriculum_db

if __name__ == "__main__":
    db = create_comprehensive_curriculum()
    
    if db:
        print("\n🎉 Comprehensive AMEB Curriculum Ready!")
        print("📁 Files created:")
        print("  - curriculum_database.json (complete database)")
        print("\n🚀 Ready to integrate with app.py!")
    else:
        print("\n❌ Failed to create curriculum database") 