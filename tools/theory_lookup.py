import json
import os
from typing import Dict, List, Optional, Any
from functools import lru_cache
from music21 import scale, key, pitch

class TheoryLookup:
    """
    Comprehensive music theory lookup system with caching and fallback mechanisms.
    Contains databases for scales, chords, intervals, and other musical concepts.
    """
    
    def __init__(self):
        self.cache = {}
        self.scales = self._load_scales()
        self.chords = self._load_chords()
        self.intervals = self._load_intervals()
        self.time_signatures = self._load_time_signatures()
        self.key_signatures = self._load_key_signatures()
        self.rhythms = self._load_rhythms()
        self.harmony = self._load_harmony()
        self.ear_training = self._load_ear_training()
        self.musical_form = self._load_musical_form()
        
        # Musical note relationships
        self.note_order = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        self.semitones = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
    
    def _load_scales(self) -> Dict[str, Dict]:
        """Load scale database"""
        return {
            'C_major': {
                'notes': ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C'],
                'abjad_notes': ['c', 'd', 'e', 'f', 'g', 'a', 'b', 'c'],
                'key_signature': 'c \\major',
                'grade_level': 1
            },
            'G_major': {
                'notes': ['G', 'A', 'B', 'C', 'D', 'E', 'F#', 'G'],
                'abjad_notes': ['g', 'a', 'b', 'c', 'd', 'e', 'f', 'g'],
                'key_signature': 'g \\major',
                'grade_level': 2
            },
            'D_major': {
                'notes': ['D', 'E', 'F#', 'G', 'A', 'B', 'C#', 'D'],
                'abjad_notes': ['d', 'e', 'f', 'g', 'a', 'b', 'c', 'd'],
                'key_signature': 'd \\major',
                'grade_level': 3
            },
            'A_major': {
                'notes': ['A', 'B', 'C#', 'D', 'E', 'F#', 'G#', 'A'],
                'abjad_notes': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'a'],
                'key_signature': 'a \\major',
                'grade_level': 4
            },
            'E_major': {
                'notes': ['E', 'F#', 'G#', 'A', 'B', 'C#', 'D#', 'E'],
                'abjad_notes': ['e', 'f', 'g', 'a', 'b', 'c', 'd', 'e'],
                'key_signature': 'e \\major',
                'grade_level': 5
            },
            'A_minor': {
                'notes': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'A'],
                'abjad_notes': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'a'],
                'key_signature': 'a \\minor',
                'grade_level': 3
            },
            'E_minor': {
                'notes': ['E', 'F#', 'G', 'A', 'B', 'C', 'D', 'E'],
                'abjad_notes': ['e', 'f', 'g', 'a', 'b', 'c', 'd', 'e'],
                'key_signature': 'e \\minor',
                'grade_level': 4
            }
        }
    
    def _load_chords(self) -> Dict[str, Dict]:
        """Load chord database"""
        return {
            'triads': {
                'C_major': {
                    'notes': ['C', 'E', 'G'],
                    'abjad_notes': ['c', 'e', 'g'],
                    'roman_numeral': 'I',
                    'grade_level': 1
                },
                'D_minor': {
                    'notes': ['D', 'F', 'A'],
                    'abjad_notes': ['d', 'f', 'a'],
                    'roman_numeral': 'ii',
                    'grade_level': 2
                },
                'E_minor': {
                    'notes': ['E', 'G', 'B'],
                    'abjad_notes': ['e', 'g', 'b'],
                    'roman_numeral': 'iii',
                    'grade_level': 3
                },
                'F_major': {
                    'notes': ['F', 'A', 'C'],
                    'abjad_notes': ['f', 'a', 'c'],
                    'roman_numeral': 'IV',
                    'grade_level': 2
                },
                'G_major': {
                    'notes': ['G', 'B', 'D'],
                    'abjad_notes': ['g', 'b', 'd'],
                    'roman_numeral': 'V',
                    'grade_level': 1
                },
                'A_minor': {
                    'notes': ['A', 'C', 'E'],
                    'abjad_notes': ['a', 'c', 'e'],
                    'roman_numeral': 'vi',
                    'grade_level': 3
                },
                'B_diminished': {
                    'notes': ['B', 'D', 'F'],
                    'abjad_notes': ['b', 'd', 'f'],
                    'roman_numeral': 'vii°',
                    'grade_level': 4
                }
            },
            'seventh_chords': {
                'C_major_7': {
                    'notes': ['C', 'E', 'G', 'B'],
                    'abjad_notes': ['c', 'e', 'g', 'b'],
                    'grade_level': 5
                },
                'D_minor_7': {
                    'notes': ['D', 'F', 'A', 'C'],
                    'abjad_notes': ['d', 'f', 'a', 'c'],
                    'grade_level': 5
                }
            }
        }
    
    def _load_intervals(self) -> Dict[str, Dict]:
        """Load interval database"""
        return {
            'perfect_unison': {'semitones': 0, 'quality': 'perfect'},
            'minor_second': {'semitones': 1, 'quality': 'minor'},
            'major_second': {'semitones': 2, 'quality': 'major'},
            'minor_third': {'semitones': 3, 'quality': 'minor'},
            'major_third': {'semitones': 4, 'quality': 'major'},
            'perfect_fourth': {'semitones': 5, 'quality': 'perfect'},
            'augmented_fourth': {'semitones': 6, 'quality': 'augmented'},
            'diminished_fifth': {'semitones': 6, 'quality': 'diminished'},
            'perfect_fifth': {'semitones': 7, 'quality': 'perfect'},
            'minor_sixth': {'semitones': 8, 'quality': 'minor'},
            'major_sixth': {'semitones': 9, 'quality': 'major'},
            'minor_seventh': {'semitones': 10, 'quality': 'minor'},
            'major_seventh': {'semitones': 11, 'quality': 'major'},
            'perfect_octave': {'semitones': 12, 'quality': 'perfect'}
        }
    
    def _load_time_signatures(self) -> Dict[str, Dict]:
        """Load time signature database"""
        return {
            '2/4': {
                'beats_per_measure': 2,
                'beat_unit': 4,
                'example_notes': ['c4', 'c4'],
                'grade_level': 1
            },
            '3/4': {
                'beats_per_measure': 3,
                'beat_unit': 4,
                'example_notes': ['c4', 'c4', 'c4'],
                'grade_level': 1
            },
            '4/4': {
                'beats_per_measure': 4,
                'beat_unit': 4,
                'example_notes': ['c4', 'c4', 'c4', 'c4'],
                'grade_level': 1
            },
            '6/8': {
                'beats_per_measure': 6,
                'beat_unit': 8,
                'example_notes': ['c8', 'c8', 'c8', 'c8', 'c8', 'c8'],
                'grade_level': 3
            }
        }
    
    def _load_key_signatures(self) -> Dict[str, Dict]:
        """Load key signature database"""
        return {
            'C_major': {
                'sharps': 0,
                'flats': 0,
                'accidentals': [],
                'grade_level': 1
            },
            'G_major': {
                'sharps': 1,
                'flats': 0,
                'accidentals': ['F#'],
                'grade_level': 2
            },
            'D_major': {
                'sharps': 2,
                'flats': 0,
                'accidentals': ['F#', 'C#'],
                'grade_level': 3
            },
            'A_major': {
                'sharps': 3,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#'],
                'grade_level': 4
            },
            'F_major': {
                'sharps': 0,
                'flats': 1,
                'accidentals': ['Bb'],
                'grade_level': 2
            },
            'E_major': {
                'sharps': 4,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#', 'D#'],
                'grade_level': 5
            },
            'B_major': {
                'sharps': 5,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#', 'D#', 'A#'],
                'grade_level': 6
            },
            'F#_major': {
                'sharps': 6,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#', 'D#', 'A#', 'E#'],
                'grade_level': 7
            },
            'C#_major': {
                'sharps': 7,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#', 'D#', 'A#', 'E#', 'B#'],
                'grade_level': 8
            },
            'Bb_major': {
                'sharps': 0,
                'flats': 2,
                'accidentals': ['Bb', 'Eb'],
                'grade_level': 3
            },
            'Eb_major': {
                'sharps': 0,
                'flats': 3,
                'accidentals': ['Bb', 'Eb', 'Ab'],
                'grade_level': 4
            },
            'Ab_major': {
                'sharps': 0,
                'flats': 4,
                'accidentals': ['Bb', 'Eb', 'Ab', 'Db'],
                'grade_level': 5
            },
            'Db_major': {
                'sharps': 0,
                'flats': 5,
                'accidentals': ['Bb', 'Eb', 'Ab', 'Db', 'Gb'],
                'grade_level': 6
            },
            'Gb_major': {
                'sharps': 0,
                'flats': 6,
                'accidentals': ['Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb'],
                'grade_level': 7
            },
            'Cb_major': {
                'sharps': 0,
                'flats': 7,
                'accidentals': ['Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb', 'Fb'],
                'grade_level': 8
            },
            # Add minor keys
            'A_minor': {
                'sharps': 0,
                'flats': 0,
                'accidentals': [],
                'grade_level': 2
            },
            'E_minor': {
                'sharps': 1,
                'flats': 0,
                'accidentals': ['F#'],
                'grade_level': 3
            },
            'B_minor': {
                'sharps': 2,
                'flats': 0,
                'accidentals': ['F#', 'C#'],
                'grade_level': 4
            },
            'F#_minor': {
                'sharps': 3,
                'flats': 0,
                'accidentals': ['F#', 'C#', 'G#'],
                'grade_level': 5
            },
            'C_minor': {
                'sharps': 0,
                'flats': 3,
                'accidentals': ['Bb', 'Eb', 'Ab'],
                'grade_level': 4
            },
            'G_minor': {
                'sharps': 0,
                'flats': 2,
                'accidentals': ['Bb', 'Eb'],
                'grade_level': 3
            },
            'D_minor': {
                'sharps': 0,
                'flats': 1,
                'accidentals': ['Bb'],
                'grade_level': 2
            }
        }
    
    def _load_rhythms(self) -> Dict[str, Dict]:
        """Load rhythm database"""
        return {
            'basic_patterns': {
                'quarter_notes': {
                    'pattern': ['c4', 'c4', 'c4', 'c4'],
                    'time_signature': '4/4',
                    'description': 'Four quarter notes',
                    'grade_level': 1
                },
                'half_notes': {
                    'pattern': ['c2', 'c2'],
                    'time_signature': '4/4',
                    'description': 'Two half notes',
                    'grade_level': 1
                },
                'eighth_notes': {
                    'pattern': ['c8', 'c8', 'c8', 'c8', 'c8', 'c8', 'c8', 'c8'],
                    'time_signature': '4/4',
                    'description': 'Eight eighth notes',
                    'grade_level': 2
                },
                'syncopation': {
                    'pattern': ['c4', 'r4', 'c4', 'c4'],
                    'time_signature': '4/4',
                    'description': 'Syncopated rhythm with rest',
                    'grade_level': 3
                }
            },
            'time_signatures': {
                '2/4': {
                    'beats': 2,
                    'beat_unit': 4,
                    'common_patterns': ['c4', 'c4'],
                    'grade_level': 1
                },
                '3/4': {
                    'beats': 3,
                    'beat_unit': 4,
                    'common_patterns': ['c4', 'c4', 'c4'],
                    'grade_level': 1
                },
                '4/4': {
                    'beats': 4,
                    'beat_unit': 4,
                    'common_patterns': ['c4', 'c4', 'c4', 'c4'],
                    'grade_level': 1
                },
                '6/8': {
                    'beats': 6,
                    'beat_unit': 8,
                    'common_patterns': ['c8', 'c8', 'c8', 'c8', 'c8', 'c8'],
                    'grade_level': 3
                }
            }
        }
    
    def _load_harmony(self) -> Dict[str, Dict]:
        """Load harmony database"""
        return {
            'progressions': {
                'I_IV_V': {
                    'chords': ['I', 'IV', 'V'],
                    'description': 'Basic three-chord progression',
                    'grade_level': 2
                },
                'ii_V_I': {
                    'chords': ['ii', 'V', 'I'],
                    'description': 'Jazz standard progression',
                    'grade_level': 4
                },
                'I_vi_IV_V': {
                    'chords': ['I', 'vi', 'IV', 'V'],
                    'description': 'Pop progression',
                    'grade_level': 3
                }
            },
            'seventh_chords': {
                'dominant_seventh': {
                    'structure': 'major_triad + minor_seventh',
                    'example': 'C-E-G-Bb',
                    'grade_level': 4
                },
                'major_seventh': {
                    'structure': 'major_triad + major_seventh',
                    'example': 'C-E-G-B',
                    'grade_level': 5
                },
                'minor_seventh': {
                    'structure': 'minor_triad + minor_seventh',
                    'example': 'C-Eb-G-Bb',
                    'grade_level': 4
                }
            },
            'voice_leading': {
                'common_tone': {
                    'description': 'Keep common tones between chords',
                    'grade_level': 3
                },
                'stepwise_motion': {
                    'description': 'Move voices by step when possible',
                    'grade_level': 3
                }
            }
        }
    
    def _load_ear_training(self) -> Dict[str, Dict]:
        """Load ear training database"""
        return {
            'intervals': {
                'unison': {'semitones': 0, 'grade_level': 1},
                'minor_second': {'semitones': 1, 'grade_level': 2},
                'major_second': {'semitones': 2, 'grade_level': 1},
                'minor_third': {'semitones': 3, 'grade_level': 2},
                'major_third': {'semitones': 4, 'grade_level': 1},
                'perfect_fourth': {'semitones': 5, 'grade_level': 2},
                'perfect_fifth': {'semitones': 7, 'grade_level': 1},
                'minor_sixth': {'semitones': 8, 'grade_level': 3},
                'major_sixth': {'semitones': 9, 'grade_level': 2},
                'minor_seventh': {'semitones': 10, 'grade_level': 4},
                'major_seventh': {'semitones': 11, 'grade_level': 4},
                'octave': {'semitones': 12, 'grade_level': 2}
            },
            'chord_qualities': {
                'major': {'description': 'Bright, happy sound', 'grade_level': 1},
                'minor': {'description': 'Sad, somber sound', 'grade_level': 2},
                'diminished': {'description': 'Tense, unstable sound', 'grade_level': 4},
                'augmented': {'description': 'Bright, tense sound', 'grade_level': 5}
            },
            'scales': {
                'major': {'description': 'Happy, bright scale', 'grade_level': 1},
                'natural_minor': {'description': 'Sad, dark scale', 'grade_level': 2},
                'harmonic_minor': {'description': 'Dark, exotic scale', 'grade_level': 3},
                'melodic_minor': {'description': 'Jazz scale', 'grade_level': 4}
            }
        }
    
    def _load_musical_form(self) -> Dict[str, Dict]:
        """Load musical form database"""
        return {
            'basic_forms': {
                'binary': {
                    'structure': 'A-B',
                    'description': 'Two contrasting sections',
                    'grade_level': 2
                },
                'ternary': {
                    'structure': 'A-B-A',
                    'description': 'Three sections with return',
                    'grade_level': 3
                },
                'rondo': {
                    'structure': 'A-B-A-C-A',
                    'description': 'Main theme alternates with episodes',
                    'grade_level': 4
                }
            },
            'sections': {
                'verse': {
                    'description': 'Main melodic section',
                    'grade_level': 2
                },
                'chorus': {
                    'description': 'Repeated section with hook',
                    'grade_level': 2
                },
                'bridge': {
                    'description': 'Contrasting middle section',
                    'grade_level': 3
                },
                'intro': {
                    'description': 'Opening section',
                    'grade_level': 2
                },
                'outro': {
                    'description': 'Closing section',
                    'grade_level': 2
                }
            },
            'phrases': {
                'antecedent': {
                    'description': 'Question phrase',
                    'grade_level': 3
                },
                'consequent': {
                    'description': 'Answer phrase',
                    'grade_level': 3
                }
            }
        }
    
    @lru_cache(maxsize=128)
    def get_scale(self, key: str, mode: str = 'major') -> Optional[Dict]:
        """
        Get scale data for a given key and mode.
        Uses caching for performance.
        """
        cache_key = f"{key}_{mode}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        scale_key = f"{key}_{mode}"
        scale_data = self.scales.get(scale_key)
        
        if scale_data:
            self.cache[cache_key] = scale_data
            return scale_data
        
        # If not found, calculate dynamically
        calculated_scale = self._calculate_scale(key, mode)
        if calculated_scale:
            self.cache[cache_key] = calculated_scale
            return calculated_scale
        
        return None
    
    def _calculate_scale(self, key: str, mode: str) -> Optional[Dict]:
        """
        Calculate scale data dynamically using music21.
        """
        try:
            # Create the appropriate scale using music21
            if mode == 'major':
                s = scale.MajorScale(key)
            elif mode == 'minor' or mode == 'natural_minor':
                s = scale.MinorScale(key)
            elif mode == 'harmonic_minor':
                s = scale.HarmonicMinorScale(key)
            elif mode == 'melodic_minor':
                s = scale.MelodicMinorScale(key)
            else:
                return None
            
            # Get scale pitches (one octave)
            pitches = s.getPitches(f"{key}3", f"{key}4")
            
            # Extract note names and convert to Abjad format
            notes = []
            abjad_notes = []
            
            for p in pitches:
                note_name = p.name
                notes.append(note_name)
                
                # Convert to Abjad format
                abjad_note = self._music21_to_abjad(p)
                abjad_notes.append(abjad_note)
            
            return {
                'notes': notes,
                'abjad_notes': abjad_notes,
                'key_signature': f"{key.lower()} \\{mode}",
                'grade_level': self._estimate_grade_level(key, mode)
            }
            
        except Exception as e:
            print(f"Error calculating scale for {key} {mode}: {e}")
            return None
    
    def get_chord(self, degree: str, key: str, mode: str = 'major') -> Optional[Dict]:
        """
        Get chord data for a given degree in a key.
        """
        cache_key = f"chord_{degree}_{key}_{mode}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # First try to get from database
        chord_key = f"{key}_{mode}"
        chord_data = self.chords['triads'].get(chord_key)
        
        if chord_data:
            self.cache[cache_key] = chord_data
            return chord_data
        
        # Calculate dynamically
        calculated_chord = self._calculate_chord(degree, key, mode)
        if calculated_chord:
            self.cache[cache_key] = calculated_chord
            return calculated_chord
        
        return None
    
    def _calculate_chord(self, degree: str, key: str, mode: str) -> Optional[Dict]:
        """
        Calculate chord data dynamically.
        """
        try:
            # Get the scale for the key
            scale_data = self.get_scale(key, mode)
            if not scale_data:
                return None
            
            scale_notes = scale_data['notes']
            
            # Map degree to scale position
            degree_map = {
                'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4, 'vi': 5, 'vii': 6,
                'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6
            }
            
            if degree.lower() not in degree_map:
                return None
            
            position = degree_map[degree.lower()]
            root_note = scale_notes[position]
            
            # Build triad
            third_note = scale_notes[(position + 2) % 7]
            fifth_note = scale_notes[(position + 4) % 7]
            
            chord_notes = [root_note, third_note, fifth_note]
            abjad_notes = [self._note_to_abjad(note) for note in chord_notes]
            
            return {
                'notes': chord_notes,
                'abjad_notes': abjad_notes,
                'roman_numeral': degree,
                'grade_level': self._estimate_grade_level(key, mode)
            }
            
        except Exception as e:
            print(f"Error calculating chord {degree} in {key} {mode}: {e}")
            return None
    
    def get_interval(self, start_note: str, end_note: str) -> Optional[Dict]:
        """
        Calculate interval between two notes.
        """
        try:
            # Handle case sensitivity for accidentals
            start_note_upper = start_note.upper()
            end_note_upper = end_note.upper()
            
            # For notes with flats, handle case properly
            # Only replace 'B' with 'b' if it's actually a flat (like 'Bb'), not if it's just 'B'
            if 'b' in start_note.lower() and len(start_note) > 1:
                start_note_upper = start_note.replace('B', 'b') if 'B' in start_note else start_note
            if 'b' in end_note.lower() and len(end_note) > 1:
                end_note_upper = end_note.replace('B', 'b') if 'B' in end_note else end_note
            
            start_semitone = self.semitones.get(start_note_upper)
            end_semitone = self.semitones.get(end_note_upper)
            
            if start_semitone is None or end_semitone is None:
                return None
            
            # Calculate semitone difference
            semitones = (end_semitone - start_semitone) % 12
            
            # Find interval name
            for interval_name, interval_data in self.intervals.items():
                if interval_data['semitones'] == semitones:
                    return {
                        'name': interval_name,
                        'semitones': semitones,
                        'quality': interval_data['quality'],
                        'start_note': start_note.upper(),
                        'end_note': end_note.upper()
                    }
            
            return None
            
        except Exception as e:
            print(f"Error calculating interval {start_note} to {end_note}: {e}")
            return None
    
    def get_time_signature(self, signature: str) -> Optional[Dict]:
        """
        Get time signature data.
        """
        return self.time_signatures.get(signature)
    
    def get_key_signature(self, key: str, mode: str = 'major') -> Optional[Dict]:
        """
        Get key signature data.
        """
        key_key = f"{key}_{mode}"
        return self.key_signatures.get(key_key)
    
    def _music21_to_abjad(self, p: pitch.Pitch) -> str:
        """
        Convert music21 pitch to Abjad format.
        Returns simplified note names that Abjad can handle.
        """
        # Get the note name without octave
        note_name = p.name
        
        # Convert to simplified Abjad format (base notes only)
        # Abjad only supports basic note names like 'c', 'd', 'e', etc.
        if '#' in note_name:
            # Sharp: C# -> c (simplified)
            base_note = note_name.replace('#', '')
            abjad_note = base_note.lower()
        elif '-' in note_name:
            # Flat: Bb -> b (simplified)
            base_note = note_name.replace('-', '')
            abjad_note = base_note.lower()
        else:
            # Natural note
            abjad_note = note_name.lower()
        
        return abjad_note

    def _note_to_abjad(self, note: str) -> str:
        """
        Convert note name to Abjad format.
        """
        note = note.upper()
        
        # Handle accidentals
        if '#' in note:
            note = note.replace('#', 'is')
        elif 'B' in note and len(note) > 1:
            note = note.replace('B', 'es')
        
        # Convert to lowercase for Abjad
        return note.lower()
    
    def _add_semitones(self, note: str, semitones: int) -> str:
        """
        Add semitones to a note and return the resulting note.
        """
        if note not in self.semitones:
            return note
        
        current_semitone = self.semitones[note]
        new_semitone = (current_semitone + semitones) % 12
        
        # Find note with this semitone value
        for note_name, semitone_value in self.semitones.items():
            if semitone_value == new_semitone:
                return note_name
        
        return note
    
    def _estimate_grade_level(self, key: str, mode: str) -> int:
        """
        Estimate the grade level for a key/mode combination.
        """
        # Simple estimation based on number of accidentals
        if mode == 'major':
            if key in ['C']:
                return 1
            elif key in ['G', 'F']:
                return 2
            elif key in ['D', 'A']:
                return 3
            else:
                return 4
        else:  # minor
            if key in ['A', 'E']:
                return 3
            else:
                return 4
    
    def clear_cache(self):
        """Clear the lookup cache."""
        self.cache.clear()

# Test the theory lookup
if __name__ == "__main__":
    lookup = TheoryLookup()
    
    # Test scale lookup
    print("Testing scale lookup:")
    c_major = lookup.get_scale('C', 'major')
    print(f"C major scale: {c_major}")
    
    # Test chord lookup
    print("\nTesting chord lookup:")
    c_chord = lookup.get_chord('I', 'C', 'major')
    print(f"C major I chord: {c_chord}")
    
    # Test interval calculation
    print("\nTesting interval calculation:")
    interval = lookup.get_interval('C', 'E')
    print(f"C to E interval: {interval}")
    
    # Test time signature
    print("\nTesting time signature:")
    time_sig = lookup.get_time_signature('3/4')
    print(f"3/4 time signature: {time_sig}")
