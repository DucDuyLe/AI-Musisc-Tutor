import abjad
from typing import Dict, List, Optional, Any, Union
import tempfile
import os

class AbjadBuilder:
    """
    Converts structured musical data into valid Abjad Python code.
    Handles different musical concepts with error handling and fallback mechanisms.
    """
    
    def __init__(self):
        self.templates = self._load_templates()
        self.error_count = 0
        self.max_retries = 3
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load Abjad code templates for different musical concepts"""
        return {
            'scale': {
                'template': self._build_scale_template,
                'validation': self._validate_scale
            },
            'chord': {
                'template': self._build_chord_template,
                'validation': self._validate_chord
            },
            'interval': {
                'template': self._build_interval_template,
                'validation': self._validate_interval
            },
            'time_signature': {
                'template': self._build_time_signature_template,
                'validation': self._validate_time_signature
            },
            'note_identification': {
                'template': self._build_note_identification_template,
                'validation': self._validate_note_identification
            },
            'key_signature': {
                'template': self._build_key_signature_template,
                'validation': self._validate_key_signature
            },
            'rhythm': {
                'template': self._build_rhythm_template,
                'validation': self._validate_rhythm
            },
            'harmony': {
                'template': self._build_harmony_template,
                'validation': self._validate_harmony
            },
            'ear_training': {
                'template': self._build_ear_training_template,
                'validation': self._validate_ear_training
            },
            'musical_form': {
                'template': self._build_musical_form_template,
                'validation': self._validate_musical_form
            }
        }
    
    def build_notation(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """
        Build Abjad notation from parsed question data.
        Returns an Abjad Staff object or None if building fails.
        """
        try:
            question_type = parsed_data.get('type', 'unknown')
            
            if question_type not in self.templates:
                print(f"Unknown question type: {question_type}")
                return self._fallback_build(parsed_data)
            
            # Get template and validation function
            template_func = self.templates[question_type]['template']
            validation_func = self.templates[question_type]['validation']
            
            # Build the notation
            staff = template_func(parsed_data)
            
            # Validate the result
            if staff and validation_func(staff, parsed_data):
                return staff
            else:
                print(f"Validation failed for {question_type}")
                return self._fallback_build(parsed_data)
                
        except Exception as e:
            print(f"Error building notation: {e}")
            return self._fallback_build(parsed_data)
    
    def _build_scale_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build scale notation"""
        try:
            key = parsed_data.get('key', 'C')
            mode = parsed_data.get('mode', 'major')
            
            # Create staff
            staff = abjad.Staff()
            
            # Get scale data from theory lookup
            from tools.theory_lookup import TheoryLookup
            lookup = TheoryLookup()
            scale_data = lookup.get_scale(key, mode)
            
            if scale_data:
                # Use the notes from theory lookup
                scale_notes = scale_data['abjad_notes']
            else:
                # Fallback to manual generation
                scale_notes = self._generate_scale_notes(key, mode)
            
            # Convert to simplified Abjad format (base notes only)
            simplified_notes = []
            for note in scale_notes:
                # Extract base note (remove accidentals)
                if 'is' in note:  # sharp
                    base_note = note.replace('is', '')
                elif 'es' in note:  # flat
                    base_note = note.replace('es', '')
                else:
                    base_note = note
                simplified_notes.append(base_note)
            
            # Add key signature to first note if needed
            try:
                if mode == 'major':
                    key_signature = abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("major"))
                else:
                    key_signature = abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("minor"))
                
                # Create first note and attach key signature
                first_note = abjad.Note(simplified_notes[0], (1, 4))
                abjad.attach(key_signature, first_note)
                staff.append(first_note)
                
                # Add remaining notes
                for note_name in simplified_notes[1:]:
                    note = abjad.Note(note_name, (1, 4))  # Quarter notes
                    staff.append(note)
                    
            except Exception as e:
                print(f"Error creating key signature: {type(e).__name__}: {e}")
                # Continue without key signature - add all notes normally
                for note_name in simplified_notes:
                    note = abjad.Note(note_name, (1, 4))  # Quarter notes
                    staff.append(note)
            
            return staff
            
        except Exception as e:
            print(f"Error building scale template: {e}")
            return None
    
    def _build_chord_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build chord notation"""
        try:
            chord_degree = parsed_data.get('chord_degree', 'I')
            key = parsed_data.get('key', 'C')
            
            # Create staff
            staff = abjad.Staff()
            
            # Build chord based on degree (example: I chord in C major = C-E-G)
            if chord_degree.lower() == 'i' or chord_degree.lower() == 'i':
                chord_notes = ['c', 'e', 'g']
            elif chord_degree.lower() == 'ii':
                chord_notes = ['d', 'f', 'a']
            elif chord_degree.lower() == 'iii':
                chord_notes = ['e', 'g', 'b']
            elif chord_degree.lower() == 'iv':
                chord_notes = ['f', 'a', 'c']
            elif chord_degree.lower() == 'v':
                chord_notes = ['g', 'b', 'd']
            elif chord_degree.lower() == 'vi':
                chord_notes = ['a', 'c', 'e']
            elif chord_degree.lower() == 'vii':
                chord_notes = ['b', 'd', 'f']
            else:
                # Default to C major triad
                chord_notes = ['c', 'e', 'g']
            
            # Create chord
            chord = abjad.Chord(chord_notes, (1, 4))
            
            # Add key signature to chord if needed
            try:
                key_signature = abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("major"))
                abjad.attach(key_signature, chord)
            except Exception as e:
                print(f"Error creating key signature: {type(e).__name__}: {e}")
                # Continue without key signature
            
            staff.append(chord)
            
            return staff
            
        except Exception as e:
            print(f"Error building chord template: {e}")
            return None
    
    def _build_interval_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build interval notation"""
        try:
            start_note = parsed_data.get('start_note', 'C')
            end_note = parsed_data.get('end_note', 'E')
            
            # Create staff
            staff = abjad.Staff()
            
            # Convert note names to Abjad format
            start_abjad = self._note_to_abjad(start_note)
            end_abjad = self._note_to_abjad(end_note)
            
            # Add notes with proper octaves (middle C register)
            staff.append(abjad.Note(start_abjad + "'", (1, 4)))  # Add octave mark
            staff.append(abjad.Note(end_abjad + "'", (1, 4)))    # Add octave mark
            
            return staff
            
        except Exception as e:
            print(f"Error building interval template: {e}")
            return None
    
    def _build_time_signature_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build time signature notation"""
        try:
            signature = parsed_data.get('signature', '3/4')
            
            # Create staff
            staff = abjad.Staff()
            
            # Add example notes based on time signature with proper octaves
            if signature == '2/4':
                notes = [abjad.Note("c'4"), abjad.Note("c'4")]  # Middle C octave
            elif signature == '3/4':
                notes = [abjad.Note("c'4"), abjad.Note("e'4"), abjad.Note("g'4")]  # C major triad
            elif signature == '4/4':
                notes = [abjad.Note("c'4"), abjad.Note("d'4"), abjad.Note("e'4"), abjad.Note("f'4")]  # C major scale notes
            elif signature == '6/8':
                notes = [abjad.Note("c'8"), abjad.Note("d'8"), abjad.Note("e'8"), abjad.Note("f'8"), abjad.Note("g'8"), abjad.Note("a'8")]
            else:
                # Default to 3/4
                notes = [abjad.Note("c'4"), abjad.Note("e'4"), abjad.Note("g'4")]
            
            # Add time signature to first note
            try:
                if '/' in signature:
                    numerator, denominator = signature.split('/')
                    time_signature = abjad.TimeSignature((int(numerator), int(denominator)))
                else:
                    time_signature = abjad.TimeSignature((3, 4))  # Default
                
                abjad.attach(time_signature, notes[0])
            except Exception as e:
                print(f"Error creating time signature: {type(e).__name__}: {e}")
                # Continue without time signature
            
            # Add all notes to staff
            for note in notes:
                staff.append(note)
            
            # Add final barline
            try:
                final_barline = abjad.BarLine('|.')
                abjad.attach(final_barline, staff[-1])
            except Exception as e:
                print(f"Error adding final barline: {type(e).__name__}: {e}")
                # Continue without barline
            
            return staff
            
        except Exception as e:
            print(f"Error building time signature template: {e}")
            return None
    
    def _build_note_identification_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build note identification notation"""
        try:
            note = parsed_data.get('note', 'G')
            clef = parsed_data.get('clef', 'treble')
            
            # Create staff
            staff = abjad.Staff()
            
            # Add clef
            if clef.lower() == 'treble':
                staff.append(abjad.Clef('treble'))
            else:
                staff.append(abjad.Clef('bass'))
            
            # Add the note
            abjad_note = self._note_to_abjad(note)
            staff.append(abjad.Note(abjad_note, (1, 4)))
            
            return staff
            
        except Exception as e:
            print(f"Error building note identification template: {e}")
            return None
    
    def _build_key_signature_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build key signature notation"""
        try:
            key = parsed_data.get('key', 'C')
            mode = parsed_data.get('mode', 'major')
            
            # Create staff
            staff = abjad.Staff()
            
            # Add key signature
            if mode == 'major':
                staff.append(abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("major")))
            else:
                staff.append(abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("minor")))
            
            # Add a rest to show the key signature
            staff.append(abjad.Rest((1, 4)))
            
            return staff
            
        except Exception as e:
            print(f"Error building key signature template: {e}")
            return None
    
    def _fallback_build(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """
        Fallback builder for when primary templates fail.
        Creates a simple staff with basic notation.
        """
        try:
            staff = abjad.Staff()
            
            # Add a simple note as fallback
            staff.append(abjad.Note('c4'))
            
            return staff
            
        except Exception as e:
            print(f"Fallback build failed: {e}")
            return None
    
    def _generate_scale_notes(self, key: str, mode: str) -> List[str]:
        """Generate scale notes based on key and mode"""
        key = key.upper()
        
        # Define scale patterns
        major_pattern = [0, 2, 4, 5, 7, 9, 11, 12]  # Whole, Whole, Half, Whole, Whole, Whole, Half
        natural_minor_pattern = [0, 2, 3, 5, 7, 8, 10, 12]  # Whole, Half, Whole, Whole, Half, Whole, Whole
        harmonic_minor_pattern = [0, 2, 3, 5, 7, 8, 11, 12]  # Natural minor with raised 7th
        
        # Define note names
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Find the starting note index
        start_index = note_names.index(key) if key in note_names else 0
        
        # Choose pattern based on mode
        if mode.lower() == 'harmonic_minor':
            pattern = harmonic_minor_pattern
        elif mode.lower() == 'natural_minor':
            pattern = natural_minor_pattern
        else:  # major
            pattern = major_pattern
        
        # Generate scale notes
        scale_notes = []
        for step in pattern:
            note_index = (start_index + step) % 12
            note_name = note_names[note_index]
            
            # Convert to Abjad format (lowercase)
            abjad_note = note_name.lower()
            
            # Handle accidentals for Abjad - use simplified base notes only
            if '#' in abjad_note:
                # Convert sharp to base note (e.g., 'c#' -> 'c')
                abjad_note = abjad_note.replace('#', '')
            elif 'b' in abjad_note and len(abjad_note) > 1:
                # Convert flat to base note (e.g., 'eb' -> 'e')
                abjad_note = abjad_note.replace('b', '')
            
            scale_notes.append(abjad_note)
        
        return scale_notes

    def _note_to_abjad(self, note: str) -> str:
        """
        Convert note name to Abjad format.
        For now, use basic notes and handle accidentals through key signatures.
        """
        note = note.upper()
        
        # Extract the base note (remove accidentals)
        if '#' in note:
            base_note = note.replace('#', '')
        elif 'B' in note and len(note) > 1 and note != 'B':
            base_note = note.replace('B', '')
        else:
            base_note = note
        
        # Convert to lowercase for Abjad
        return base_note.lower()
    
    def _validate_scale(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate scale notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes
            notes = [comp for comp in staff if isinstance(comp, abjad.Note)]
            return len(notes) > 0
            
        except Exception:
            return False
    
    def _validate_chord(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate chord notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has a chord
            chords = [comp for comp in staff if isinstance(comp, abjad.Chord)]
            return len(chords) > 0
            
        except Exception:
            return False
    
    def _validate_interval(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate interval notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has at least 2 notes
            notes = [comp for comp in staff if isinstance(comp, abjad.Note)]
            return len(notes) >= 2
            
        except Exception:
            return False
    
    def _validate_time_signature(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate time signature notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes (time signature is attached to first note)
            notes = [comp for comp in staff if isinstance(comp, abjad.Note)]
            return len(notes) > 0
            
        except Exception:
            return False
    
    def _validate_note_identification(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate note identification notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has a note
            notes = [comp for comp in staff if isinstance(comp, abjad.Note)]
            return len(notes) > 0
            
        except Exception:
            return False
    
    def _validate_key_signature(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate key signature notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes (key signature is attached to first note/chord)
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord))]
            return len(notes) > 0
            
        except Exception:
            return False
    
    def export_to_lilypond(self, staff: abjad.Staff) -> str:
        """
        Export Abjad staff to LilyPond code string.
        """
        try:
            if not staff:
                return ""
            
            return abjad.lilypond(staff)
            
        except Exception as e:
            print(f"Error exporting to LilyPond: {e}")
            return ""
    
    def get_staff_info(self, staff: abjad.Staff) -> Dict[str, Any]:
        """
        Get information about the built staff.
        """
        try:
            if not staff:
                return {'error': 'No staff provided'}
            
            # Count notes and chords manually
            note_count = 0
            chord_count = 0
            for component in staff:
                if isinstance(component, abjad.Note):
                    note_count += 1
                elif isinstance(component, abjad.Chord):
                    chord_count += 1
            
            info = {
                'note_count': note_count,
                'chord_count': chord_count,
                'duration': str(abjad.get.duration(staff)),
                'lilypond_code': self.export_to_lilypond(staff)
            }
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _build_rhythm_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build rhythm notation"""
        try:
            rhythm_type = parsed_data.get('rhythm_type', 'quarter_notes')
            time_signature = parsed_data.get('time_signature', '4/4')
            
            # Create staff
            staff = abjad.Staff()
            
            # Get rhythm data from theory lookup
            from tools.theory_lookup import TheoryLookup
            lookup = TheoryLookup()
            
            # Get rhythm pattern based on type
            if rhythm_type == 'quarter_notes':
                pattern = ['c4', 'c4', 'c4', 'c4']
            elif rhythm_type == 'half_notes':
                pattern = ['c2', 'c2']
            elif rhythm_type == 'eighth_notes':
                pattern = ['c8', 'c8', 'c8', 'c8', 'c8', 'c8', 'c8', 'c8']
            elif rhythm_type == 'syncopation':
                pattern = ['c4', 'r4', 'c4', 'c4']
            else:
                pattern = ['c4', 'c4', 'c4', 'c4']  # Default
            
            # Add time signature to first note
            try:
                if '/' in time_signature:
                    numerator, denominator = time_signature.split('/')
                    time_sig = abjad.TimeSignature((int(numerator), int(denominator)))
                    first_note = abjad.Note(pattern[0])
                    abjad.attach(time_sig, first_note)
                    staff.append(first_note)
                    
                    # Add remaining notes
                    for note_str in pattern[1:]:
                        if note_str.startswith('r'):
                            # Rest
                            rest = abjad.Rest(note_str[1:])
                            staff.append(rest)
                        else:
                            # Note
                            note = abjad.Note(note_str)
                            staff.append(note)
                else:
                    # Default to 4/4
                    for note_str in pattern:
                        if note_str.startswith('r'):
                            rest = abjad.Rest(note_str[1:])
                            staff.append(rest)
                        else:
                            note = abjad.Note(note_str)
                            staff.append(note)
                            
            except Exception as e:
                print(f"Error creating rhythm: {e}")
                # Fallback to simple notes
                for note_str in pattern:
                    if note_str.startswith('r'):
                        rest = abjad.Rest(note_str[1:])
                        staff.append(rest)
                    else:
                        note = abjad.Note(note_str)
                        staff.append(note)
            
            return staff
            
        except Exception as e:
            print(f"Error building rhythm template: {e}")
            return None
    
    def _build_harmony_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build harmony notation (chord progressions)"""
        try:
            progression_type = parsed_data.get('progression_type', 'I_IV_V')
            key = parsed_data.get('key', 'C')
            
            # Create staff
            staff = abjad.Staff()
            
            # Get progression data
            from tools.theory_lookup import TheoryLookup
            lookup = TheoryLookup()
            
            # Define chord progressions
            if progression_type == 'I_IV_V':
                chords = [['c', 'e', 'g'], ['f', 'a', 'c'], ['g', 'b', 'd']]
            elif progression_type == 'ii_V_I':
                chords = [['d', 'f', 'a'], ['g', 'b', 'd'], ['c', 'e', 'g']]
            elif progression_type == 'I_vi_IV_V':
                chords = [['c', 'e', 'g'], ['a', 'c', 'e'], ['f', 'a', 'c'], ['g', 'b', 'd']]
            else:
                # Default to I-IV-V
                chords = [['c', 'e', 'g'], ['f', 'a', 'c'], ['g', 'b', 'd']]
            
            # Add key signature to first chord
            try:
                key_signature = abjad.KeySignature(abjad.NamedPitchClass(key.lower()), abjad.Mode("major"))
                first_chord = abjad.Chord(chords[0], (1, 4))
                abjad.attach(key_signature, first_chord)
                staff.append(first_chord)
                
                # Add remaining chords
                for chord_notes in chords[1:]:
                    chord = abjad.Chord(chord_notes, (1, 4))
                    staff.append(chord)
                    
            except Exception as e:
                print(f"Error creating harmony: {e}")
                # Fallback without key signature
                for chord_notes in chords:
                    chord = abjad.Chord(chord_notes, (1, 4))
                    staff.append(chord)
            
            return staff
            
        except Exception as e:
            print(f"Error building harmony template: {e}")
            return None
    
    def _build_ear_training_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build ear training notation"""
        try:
            training_type = parsed_data.get('training_type', 'interval')
            interval_type = parsed_data.get('interval_type', 'major_third')
            root = parsed_data.get('root')
            
            # Create staff
            staff = abjad.Staff()
            
            if training_type == 'interval':
                # Create interval for ear training with optional random root
                import random
                random.seed()
                roots = ['c', 'd', 'e', 'f', 'g', 'a', 'b']
                base = (root.lower() if isinstance(root, str) else random.choice(roots))
                # map interval to semitone steps
                steps = {
                    'minor_second': 1,
                    'major_second': 2,
                    'minor_third': 3,
                    'major_third': 4,
                    'perfect_fourth': 5,
                    'augmented_fourth': 6,
                    'diminished_fifth': 6,
                    'perfect_fifth': 7,
                    'minor_sixth': 8,
                    'major_sixth': 9,
                    'minor_seventh': 10,
                    'major_seventh': 11,
                    'perfect_octave': 12,
                    'octave': 12
                }
                semis = steps.get(interval_type, 4)
                # simple pitch map for semitone transposition within one octave
                pitch_order = ['c', 'cis', 'd', 'dis', 'e', 'f', 'fis', 'g', 'gis', 'a', 'ais', 'b']
                idx = pitch_order.index(base) if base in pitch_order else pitch_order.index(base[0])
                idx2 = (idx + semis) % 12
                n1 = base + "4"
                n2 = pitch_order[idx2] + "4"
                staff.append(abjad.Note(n1))
                staff.append(abjad.Note(n2))
                    
            elif training_type == 'chord':
                # Create chord for ear training
                chord_quality = parsed_data.get('chord_quality', 'major')
                
                if chord_quality == 'major':
                    chord_notes = ['c', 'e', 'g']
                elif chord_quality == 'minor':
                    chord_notes = ['c', 'es', 'g']  # es = e flat
                elif chord_quality == 'diminished':
                    chord_notes = ['c', 'es', 'ges']  # ges = g flat
                elif chord_quality == 'dominant7':
                    chord_notes = ['c', 'e', 'g', 'bes']
                elif chord_quality == 'major7':
                    chord_notes = ['c', 'e', 'g', 'b']
                elif chord_quality == 'minor7':
                    chord_notes = ['c', 'es', 'g', 'bes']
                elif chord_quality == 'half_diminished7':
                    chord_notes = ['c', 'es', 'ges', 'bes']
                elif chord_quality == 'diminished7':
                    chord_notes = ['c', 'es', 'ges', 'a']
                elif chord_quality == 'neapolitan6':
                    # Neapolitan 6th in C: Db in first inversion -> F-Ab-Db
                    chord_notes = ['f', 'as', 'des']
                elif chord_quality == 'augmented6':
                    # Italian augmented 6th in C as example: Ab-C-F#
                    chord_notes = ['as', 'c', 'fis']
                else:
                    chord_notes = ['c', 'e', 'g']  # Default to major
                
                chord = abjad.Chord(chord_notes, (1, 4))
                staff.append(chord)
            elif training_type == 'scale':
                # Build scale based on key & mode
                key = parsed_data.get('key', 'C')
                mode = parsed_data.get('mode', 'major')
                return self._build_scale_template({'key': key, 'mode': mode})
            
            return staff
            
        except Exception as e:
            print(f"Error building ear training template: {e}")
            return None
    
    def _build_musical_form_template(self, parsed_data: Dict[str, Any]) -> Optional[abjad.Staff]:
        """Build musical form notation"""
        try:
            form_type = parsed_data.get('form_type', 'binary')
            
            # Create staff
            staff = abjad.Staff()
            
            if form_type == 'binary':
                # A section (4 measures)
                for i in range(4):
                    note = abjad.Note('c4')
                    staff.append(note)
                # B section (4 measures) - different note
                for i in range(4):
                    note = abjad.Note('e4')
                    staff.append(note)
                    
            elif form_type == 'ternary':
                # A section (2 measures)
                for i in range(2):
                    note = abjad.Note('c4')
                    staff.append(note)
                # B section (2 measures)
                for i in range(2):
                    note = abjad.Note('e4')
                    staff.append(note)
                # A section again (2 measures)
                for i in range(2):
                    note = abjad.Note('c4')
                    staff.append(note)
                    
            elif form_type == 'rondo':
                # A section (2 measures)
                for i in range(2):
                    note = abjad.Note('c4')
                    staff.append(note)
                # B section (1 measure)
                for i in range(1):
                    note = abjad.Note('e4')
                    staff.append(note)
                # A section again (1 measure)
                for i in range(1):
                    note = abjad.Note('c4')
                    staff.append(note)
                # C section (1 measure)
                for i in range(1):
                    note = abjad.Note('g4')
                    staff.append(note)
                # A section final (1 measure)
                for i in range(1):
                    note = abjad.Note('c4')
                    staff.append(note)
            
            return staff
            
        except Exception as e:
            print(f"Error building musical form template: {e}")
            return None
    
    def _validate_rhythm(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate rhythm notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes or rests
            components = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Rest))]
            return len(components) > 0
            
        except Exception:
            return False
    
    def _validate_harmony(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate harmony notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has chords
            chords = [comp for comp in staff if isinstance(comp, abjad.Chord)]
            return len(chords) > 0
            
        except Exception:
            return False
    
    def _validate_ear_training(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate ear training notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes or chords
            components = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord))]
            return len(components) > 0
            
        except Exception:
            return False
    
    def _validate_musical_form(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """Validate musical form notation"""
        try:
            if not staff:
                return False
            
            # Check if staff has notes
            notes = [comp for comp in staff if isinstance(comp, abjad.Note)]
            return len(notes) > 0
            
        except Exception:
            return False

# Test the Abjad builder
if __name__ == "__main__":
    builder = AbjadBuilder()
    
    # Test data
    test_data = {
        'type': 'interval',
        'start_note': 'C',
        'end_note': 'E',
        'original_question': 'What is the interval between C and E?'
    }
    
    # Build notation
    staff = builder.build_notation(test_data)
    
    if staff:
        print("✅ Successfully built notation")
        info = builder.get_staff_info(staff)
        print(f"Staff info: {info}")
    else:
        print("❌ Failed to build notation")
