import hashlib
import tempfile
import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import uuid4

# Import our core modules
from agents.question_parser import QuestionParser
from tools.theory_lookup import TheoryLookup
from tools.abjad_builder import AbjadBuilder
from tools.validator import NotationValidator, ValidationLevel
from tools.image_renderer import ImageRenderer
from tools.audio_renderer import AudioRenderer

class MusicTheoryEngine:
    """
    Main interface that orchestrates all four modules into a unified system.
    Provides caching, error handling, and fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize the music theory engine with all components."""
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.parser = QuestionParser()
        self.lookup = TheoryLookup()
        self.builder = AbjadBuilder()
        self.validator = NotationValidator()
        self.renderer = ImageRenderer()
        self.audio_renderer = AudioRenderer()
        
        # Caching system
        self.cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
        # Error tracking
        self.error_log = []
        self.performance_log = []
    
    def generate_notation(self, question: str, validation_level: ValidationLevel = ValidationLevel.COMPLETE, instrument: str = "Music Theory", exercise_type: str = None, question_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate musical notation from a question using the complete pipeline.
        
        Args:
            question: The music theory question
            validation_level: Level of validation to perform
            instrument: The selected instrument for audio generation
            exercise_type: The type of exercise (for special parsing)
            question_data: Full question data including correct answer (for special parsing)
        
        Returns:
            Dictionary containing the result with notation, metadata, and validation info
        """
        trace_id = str(uuid4())[:8]
        start_time = datetime.now()
        
        try:
            # Check cache first (include instrument, exercise type, and correct option in cache key)
            cache_key = self._generate_cache_key(question, validation_level, instrument, exercise_type, question_data)
            if cache_key in self.cache:
                self.cache_stats['hits'] += 1
                self.cache_stats['total_requests'] += 1
                cached_result = self.cache[cache_key]
                cached_result['cached'] = True
                return cached_result
            
            self.cache_stats['misses'] += 1
            self.cache_stats['total_requests'] += 1
            
            # Step 1: Parse the question (with special handling for certain exercise types)
            parsed_data = self._parse_question(question, exercise_type, question_data)
            if not parsed_data:
                self.logger.error(f"[TRACE {trace_id}] Failed to parse question")
                return self._create_error_result("Failed to parse question", question)
            
            # Step 2: Lookup musical data
            musical_data = self._lookup_musical_data(parsed_data)
            if not musical_data:
                self.logger.error(f"[TRACE {trace_id}] Failed to lookup musical data")
                return self._create_error_result("Failed to lookup musical data", question)
            
            # Step 3: Build notation
            notation_result = self._build_notation(parsed_data, musical_data)
            if not notation_result:
                self.logger.error(f"[TRACE {trace_id}] Failed to build notation")
                return self._create_error_result("Failed to build notation", question)
            
            # Step 4: Validate notation
            validation_result = self._validate_notation(notation_result['staff'], parsed_data, validation_level)
            
            # Step 5: Export to LilyPond
            lilypond_code = self._export_to_lilypond(notation_result['staff'])
            
            # Step 6: Generate image
            image_result = self._generate_image(notation_result['staff'])
            
            # Step 7: Generate audio with instrument-specific settings
            audio_result = self._generate_audio(notation_result['staff'], instrument)
            
            # Create result
            result = {
                'success': True,
                'question': question,
                'parsed_data': parsed_data,
                'musical_data': musical_data,
                'notation': notation_result,
                'validation': validation_result,
                'lilypond_code': lilypond_code,
                'image': image_result,
                'audio': audio_result,
                'instrument': instrument,  # Store the instrument used
                'cached': False,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            error_msg = f"Error in generate_notation: {str(e)}"
            self._log_error(error_msg, question)
            return self._create_error_result(error_msg, question)
    
    def _generate_cache_key(self, question: str, validation_level: ValidationLevel, instrument: str, exercise_type: Optional[str] = None, question_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key that uniquely identifies the rendered content for this prompt.
        Includes instrument, exercise type, and the correct option text when available to avoid
        reusing cached audio/notation across identical ear-training prompts."""
        correct_token = ""
        if question_data:
            try:
                key = question_data.get('correct_answer')
                if key and 'options' in question_data:
                    correct_token = str(question_data['options'].get(key, ''))
            except Exception:
                correct_token = ""
        key_string = f"{question}_{validation_level.value}_{instrument}_{exercise_type or ''}_{correct_token}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _parse_question(self, question: str, exercise_type: str = None, question_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Parse the question using the QuestionParser."""
        try:
            # Special handling for exercise types that may lack explicit notes in the question
            special_exercise_types = ["Note Reading", "Musical Form", "Ear Training"]
            
            if exercise_type in special_exercise_types and question_data:
                parsed = self.parser.parse_from_correct_answer(question_data, exercise_type)
                if parsed:
                    return parsed
            
            parsed = self.parser.parse(question, debug=True)
            
            if not parsed:
                # Try GPT fallback explicitly
                try:
                    parsed = self.parser._gpt_parse(question)
                except Exception:
                    parsed = None
                if not parsed:
                    self._log_error("Question parsing returned None (regex + GPT)", question)
                    return None
            
            if not self.parser.validate_parsed_data(parsed):
                self._log_error("Parsed data validation failed", question)
                return None
            
            return parsed
            
        except Exception as e:
            self._log_error(f"Error in question parsing: {str(e)}", question)
            return None
    
    def _lookup_musical_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lookup musical data using the TheoryLookup."""
        try:
            question_type = parsed_data.get('type', 'unknown')
            
            if question_type == 'interval':
                start_note = parsed_data.get('start_note')
                end_note = parsed_data.get('end_note')
                if not start_note or not end_note:
                    self._log_error("Interval parsing did not provide start/end notes", parsed_data.get('original_question', ''))
                    return None
                result = self.lookup.get_interval(start_note, end_note)
                if result:
                    return result
                else:
                    self._log_error(f"Interval lookup returned None for {start_note} to {end_note}", parsed_data.get('original_question', ''))
                    return None
            
            elif question_type == 'chord':
                degree = parsed_data.get('chord_degree', 'I')
                key = parsed_data.get('key', 'C')
                mode = parsed_data.get('mode', 'major')
                return self.lookup.get_chord(degree, key, mode)
            
            elif question_type == 'scale':
                key = parsed_data.get('key', 'C')
                mode = parsed_data.get('mode', 'major')
                return self.lookup.get_scale(key, mode)
            
            elif question_type == 'time_signature':
                signature = parsed_data.get('signature', '3/4')
                return self.lookup.get_time_signature(signature)

            elif question_type == 'rhythm':
                # Treat rhythm questions as time-signature focused unless more detail is present
                signature = parsed_data.get('signature')
                if not signature:
                    self._log_error("Rhythm parsing did not provide a time signature", parsed_data.get('original_question', ''))
                    return None
                return self.lookup.get_time_signature(signature)
            
            elif question_type == 'note_identification':
                note = parsed_data.get('note', 'G')
                clef = parsed_data.get('clef', 'treble')
                return {
                    'note': note,
                    'clef': clef,
                    'abjad_note': self.lookup._note_to_abjad(note)
                }
            
            elif question_type == 'ear_training':
                # Build musical content from the abstract ear-training label
                training_type = parsed_data.get('training_type', 'interval')
                if training_type == 'interval':
                    interval_key = parsed_data.get('interval_type', 'major_third')
                    # Require explicit mapping; do not default silently
                    if not interval_key:
                        self._log_error("Ear training: interval_type missing", parsed_data.get('original_question', ''))
                        return None
                    # Choose a root (varied) only if interval class provided
                    import random, time
                    random.seed(time.time())
                    roots = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
                    start_note = parsed_data.get('start_note') or random.choice(roots)
                    # Map interval name to semitone distance via lookup table
                    interval_info = self.lookup.intervals.get(interval_key)
                    if not interval_info:
                        # fallback to major third
                        interval_info = self.lookup.intervals.get('major_third', {'semitones': 4})
                    semitones = interval_info.get('semitones', 4)
                    end_note = parsed_data.get('end_note') or self.lookup._add_semitones(start_note, semitones)
                    return {
                        'start_note': start_note,
                        'end_note': end_note,
                        'interval_name': interval_key,
                        'clef': 'treble'
                    }
                elif training_type == 'chord':
                    quality = parsed_data.get('chord_quality')
                    if not quality and not parsed_data.get('chord_notes'):
                        self._log_error("Ear training: chord_quality or chord_notes missing", parsed_data.get('original_question', ''))
                        return None
                    import random, time
                    random.seed(time.time())
                    roots = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
                    root = parsed_data.get('root') or random.choice(roots)
                    # If chord_notes provided directly, use them
                    if parsed_data.get('chord_notes'):
                        notes = parsed_data['chord_notes']
                    else:
                        chord_key = f"{root}_{quality}"
                        triads = self.lookup.chords.get('triads', {})
                        chord = triads.get(chord_key)
                        if chord:
                            notes = chord.get('notes', [])
                        else:
                            # Construct simple triad by intervals
                            notes = [root]
                            third = self.lookup._add_semitones(root, 4 if quality == 'major' else 3)
                            fifth = self.lookup._add_semitones(root, 7)
                            notes.extend([third, fifth])
                    return {
                        'chord_notes': notes,
                        'root': root,
                        'quality': quality,
                        'clef': 'treble'
                    }
                else:
                    self._log_error(f"Unsupported ear training type: {training_type}", parsed_data.get('original_question', ''))
                    return None
            
            elif question_type == 'key_signature':
                key = parsed_data.get('key', 'C')
                mode = parsed_data.get('mode', 'major')
                return self.lookup.get_key_signature(key, mode)

            elif question_type == 'musical_form':
                # Minimal data needed; builder will render sections from form_type
                form_type = parsed_data.get('form_type')
                if not form_type:
                    self._log_error("Musical form parsing did not provide form_type", parsed_data.get('original_question', ''))
                    return None
                return {'form_type': form_type}
            
            else:
                self._log_error(f"Unknown question type: {question_type}", parsed_data.get('original_question', ''))
                return None
            
        except Exception as e:
            self._log_error(f"Error in musical data lookup: {str(e)}", parsed_data.get('original_question', ''))
            return None
    
    def _build_notation(self, parsed_data: Dict[str, Any], musical_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build notation using the AbjadBuilder."""
        try:
            # Merge parsed data with musical data for building
            build_data = {**parsed_data, **musical_data}
            
            staff = self.builder.build_notation(build_data)
            
            if not staff:
                self._log_error("AbjadBuilder returned None staff", parsed_data.get('original_question', ''))
                return None
            
            # Get staff information
            staff_info = self.builder.get_staff_info(staff)
            
            return {
                'staff': staff,
                'staff_info': staff_info,
                'build_data': build_data
            }
            
        except Exception as e:
            self._log_error(f"Error in notation building: {str(e)}", parsed_data.get('original_question', ''))
            return None
    
    def _validate_notation(self, staff, parsed_data: Dict[str, Any], validation_level: ValidationLevel) -> Dict[str, Any]:
        """Validate notation using the NotationValidator."""
        try:
            is_valid = self.validator.validate(staff, parsed_data, validation_level)
            validation_report = self.validator.get_validation_report()
            
            return {
                'is_valid': is_valid,
                'report': validation_report,
                'validation_level': validation_level.value
            }
            
        except Exception as e:
            self._log_error(f"Error in notation validation: {str(e)}", parsed_data.get('original_question', ''))
            return {
                'is_valid': False,
                'report': {'error': str(e)},
                'validation_level': validation_level.value
            }
    
    def _export_to_lilypond(self, staff) -> str:
        """Export staff to LilyPond code."""
        try:
            return self.builder.export_to_lilypond(staff)
        except Exception as e:
            self._log_error(f"Error in LilyPond export: {str(e)}", "")
            return ""
    
    def _generate_image(self, staff) -> Dict[str, Any]:
        """Generate image from staff using the image renderer."""
        try:
            return self.renderer.render_staff_to_image(staff)
        except Exception as e:
            self._log_error(f"Error in image generation: {str(e)}", "")
            return {'error': str(e)}
    
    def _generate_audio(self, staff, instrument: str) -> Dict[str, Any]:
        """Generate audio from staff using the audio renderer."""
        try:
            result = self.audio_renderer.render_staff_to_midi(staff, instrument)
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._log_error(f"Error in audio generation: {str(e)}", "")
            return {'error': str(e)}
    
    def _create_error_result(self, error_message: str, question: str) -> Dict[str, Any]:
        """Create an error result dictionary."""
        return {
            'success': False,
            'question': question,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'cached': False
        }
    
    def _log_error(self, error_message: str, context: str):
        """Log an error with context."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'context': context
        }
        self.error_log.append(error_entry)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = self.cache_stats['hits'] / self.cache_stats['total_requests']
        
        return {
            **self.cache_stats,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get the error log."""
        return self.error_log
    
    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    def clear_error_log(self):
        """Clear the error log."""
        self.error_log = []
    
    def batch_generate(self, questions: List[str], validation_level: ValidationLevel = ValidationLevel.COMPLETE) -> List[Dict[str, Any]]:
        """
        Generate notation for multiple questions in batch.
        
        Args:
            questions: List of questions to process
            validation_level: Level of validation to perform
        
        Returns:
            List of results for each question
        """
        results = []
        
        for i, question in enumerate(questions):
            print(f"Processing question {i+1}/{len(questions)}: {question[:50]}...")
            
            result = self.generate_notation(question, validation_level)
            results.append(result)
        
        return results
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the system state."""
        return {
            'cache_stats': self.get_cache_stats(),
            'error_count': len(self.error_log),
            'components': {
                'parser': 'QuestionParser',
                'lookup': 'TheoryLookup',
                'builder': 'AbjadBuilder',
                'validator': 'NotationValidator'
            },
            'timestamp': datetime.now().isoformat()
        }

# Test the complete system
if __name__ == "__main__":
    engine = MusicTheoryEngine()
    
    # Test questions
    test_questions = [
        "What is the interval between C and E?",
        "What is the iii chord in C major?",
        "What is the C major scale?",
        "What is the time signature 3/4?"
    ]
    
    print("🧪 Testing Music Theory Engine")
    print("=" * 50)
    
    for i, question in enumerate(test_questions):
        print(f"\n📝 Test {i+1}: {question}")
        
        result = engine.generate_notation(question)
        
        if result['success']:
            print(f"✅ Success!")
            print(f"   Type: {result['parsed_data']['type']}")
            print(f"   Valid: {result['validation']['is_valid']}")
            print(f"   Processing time: {result['processing_time']:.3f}s")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Print system info
    print(f"\n📊 System Info:")
    system_info = engine.get_system_info()
    print(f"   Cache hit rate: {system_info['cache_stats']['hit_rate']:.2%}")
    print(f"   Error count: {system_info['error_count']}")
    print(f"   Cache size: {system_info['cache_stats']['cache_size']}")
