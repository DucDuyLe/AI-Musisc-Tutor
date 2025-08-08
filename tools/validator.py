import abjad
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

class ValidationLevel(Enum):
    """Validation levels for different types of checks"""
    BASIC = "basic"
    MUSICAL = "musical"
    COMPLETE = "complete"

class NotationValidator:
    """
    Comprehensive validator for musical notation.
    Ensures generated notation matches the original question intent.
    """
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.error_messages = []
        self.warning_messages = []
    
    def _load_validation_rules(self) -> Dict[str, Dict]:
        """Load validation rules for different question types"""
        return {
            'interval': {
                'required_elements': ['notes'],
                'min_notes': 2,
                'max_notes': 2,
                'check_interval': True
            },
            'chord': {
                'required_elements': ['chords'],
                'min_chords': 1,
                'max_chords': 1,
                'check_chord_notes': True
            },
            'scale': {
                'required_elements': ['notes'],
                'min_notes': 7,
                'max_notes': 8,
                'check_scale_pattern': True
            },
            'time_signature': {
                'required_elements': ['time_signature'],
                'min_time_signatures': 1,
                'max_time_signatures': 1,
                'check_beat_count': True
            },
            'note_identification': {
                'required_elements': ['notes'],
                'min_notes': 1,
                'max_notes': 1,
                'check_note_name': True
            },
            'key_signature': {
                'required_elements': ['key_signature'],
                'min_key_signatures': 1,
                'max_key_signatures': 1,
                'check_key': True
            }
        }
    
    def validate(self, staff: abjad.Staff, parsed_data: Dict[str, Any], 
                 level: ValidationLevel = ValidationLevel.COMPLETE) -> bool:
        """
        Validate that the generated notation matches the original question.
        
        Args:
            staff: The Abjad staff to validate
            parsed_data: The parsed question data
            level: Validation level (basic, musical, complete)
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        self.error_messages = []
        self.warning_messages = []
        
        try:
            question_type = parsed_data.get('type', 'unknown')
            
            # Basic validation (always performed)
            if not self._basic_validation(staff, parsed_data):
                return False
            
            # Musical validation (if level >= musical)
            if level in [ValidationLevel.MUSICAL, ValidationLevel.COMPLETE]:
                if not self._musical_validation(staff, parsed_data):
                    return False
            
            # Complete validation (if level == complete)
            if level == ValidationLevel.COMPLETE:
                if not self._complete_validation(staff, parsed_data):
                    return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Validation error: {e}")
            return False
    
    def _basic_validation(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Basic validation checks that apply to all notation.
        """
        try:
            if not staff:
                self.error_messages.append("No staff provided")
                return False
            
            # Check if staff has any content
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            if not notes:
                self.error_messages.append("Staff has no musical content")
                return False
            
            # Check for required elements based on question type
            question_type = parsed_data.get('type', 'unknown')
            if question_type in self.validation_rules:
                rules = self.validation_rules[question_type]
                
                for element in rules.get('required_elements', []):
                    if not self._check_required_element(staff, element, rules):
                        return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Basic validation error: {e}")
            return False
    
    def _musical_validation(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Musical validation checks specific to the question type.
        """
        try:
            question_type = parsed_data.get('type', 'unknown')
            
            if question_type == 'interval':
                return self._validate_interval_musical(staff, parsed_data)
            elif question_type == 'chord':
                return self._validate_chord_musical(staff, parsed_data)
            elif question_type == 'scale':
                return self._validate_scale_musical(staff, parsed_data)
            elif question_type == 'time_signature':
                return self._validate_time_signature_musical(staff, parsed_data)
            elif question_type == 'note_identification':
                return self._validate_note_identification_musical(staff, parsed_data)
            elif question_type == 'key_signature':
                return self._validate_key_signature_musical(staff, parsed_data)
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Musical validation error: {e}")
            return False
    
    def _complete_validation(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Complete validation including advanced checks.
        """
        try:
            # Check notation completeness
            if not self._check_completeness(staff, parsed_data):
                return False
            
            # Check musical correctness
            if not self._check_musical_correctness(staff, parsed_data):
                return False
            
            # Check notation quality
            if not self._check_notation_quality(staff, parsed_data):
                return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Complete validation error: {e}")
            return False
    
    def _check_required_element(self, staff: abjad.Staff, element: str, rules: Dict) -> bool:
        """
        Check if staff has required elements.
        """
        try:
            if element == 'notes':
                notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
                min_notes = rules.get('min_notes', 1)
                max_notes = rules.get('max_notes', 10)
                
                if len(notes) < min_notes:
                    self.error_messages.append(f"Not enough notes: {len(notes)} < {min_notes}")
                    return False
                if len(notes) > max_notes:
                    self.error_messages.append(f"Too many notes: {len(notes)} > {max_notes}")
                    return False
            
            elif element == 'chords':
                chords = [comp for comp in staff if isinstance(comp, abjad.Chord)]
                min_chords = rules.get('min_chords', 1)
                max_chords = rules.get('max_chords', 5)
                
                if len(chords) < min_chords:
                    self.error_messages.append(f"Not enough chords: {len(chords)} < {min_chords}")
                    return False
                if len(chords) > max_chords:
                    self.error_messages.append(f"Too many chords: {len(chords)} > {max_chords}")
                    return False
            
            elif element == 'time_signature':
                # Check for time signatures attached to notes/chords
                time_signatures = []
                for comp in staff:
                    if isinstance(comp, (abjad.Note, abjad.Chord)):
                        for indicator in abjad.get.indicators(comp):
                            if isinstance(indicator, abjad.TimeSignature):
                                time_signatures.append(indicator)
                
                min_time_sigs = rules.get('min_time_signatures', 1)
                max_time_sigs = rules.get('max_time_signatures', 1)
                
                if len(time_signatures) < min_time_sigs:
                    self.error_messages.append(f"Missing time signature")
                    return False
                if len(time_signatures) > max_time_sigs:
                    self.error_messages.append(f"Too many time signatures: {len(time_signatures)}")
                    return False
            
            elif element == 'key_signature':
                # Check for key signatures attached to notes/chords
                key_signatures = []
                for comp in staff:
                    if isinstance(comp, (abjad.Note, abjad.Chord)):
                        for indicator in abjad.get.indicators(comp):
                            if isinstance(indicator, abjad.KeySignature):
                                key_signatures.append(indicator)
                
                min_key_sigs = rules.get('min_key_signatures', 1)
                max_key_sigs = rules.get('max_key_signatures', 1)
                
                if len(key_signatures) < min_key_sigs:
                    self.error_messages.append(f"Missing key signature")
                    return False
                if len(key_signatures) > max_key_sigs:
                    self.error_messages.append(f"Too many key signatures: {len(key_signatures)}")
                    return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Error checking required element {element}: {e}")
            return False
    
    def _validate_interval_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate interval notation musically.
        """
        try:
            start_note = parsed_data.get('start_note', 'C')
            end_note = parsed_data.get('end_note', 'E')
            
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            if len(notes) < 2:
                self.error_messages.append("Interval must have at least 2 notes")
                return False
            
            # Check if notes match the expected interval
            note_names = []
            for note in notes:
                if hasattr(note, 'written_pitch'):
                    pitch = note.written_pitch
                    note_names.append(str(pitch).upper())
            
            if len(note_names) >= 2:
                actual_start = note_names[0]
                actual_end = note_names[1]
                
                # Convert to standard format for comparison
                expected_start = self._normalize_note_name(start_note)
                expected_end = self._normalize_note_name(end_note)
                actual_start_norm = self._normalize_note_name(actual_start)
                actual_end_norm = self._normalize_note_name(actual_end)
                
                if actual_start_norm != expected_start or actual_end_norm != expected_end:
                    self.warning_messages.append(
                        f"Interval notes don't match: expected {start_note}-{end_note}, got {actual_start}-{actual_end}"
                    )
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Interval validation error: {e}")
            return False
    
    def _validate_chord_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate chord notation musically.
        """
        try:
            chord_degree = parsed_data.get('chord_degree', 'I')
            key = parsed_data.get('key', 'C')
            
            chords = [comp for comp in staff if isinstance(comp, abjad.Chord)]
            if not chords:
                self.error_messages.append("No chord found in chord notation")
                return False
            
            # Check if chord has the right number of notes (triad = 3 notes)
            chord = chords[0]
            if len(chord.written_pitches) < 3:
                self.warning_messages.append(f"Chord has fewer than 3 notes: {len(chord.written_pitches)}")
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Chord validation error: {e}")
            return False
    
    def _validate_scale_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate scale notation musically.
        """
        try:
            key = parsed_data.get('key', 'C')
            mode = parsed_data.get('mode', 'major')
            
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            if len(notes) < 7:
                self.error_messages.append(f"Scale should have at least 7 notes, got {len(notes)}")
                return False
            
            # Check if notes follow a scale pattern
            note_names = []
            for note in notes:
                if hasattr(note, 'written_pitch'):
                    pitch = note.written_pitch
                    note_names.append(str(pitch).upper())
            
            if len(note_names) >= 7:
                # Basic check: first and last notes should be the same (octave)
                if note_names[0] != note_names[-1]:
                    self.warning_messages.append("Scale doesn't end on the same note as it starts")
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Scale validation error: {e}")
            return False
    
    def _validate_time_signature_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate time signature notation musically.
        """
        try:
            signature = parsed_data.get('signature', '3/4')
            
            # Check for time signatures attached to notes/chords
            time_signatures = []
            for comp in staff:
                if isinstance(comp, (abjad.Note, abjad.Chord)):
                    for indicator in abjad.get.indicators(comp):
                        if isinstance(indicator, abjad.TimeSignature):
                            time_signatures.append(indicator)
            
            if not time_signatures:
                self.error_messages.append("No time signature found")
                return False
            
            # Check if time signature matches expected
            time_sig = time_signatures[0]
            actual_signature = f"{time_sig.pair[0]}/{time_sig.pair[1]}"
            
            if actual_signature != signature:
                self.error_messages.append(f"Time signature mismatch: expected {signature}, got {actual_signature}")
                return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Time signature validation error: {e}")
            return False
    
    def _validate_note_identification_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate note identification notation musically.
        """
        try:
            expected_note = parsed_data.get('note', 'G')
            clef = parsed_data.get('clef', 'treble')
            
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            if not notes:
                self.error_messages.append("No note found in note identification")
                return False
            
            # Check if clef is present
            clefs = [comp for comp in staff if isinstance(comp, abjad.Clef)]
            if not clefs:
                self.warning_messages.append("No clef specified")
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Note identification validation error: {e}")
            return False
    
    def _validate_key_signature_musical(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate key signature notation musically.
        """
        try:
            key = parsed_data.get('key', 'C')
            mode = parsed_data.get('mode', 'major')
            
            # Check for key signatures attached to notes/chords
            key_signatures = []
            for comp in staff:
                if isinstance(comp, (abjad.Note, abjad.Chord)):
                    for indicator in abjad.get.indicators(comp):
                        if isinstance(indicator, abjad.KeySignature):
                            key_signatures.append(indicator)
            
            if not key_signatures:
                self.error_messages.append("No key signature found")
                return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Key signature validation error: {e}")
            return False
    
    def _check_completeness(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Check if the notation is complete for the question.
        """
        try:
            question_type = parsed_data.get('type', 'unknown')
            original_question = parsed_data.get('original_question', '')
            
            # Check if all elements mentioned in the question are present
            if 'interval' in original_question.lower():
                notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
                if len(notes) < 2:
                    self.error_messages.append("Interval question requires at least 2 notes")
                    return False
            
            elif 'chord' in original_question.lower():
                chords = [comp for comp in staff if isinstance(comp, abjad.Chord)]
                if not chords:
                    self.error_messages.append("Chord question requires at least one chord")
                    return False
            
            elif 'scale' in original_question.lower():
                notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
                if len(notes) < 7:
                    self.error_messages.append("Scale question requires at least 7 notes")
                    return False
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Completeness check error: {e}")
            return False
    
    def _check_musical_correctness(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Check if the notation is musically correct.
        """
        try:
            # Check for basic musical errors
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            
            # Check for consecutive rests (usually indicates error)
            rest_count = 0
            for note in notes:
                if isinstance(note, abjad.Rest):
                    rest_count += 1
                else:
                    rest_count = 0
                
                if rest_count > 2:
                    self.warning_messages.append("Multiple consecutive rests detected")
            
            # Check for reasonable note durations
            for note in notes:
                if hasattr(note, 'written_duration'):
                    duration = note.written_duration
                    if duration > abjad.Duration(4, 1):  # Longer than whole note
                        self.warning_messages.append("Very long note duration detected")
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Musical correctness check error: {e}")
            return False
    
    def _check_notation_quality(self, staff: abjad.Staff, parsed_data: Dict[str, Any]) -> bool:
        """
        Check the overall quality of the notation.
        """
        try:
            # Check if notation is too simple (just one note might indicate error)
            notes = [comp for comp in staff if isinstance(comp, (abjad.Note, abjad.Chord, abjad.Rest))]
            if len(notes) == 1 and not isinstance(notes[0], abjad.Rest):
                self.warning_messages.append("Very simple notation - might be incomplete")
            
            # Check if notation has reasonable structure
            if len(notes) > 20:
                self.warning_messages.append("Very long notation - might be excessive")
            
            return True
            
        except Exception as e:
            self.error_messages.append(f"Notation quality check error: {e}")
            return False
    
    def _normalize_note_name(self, note: str) -> str:
        """
        Normalize note name for comparison.
        """
        note = note.upper().strip()
        
        # Handle accidentals
        if '#' in note:
            note = note.replace('#', 'SHARP')
        elif 'B' in note and len(note) > 1:
            note = note.replace('B', 'FLAT')
        
        return note
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get a detailed validation report.
        """
        return {
            'passed': len(self.error_messages) == 0,
            'errors': self.error_messages,
            'warnings': self.warning_messages,
            'error_count': len(self.error_messages),
            'warning_count': len(self.warning_messages)
        }
    
    def clear_messages(self):
        """Clear all error and warning messages."""
        self.error_messages = []
        self.warning_messages = []

# Test the validator
if __name__ == "__main__":
    validator = NotationValidator()
    
    # Test data
    test_data = {
        'type': 'interval',
        'start_note': 'C',
        'end_note': 'E',
        'original_question': 'What is the interval between C and E?'
    }
    
    # Create a test staff (this would normally come from AbjadBuilder)
    import abjad
    staff = abjad.Staff()
    staff.append(abjad.Note('c4'))
    staff.append(abjad.Note('e4'))
    
    # Validate
    result = validator.validate(staff, test_data)
    report = validator.get_validation_report()
    
    print(f"Validation result: {result}")
    print(f"Validation report: {report}")
