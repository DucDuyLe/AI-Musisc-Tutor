import re
import json
from typing import Dict, Optional, Any
from openai import OpenAI

class QuestionParser:
    """
    Enhanced question parser with multiple parsing strategies.
    Uses regex patterns first (fast, deterministic), then GPT as fallback.
    """
    
    def __init__(self):
        self.patterns = {
            'interval': [
                # Capture note names with optional #/b accidentals
                r'between[^A-Ga-g#b]*([A-Ga-g][#b]?)[^A-Ga-g#b]*and[^A-Ga-g#b]*([A-Ga-g][#b]?)',
                r'([A-Ga-g][#b]?)[^A-Ga-g#b]*([A-Ga-g][#b]?)[^\n]*?interval',
                r'interval[^A-Ga-g#b]*([A-Ga-g][#b]?)[^A-Ga-g#b]*([A-Ga-g][#b]?)',
                r'([A-Ga-g][#b]?)[^A-Ga-g#b]*([A-Ga-g][#b]?)[^\n]*?quality'
            ],
            'chord': [
                r'(\w+)\s+chord.*?(\w+)\s+major',
                r'(\w+)\s+chord.*?(\w+)\s+minor',
                r'chord.*?(\w+).*?(\w+)',
                r'(\w+)\s+triad.*?(\w+)'
            ],
            'scale': [
                r'harmonic\s+minor\s+scale\s+of\s+(\w+)\s+minor',
                r'melodic\s+minor\s+scale\s+of\s+(\w+)\s+minor',
                r'natural\s+minor\s+scale\s+of\s+(\w+)\s+minor',
                r'scale\s+of\s+(\w+)\s+harmonic\s+minor',
                r'scale\s+of\s+(\w+)\s+melodic\s+minor',
                r'scale\s+of\s+(\w+)\s+naturel\s+minor',
                r'scale\s+of\s+(\w+)\s+minor',
                r'scale\s+of\s+(\w+)\s+major',
                r'(\w+)\s+harmonic\s+minor\s+scale',
                r'(\w+)\s+melodic\s+minor\s+scale',
                r'(\w+)\s+natural\s+minor\s+scale',
                r'(\w+)\s+minor\s+scale',
                r'(\w+)\s+major\s+scale',
                r'scale.*?(\w+).*?(\w+)',
                r'(\w+).*?scale'
            ],
            'time_signature': [
                r'time signature.*?(\d+/\d+)',
                r'(\d+/\d+).*?time signature',
                r'(\d+/\d+).*?beats'
            ],
            'note_identification': [
                r'note.*?(\w+).*?line',
                r'(\w+).*?note.*?treble',
                r'(\w+).*?note.*?bass'
            ],
            'key_signature': [
                r'key signature.*?of\s+(\w+)\s+(\w+)',
                r'(\w+)\s+key\s+(\w+)',
                r'key signature.*?(\w+)',
                r'key.*?(\w+)\s+(\w+)'
            ],
            'rhythm': [
                r'rhythm.*?(\d+/\d+)',
                r'(\d+/\d+).*?rhythm',
                r'beat.*?(\d+/\d+)',
                r'(\d+/\d+).*?beat',
                r'syncopation',
                r'syncopated',
                r'rhythmic.*?pattern',
                r'pattern.*?rhythm'
            ],
            'harmony': [
                r'progression.*?(\w+).*?(\w+).*?(\w+)',
                r'(\w+).*?(\w+).*?(\w+).*?progression',
                r'chord.*?progression',
                r'voice.*?leading',
                r'dominant.*?seventh',
                r'seventh.*?chord',
                r'harmonic.*?function',
                r'function.*?chord'
            ],
            'ear_training': [
                r'interval.*?hear',
                r'hear.*?interval',
                r'chord.*?quality.*?hear',
                r'hear.*?chord',
                r'scale.*?hear',
                r'hear.*?scale',
                r'rhythm.*?hear',
                r'hear.*?rhythm',
                r'pitch.*?recognition',
                r'recognition.*?pitch'
            ],
            'musical_form': [
                r'form.*?(\w+)',
                r'(\w+).*?form',
                r'phrase.*?structure',
                r'structure.*?phrase',
                r'section.*?(\w+)',
                r'(\w+).*?section',
                r'repetition.*?pattern',
                r'pattern.*?repetition',
                r'motif.*?repeat',
                r'repeat.*?motif'
            ]
        }
        
        # Musical note patterns for validation
        self.valid_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        self.valid_accidentals = ['#', 'b', 'sharp', 'flat']
        
        # Initialize OpenAI client for fallback parsing (lazy init later to avoid secrets issues)
        self.client = None
    
    def _get_openai_client(self):
        """Get OpenAI client from env/secrets without hardcoding."""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            try:
                import streamlit as st  # Optional
                api_key = st.secrets.get('OPENAI_API_KEY')  # type: ignore[attr-defined]
            except Exception:
                api_key = None
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    
    def parse(self, question: str, debug: bool = False) -> Dict[str, Any]:
        """
        Parse a music theory question into structured data.
        Returns a dictionary with question type and extracted parameters.
        """
        question = question.strip()
        
        # Try regex patterns first (fast, deterministic)
        result = self._regex_parse(question)
        if result:
            if debug:
                print(f"✅ Regex parsed: {result['type']}")
            return result
        
        # Fallback to GPT only if needed
        if debug:
            print(f"❌ Regex failed, using GPT fallback for: {question[:50]}...")
        return self._gpt_parse(question)
    
    def _regex_parse(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Parse using regex patterns for common question types.
        Returns None if no pattern matches.
        """
        question_lower = question.lower()
        
        # Check each pattern type
        for question_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, question_lower, re.IGNORECASE)
                if match:
                    return self._build_parsed_data(question_type, match, question)
        
        return None
    
    def _build_parsed_data(self, question_type: str, match, original_question: str) -> Dict[str, Any]:
        """
        Build structured data from regex match.
        """
        groups = match.groups()
        
        if question_type == 'interval':
            return {
                'type': 'interval',
                'start_note': groups[0].upper(),
                'end_note': groups[1].upper(),
                'original_question': original_question,
                'confidence': 'high'
            }
        
        elif question_type == 'chord':
            # Handle different chord patterns
            if len(groups) >= 2:
                # Check if first group is a roman numeral
                chord_degree = groups[0].lower()
                key = groups[1].upper()
                
                # Convert common chord names to roman numerals
                if chord_degree in ['tonic', 'root']:
                    chord_degree = 'i' if 'minor' in original_question.lower() else 'I'
                elif chord_degree in ['supertonic', 'second']:
                    chord_degree = 'ii'
                elif chord_degree in ['mediant', 'third']:
                    chord_degree = 'iii'
                elif chord_degree in ['subdominant', 'fourth']:
                    chord_degree = 'iv' if 'minor' in original_question.lower() else 'IV'
                elif chord_degree in ['dominant', 'fifth']:
                    chord_degree = 'v' if 'minor' in original_question.lower() else 'V'
                elif chord_degree in ['submediant', 'sixth']:
                    chord_degree = 'vi'
                elif chord_degree in ['leading', 'seventh']:
                    chord_degree = 'vii'
                
                return {
                    'type': 'chord',
                    'chord_degree': chord_degree,
                    'key': key,
                    'mode': 'major' if 'major' in original_question.lower() else 'minor',
                    'original_question': original_question,
                    'confidence': 'high'
                }
            else:
                return {
                    'type': 'chord',
                    'chord_degree': 'I',  # Default
                    'key': 'C',
                    'mode': 'major',
                    'original_question': original_question,
                    'confidence': 'low'
                }
        
        elif question_type == 'scale':
            # Determine scale type from the question
            question_lower = original_question.lower()
            if 'harmonic' in question_lower:
                mode = 'harmonic_minor'
            elif 'natural' in question_lower:
                mode = 'natural_minor'
            elif 'melodic' in question_lower:
                mode = 'melodic_minor'
            elif 'major' in question_lower:
                mode = 'major'
            else:
                mode = 'minor'  # default to natural minor
            
            # Improved key extraction from captured groups
            import re
            NOTE_REGEX = r'[A-Ga-g](#|b|♯|♭)?m?'
            
            # If multiple groups, use the one that looks like a note
            key_candidates = [g for g in groups if g.lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g']]
            key = key_candidates[0].upper() if key_candidates else groups[0].upper()
            
            return {
                'type': 'scale',
                'key': key,
                'mode': mode,
                'original_question': original_question,
                'confidence': 'high'
            }
        
        elif question_type == 'time_signature':
            return {
                'type': 'time_signature',
                'signature': groups[0],
                'original_question': original_question,
                'confidence': 'high'
            }
        
        elif question_type == 'note_identification':
            return {
                'type': 'note_identification',
                'note': groups[0].upper(),
                'clef': 'treble' if 'treble' in original_question.lower() else 'bass',
                'original_question': original_question,
                'confidence': 'high'
            }
        
        elif question_type == 'key_signature':
            # Handle different key signature patterns
            if len(groups) >= 2:
                # For pattern "key signature of G major", groups[0]="SIGNATURE", groups[1]="G"
                # For pattern "G key major", groups[0]="G", groups[1]="MAJOR"
                if groups[0].upper() == 'SIGNATURE':
                    key = groups[1].upper()
                else:
                    key = groups[0].upper()
            else:
                key = groups[0].upper()
            
            return {
                'type': 'key_signature',
                'key': key,
                'mode': 'major' if 'major' in original_question.lower() else 'minor',
                'original_question': original_question,
                'confidence': 'high'
            }
        
        return {
            'type': 'unknown',
            'original_question': original_question,
            'confidence': 'low'
        }
    
    def _gpt_parse(self, question: str) -> Dict[str, Any]:
        """
        Fallback parsing using GPT for complex or ambiguous questions.
        """
        try:
            if self.client is None:
                self.client = self._get_openai_client()
            if self.client is None:
                return {
                    'type': 'unknown',
                    'original_question': question,
                    'confidence': 'low',
                    'error': 'OpenAI API key not set'
                }
            prompt = f"""
            Parse this music theory question into structured data.
            
            Question: {question}
            
            Extract the following information:
            1. Question type (interval, chord, scale, time_signature, note_identification, key_signature)
            2. Musical parameters (notes, keys, degrees, etc.)
            3. Any additional context
            
            Return ONLY a JSON object with this structure:
            {{
                "type": "question_type",
                "parameters": {{}},
                "original_question": "{question}",
                "confidence": "medium"
            }}
            
            Examples:
            - "What is the interval between C and E?" → {{"type": "interval", "parameters": {{"start_note": "C", "end_note": "E"}}}}
            - "What is the iii chord in C major?" → {{"type": "chord", "parameters": {{"degree": "iii", "key": "C", "mode": "major"}}}}
            - "What is the C major scale?" → {{"type": "scale", "parameters": {{"key": "C", "mode": "major"}}}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a music theory expert. Parse questions into structured data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                parsed = json.loads(content)
                parsed['original_question'] = question
                return parsed
            except json.JSONDecodeError:
                # If JSON parsing fails, return basic structure
                return {
                    'type': 'unknown',
                    'original_question': question,
                    'confidence': 'low',
                    'error': 'Failed to parse GPT response'
                }
                
        except Exception as e:
            return {
                'type': 'unknown',
                'original_question': question,
                'confidence': 'low',
                'error': str(e)
            }
    
    def validate_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate that parsed data contains required fields for each type.
        """
        if not parsed_data or 'type' not in parsed_data:
            return False
        
        question_type = parsed_data['type']
        
        if question_type == 'interval':
            return 'start_note' in parsed_data and 'end_note' in parsed_data
        
        elif question_type == 'chord':
            return 'chord_degree' in parsed_data and 'key' in parsed_data
        
        elif question_type == 'scale':
            return 'key' in parsed_data
        
        elif question_type == 'time_signature':
            return 'signature' in parsed_data
        
        elif question_type == 'note_identification':
            return 'note' in parsed_data
        
        elif question_type == 'key_signature':
            return 'key' in parsed_data
        
        return True

    def parse_from_correct_answer(self, question_data: Dict[str, Any], exercise_type: str) -> Dict[str, Any]:
        """
        Parse musical content from the correct answer for exercise types that don't have notes in the question.
        Used for: Note Reading, Ear Training, Musical Form
        """
        if not question_data or 'correct_answer' not in question_data:
            return None
            
        # Resolve the actual text of the correct answer
        correct_key = question_data.get('correct_answer')  # e.g., 'A'
        options = question_data.get('options', {}) or {}
        correct_text = options.get(correct_key, question_data.get('correct_text', ''))
        if not correct_text:
            # Fallback: sometimes the API may already provide text in correct_answer
            correct_text = str(question_data.get('correct_answer', '')).strip()
        
        question_text = question_data.get('question', '')
        
        # Map exercise types to question types
        exercise_type_mapping = {
            "Note Reading": "note_identification",
            "Ear Training": "ear_training", 
            "Musical Form": "musical_form",
            "Harmony": "harmony"
        }
        
        question_type = exercise_type_mapping.get(exercise_type, "note_identification")
        
        if exercise_type == "Note Reading":
            # Extract the note from correct_text (e.g., "G")
            note_token = correct_text.split()[0] if correct_text else "G"
            return {
                'type': 'note_identification',
                'note': note_token.upper(),
                'clef': 'treble',  # Default to treble clef
                'original_question': question_text,
                'confidence': 'high',
                'parsed_from_answer': True
            }
            
        elif exercise_type == "Ear Training":
            text = correct_text.lower()
            # Interval detection
            interval_map = {
                'minor second': 'minor_second',
                'major second': 'major_second',
                'minor third': 'minor_third',
                'major third': 'major_third',
                'perfect fourth': 'perfect_fourth',
                'augmented fourth': 'augmented_fourth',
                'tritone': 'augmented_fourth',
                'diminished fifth': 'diminished_fifth',
                'perfect fifth': 'perfect_fifth',
                'minor sixth': 'minor_sixth',
                'major sixth': 'major_sixth',
                'minor seventh': 'minor_seventh',
                'major seventh': 'major_seventh',
                'octave': 'perfect_octave',
                'perfect octave': 'perfect_octave'
            }
            detected_interval = None
            for label, key in interval_map.items():
                if label in text:
                    detected_interval = key
                    break
            if detected_interval:
                return {
                    'type': 'ear_training',
                    'training_type': 'interval',
                    'interval_type': detected_interval,
                    # Randomize a root to avoid repeated audio; builder will choose default if absent
                    'root': None,
                    'original_question': question_text,
                    'confidence': 'high',
                    'parsed_from_answer': True
                }
            # Scale detection (explicit handling)
            if any(w in text for w in ['harmonic minor','melodic minor','natural minor','major']):
                # extract key like 'B' from phrases like 'B harmonic minor'
                import re
                m = re.search(r'([A-Ga-g][#b]?)\s+(major|harmonic minor|melodic minor|natural minor)', correct_text)
                key = m.group(1).upper() if m else 'C'
                mode_word = (m.group(2).lower() if m else 'major')
                mode = 'major'
                if 'harmonic' in mode_word:
                    mode = 'harmonic_minor'
                elif 'melodic' in mode_word:
                    mode = 'melodic_minor'
                elif 'natural' in mode_word or (mode_word == 'minor'):
                    mode = 'natural_minor'
                return {
                    'type': 'scale',
                    'key': key,
                    'mode': mode,
                    'original_question': question_text,
                    'confidence': 'high',
                    'parsed_from_answer': True
                }
            # Chord quality detection (extract root + quality)
            import re
            m = re.search(r"([A-Ga-g][#b]?)\s*(major|minor|diminished|augmented)", correct_text)
            if m:
                root = m.group(1).upper()
                quality = m.group(2).lower()
                return {
                    'type': 'ear_training',
                    'training_type': 'chord',
                    'root': root,
                    'chord_quality': quality,
                    'original_question': question_text,
                    'confidence': 'high',
                    'parsed_from_answer': True
                }
            # Extended chord families (reverted per request – remove)
            if 'chord' in text or text in ('major','minor','diminished','augmented'):
                quality = 'major' if 'major' in text else 'minor' if 'minor' in text else 'diminished' if 'diminished' in text else 'augmented' if 'augmented' in text else 'major'
                return {
                    'type': 'ear_training',
                    'training_type': 'chord',
                    'chord_quality': quality,
                    'original_question': question_text,
                    'confidence': 'medium',
                    'parsed_from_answer': True
                }
            # If undetected, return None so upstream can use GPT fallback or regenerate
            return None
        
        elif exercise_type == "Harmony":
            # Answers often list chord tones like "Bb-D-F"; parse them into chord notes
            import re
            note_tokens = re.findall(r"[A-Ga-g][#b]?", correct_text)
            if note_tokens:
                chord_notes = [t.upper() for t in note_tokens]
                return {
                    'type': 'ear_training',
                    'training_type': 'chord',
                    'chord_notes': chord_notes,
                    'original_question': question_text,
                    'confidence': 'high',
                    'parsed_from_answer': True
                }
            return None
                
        elif exercise_type == "Musical Form":
            form_type = correct_text.lower()
            if 'binary' in form_type:
                form = 'binary'
            elif 'ternary' in form_type:
                form = 'ternary'
            elif 'rondo' in form_type:
                form = 'rondo'
            else:
                form = 'binary'  # Default
                
            return {
                'type': 'musical_form',
                'form_type': form,
                'original_question': question_text,
                'confidence': 'high',
                'parsed_from_answer': True
            }
            
        return None

# Test the parser
if __name__ == "__main__":
    parser = QuestionParser()
    
    test_questions = [
        "What is the interval between C and E?",
        "What is the iii chord in C major?",
        "What is the C major scale?",
        "What is the time signature 3/4?",
        "What note is on the second line of the treble clef?",
        "What is the key signature of D major?"
    ]
    
    for question in test_questions:
        result = parser.parse(question)
        print(f"\nQuestion: {question}")
        print(f"Parsed: {result}")
        print(f"Valid: {parser.validate_parsed_data(result)}")
