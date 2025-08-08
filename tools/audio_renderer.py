import os
import subprocess
from typing import Optional, Dict, Any, List
import base64
import uuid
import tempfile
import abjad

class AudioRenderer:
    """
    Handles rendering Abjad staff objects to MIDI files using LilyPond.
    Provides audio playback functionality for the music theory tutor.
    """
    
    def __init__(self):
        self.lilypond_path = self._find_lilypond()
        self.temp_dir = tempfile.gettempdir()
        # Initialize pygame mixer for MIDI playback
        # pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512) # Removed pygame
    
    def _find_lilypond(self) -> str:
        """Find LilyPond installation path"""
        # Common Windows paths
        possible_paths = [
            r"C:\Program Files\lilypond-2.24.4\bin\lilypond.exe",
            r"C:\Program Files (x86)\lilypond-2.24.4\bin\lilypond.exe",
            r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\LilyPond.LilyPond_Microsoft.WinGet.Source_8wekyb3d8bbwe\lilypond-2.24.4\bin\lilypond.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['lilypond', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return 'lilypond'
        except FileNotFoundError:
            pass
        
        raise FileNotFoundError("LilyPond not found. Please install LilyPond.")
    
    def render_staff_to_midi(self, staff: abjad.Staff, 
                             filename: Optional[str] = None,
                              tempo: int = 120,
                              instrument: str = "Music Theory") -> Dict[str, Any]:
        """
        Render an Abjad staff to a MIDI file and convert to WAV for web playback.
        
        Args:
            staff: The Abjad staff object
            filename: Optional filename for the output files
            tempo: Tempo in BPM
            instrument: The selected instrument for audio synthesis
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = f"audio_{uuid.uuid4().hex[:8]}"
            
            # Create paths - LilyPond generates .mid, not .midi
            ly_path = os.path.join(self.temp_dir, f"{filename}.ly")
            midi_path = os.path.join(self.temp_dir, f"{filename}.mid")  # Fixed: .mid not .midi
            wav_path = os.path.join(self.temp_dir, f"{filename}.wav")
            
            # Create LilyPond file with MIDI output
            lilypond_code = self._create_midi_template(staff, tempo)
            
            with open(ly_path, 'w', encoding='utf-8') as f:
                f.write(lilypond_code)
            
            # Run LilyPond to generate MIDI
            result = subprocess.run([
                self.lilypond_path,
                '--output=' + os.path.join(self.temp_dir, filename),  # Fixed: use filename without extension
                ly_path
            ], capture_output=True, text=True)
            
            # Check if LilyPond succeeded (return code 0) and MIDI file exists
            if result.returncode == 0:
                # Check if MIDI file was actually created
                if os.path.exists(midi_path):
                    
                    # Convert MIDI to WAV using actual staff notes with instrument-specific synthesis
                    wav_success = self._convert_midi_to_wav_with_staff(midi_path, wav_path, staff, tempo, instrument)
                    
                    if wav_success and os.path.exists(wav_path):
                        
                        # Convert WAV to base64 for Streamlit
                        audio_base64 = self._wav_to_base64(wav_path)
                        
                        # Get actual duration from WAV file
                        actual_duration = self._get_wav_duration(wav_path)
                        
                        return {
                            'success': True,
                            'midi_path': midi_path,
                            'wav_path': wav_path,
                            'audio_base64': audio_base64,
                            'tempo': tempo,
                            'duration': actual_duration,
                            'instrument': instrument
                        }
                    else:
                        return {'error': 'Failed to convert MIDI to WAV'}
                else:
                    return {'error': f'MIDI file not found at {midi_path}'}
            else:
                return {'error': f'LilyPond failed with return code {result.returncode}: {result.stderr}'}
                
        except Exception as e:
            return {'error': f'Audio generation failed: {str(e)}'}
    
    def _convert_midi_to_wav_with_staff(self, midi_path: str, wav_path: str, staff: abjad.Staff, tempo: int, instrument: str) -> bool:
        """
        Convert MIDI to WAV using the actual MIDI file for proper musical synthesis.
        """
        try:
            
            # Use the actual MIDI file that LilyPond generated
            # This contains proper musical data, not just sine waves
            result = self._convert_midi_to_wav_direct(midi_path, wav_path, instrument)
            
            if result:
                return True
            else:
                return self._create_instrument_synthesis_fallback(wav_path, staff, tempo, instrument)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._create_instrument_synthesis_fallback(wav_path, staff, tempo, instrument)

    def _convert_midi_to_wav_direct(self, midi_path: str, wav_path: str, instrument: str) -> bool:
        """
        Convert MIDI file directly to WAV using proper MIDI synthesis.
        """
        try:
            import wave
            import numpy as np
            from scipy import signal
            
            # MIDI parameters
            sample_rate = 44100
            tempo = 120  # Default tempo
            
            # Read MIDI file and extract note data
            midi_notes = self._extract_midi_notes(midi_path)
            
            if not midi_notes:
                return False
            
            # Calculate total duration - ensure we start at 0 and have proper timing
            max_time = max(note['start_time'] + note['duration'] for note in midi_notes)
            # Add a small buffer to ensure all notes are included
            total_duration = max_time + 0.5
            total_frames = int(total_duration * sample_rate)
            audio_data = np.zeros(total_frames)
            
            # Get instrument parameters
            params = self._get_instrument_parameters(instrument)
            
            # Convert MIDI note numbers to frequencies
            def midi_to_freq(midi_note):
                return 440 * (2 ** ((midi_note - 69) / 12))
            
            # Generate audio for each MIDI note
            for note in midi_notes:
                if note['velocity'] == 0:  # Skip note-off events
                    continue
                
                # Calculate note parameters
                freq = midi_to_freq(note['note'])
                start_frame = int(note['start_time'] * sample_rate)
                duration_frames = int(note['duration'] * sample_rate)
                velocity = note['velocity'] / 127.0  # Normalize velocity
                
                # Generate realistic instrument sound for this note
                for i in range(duration_frames):
                    if start_frame + i >= total_frames:
                        break
                    
                    t = (start_frame + i) / sample_rate
                    
                    # Create rich, instrument-specific tone
                    tone = 0
                    
                    # Fundamental frequency
                    fundamental = np.sin(2 * np.pi * freq * t)
                    tone += fundamental * params['fundamental_amplitude'] * velocity
                    
                    # Add realistic harmonics for the specific instrument
                    for harmonic in params['harmonics']:
                        tone += np.sin(2 * np.pi * freq * harmonic['frequency_multiplier'] * t) * harmonic['amplitude'] * velocity
                    
                    # Add slight inharmonicity (like real instruments)
                    inharmonic_factor = params['inharmonicity']
                    tone += np.sin(2 * np.pi * freq * 2 * t * inharmonic_factor) * 0.05 * velocity
                    
                    # Add very subtle noise for realism
                    noise = np.random.normal(0, params['noise_level'])
                    tone += noise
                    
                    # Apply realistic ADSR envelope
                    attack_time = int(duration_frames * params['attack_time'])
                    decay_time = int(duration_frames * params['decay_time'])
                    sustain_level = params['sustain_level']
                    release_time = int(duration_frames * params['release_time'])
                    
                    envelope = 1.0
                    
                    if i < attack_time:  # Attack phase
                        envelope = i / attack_time
                    elif i < attack_time + decay_time:  # Decay phase
                        decay_progress = (i - attack_time) / decay_time
                        envelope = 1.0 - (decay_progress * (1.0 - sustain_level))
                    elif i < duration_frames - release_time:  # Sustain phase
                        envelope = sustain_level
                    else:  # Release phase
                        release_progress = (i - (duration_frames - release_time)) / release_time
                        envelope = sustain_level * (1.0 - release_progress)
                    
                    # Apply envelope and amplitude
                    audio_data[start_frame + i] += tone * envelope * params['overall_amplitude']
            
            # Apply instrument-specific low-pass filter
            cutoff_freq = params['filter_cutoff']
            nyquist = sample_rate / 2
            normalized_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            audio_data = signal.filtfilt(b, a, audio_data)
            
            # Apply final amplitude and convert to 16-bit PCM
            audio_data = audio_data * 16384
            audio_data = np.clip(audio_data, -32767, 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(wav_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def _extract_midi_notes(self, midi_path: str) -> List[Dict]:
        """
        Extract note data from MIDI file with proper timing.
        """
        try:
            import mido
            
            notes = []
            tempo = 120  # Default tempo in BPM
            ticks_per_beat = 480  # Default MIDI resolution
            
            # Open MIDI file
            mid = mido.MidiFile(midi_path)
            
            # Get tempo and ticks per beat from the file
            ticks_per_beat = mid.ticks_per_beat
            
            # Process all tracks
            for track in mid.tracks:
                track_time = 0.0
                active_notes = {}  # Track active notes by note number
                
                for msg in track:
                    # Convert ticks to seconds
                    delta_time = msg.time / ticks_per_beat * (60.0 / tempo)
                    track_time += delta_time
                    
                    # Handle tempo changes
                    if msg.type == 'set_tempo':
                        tempo = mido.tempo2bpm(msg.tempo)
                        continue
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Note start
                        note_data = {
                            'note': msg.note,
                            'velocity': msg.velocity,
                            'start_time': track_time,
                            'duration': 0.5,  # Default duration
                            'channel': msg.channel
                        }
                        notes.append(note_data)
                        active_notes[msg.note] = note_data
                        
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # Note end - find the corresponding note start
                        if msg.note in active_notes:
                            note_data = active_notes[msg.note]
                            note_data['duration'] = track_time - note_data['start_time']
                            # Ensure minimum duration
                            if note_data['duration'] < 0.1:
                                note_data['duration'] = 0.5
                            del active_notes[msg.note]
            
            # If no notes found, create a simple test note
            if not notes:
                notes.append({
                    'note': 60,  # Middle C
                    'velocity': 100,
                    'start_time': 0.0,
                    'duration': 1.0,
                    'channel': 0
                })
            
            return notes
            
        except ImportError:
            return []
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []

    def _create_instrument_synthesis_fallback(self, wav_path: str, staff: abjad.Staff, tempo: int, instrument: str) -> bool:
        """
        Fallback synthesis using staff notes when MIDI conversion fails.
        """
        try:
            
            # Extract notes from staff
            notes_data = self._extract_notes_from_staff(staff)
            
            if not notes_data:
                return self._create_simple_wav(wav_path, 2.0)
            
            # Calculate total duration
            total_duration = sum(note['duration'] for note in notes_data)
            
            # Use the improved synthesis method
            return self._create_musical_wav_from_notes(wav_path, notes_data, tempo, total_duration, instrument)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def _create_musical_wav_from_notes(self, wav_path: str, notes_data: List[Dict], tempo: int, total_duration: float, instrument: str) -> bool:
        """
        Create WAV file from actual staff notes with improved musical synthesis.
        """
        try:
            import wave
            import numpy as np
            from scipy import signal # Added for filtering
            
            # Audio parameters
            sample_rate = 44100
            amplitude = 0.7  # Reduced amplitude to prevent clipping
            
            # Convert total duration from beats to seconds
            beats_per_second = tempo / 60.0
            total_duration_seconds = total_duration / beats_per_second
            
            # Calculate total frames
            total_frames = int(total_duration_seconds * sample_rate)
            audio_data = np.zeros(total_frames)
            
            # Convert MIDI note numbers to frequencies
            def midi_to_freq(midi_note):
                return 440 * (2 ** ((midi_note - 69) / 12))
            
            # Generate audio for each note
            current_frame = 0
            
            for note_info in notes_data:
                # Skip rests (no audio)
                if note_info['type'] == 'rest':
                    continue
                
                # Calculate note parameters
                midi_note = note_info.get('midi_note', 60)  # Default to middle C
                duration_beats = note_info['duration']
                duration_seconds = duration_beats / beats_per_second
                note_frames = int(duration_seconds * sample_rate)
                
                # Get frequency for this note
                freq = midi_to_freq(midi_note)
                
                # Get instrument-specific parameters
                params = self._get_instrument_parameters(instrument)
                
                # Create a realistic instrument sound
                for i in range(note_frames):
                    if current_frame + i >= total_frames:
                        break
                    
                    t = (current_frame + i) / sample_rate
                    
                    # Create a rich, instrument-specific tone
                    tone = 0
                    
                    # Fundamental frequency
                    fundamental = np.sin(2 * np.pi * freq * t)
                    tone += fundamental * params['fundamental_amplitude']
                    
                    # Add realistic harmonics for the specific instrument
                    for harmonic in params['harmonics']:
                        tone += np.sin(2 * np.pi * freq * harmonic['frequency_multiplier'] * t) * harmonic['amplitude']
                    
                    # Add slight inharmonicity (like real instruments)
                    inharmonic_factor = params['inharmonicity']
                    tone += np.sin(2 * np.pi * freq * 2 * t * inharmonic_factor) * 0.05
                    
                    # Add very subtle noise for realism
                    noise = np.random.normal(0, params['noise_level'])
                    tone += noise
                    
                    # Apply realistic ADSR envelope (Attack, Decay, Sustain, Release)
                    attack_time = int(note_frames * params['attack_time'])
                    decay_time = int(note_frames * params['decay_time'])
                    sustain_level = params['sustain_level']
                    release_time = int(note_frames * params['release_time'])
                    
                    envelope = 1.0
                    
                    if i < attack_time:  # Attack phase - quick rise
                        envelope = i / attack_time
                    elif i < attack_time + decay_time:  # Decay phase
                        decay_progress = (i - attack_time) / decay_time
                        envelope = 1.0 - (decay_progress * (1.0 - sustain_level))
                    elif i < note_frames - release_time:  # Sustain phase
                        envelope = sustain_level
                    else:  # Release phase
                        release_progress = (i - (note_frames - release_time)) / release_time
                        envelope = sustain_level * (1.0 - release_progress)
                    
                    # Apply envelope and amplitude
                    audio_data[current_frame + i] = tone * envelope * amplitude * params['overall_amplitude']
                
                current_frame += note_frames
            
            # Apply instrument-specific low-pass filter
            cutoff_freq = params['filter_cutoff']
            nyquist = sample_rate / 2
            normalized_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            audio_data = signal.filtfilt(b, a, audio_data)
            
            # Apply final amplitude and convert to 16-bit PCM
            audio_data = audio_data * 16384  # Reduced to prevent clipping
            audio_data = np.clip(audio_data, -32767, 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(wav_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_notes_from_staff(self, staff: abjad.Staff) -> list:
        """
        Extract actual notes and their durations from the Abjad staff.
        Returns list of dicts with 'midi_note', 'duration', and 'type'.
        """
        try:
            notes_data = []
            
            for component in staff:
                if isinstance(component, abjad.Note):
                    # Get MIDI note number
                    midi_note = component.written_pitch.number
                    
                    # Get duration in beats (fix the calculation)
                    duration = component.written_duration
                    beats = 4 * duration.numerator / duration.denominator  # Fixed: quarter note = 1 beat
                    
                    notes_data.append({
                        'midi_note': midi_note,
                        'duration': beats,
                        'type': 'note'
                    })
                    
                elif isinstance(component, abjad.Chord):
                    # For chords, use the root note
                    if component.written_pitches:
                        midi_note = component.written_pitches[0].number
                        
                        duration = component.written_duration
                        beats = 4 * duration.numerator / duration.denominator
                        
                        notes_data.append({
                            'midi_note': midi_note,
                            'duration': beats,
                            'type': 'chord'
                        })
                        
                elif isinstance(component, abjad.Rest):
                    # Handle rests
                    duration = component.written_duration
                    beats = 4 * duration.numerator / duration.denominator
                    
                    notes_data.append({
                        'midi_note': None,  # Rest has no pitch
                        'duration': beats,
                        'type': 'rest'
                    })
            
            return notes_data
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []
    
    def _create_simple_wav(self, wav_path: str, duration: float):
        """
        Create a simple WAV file as a placeholder with improved sound quality.
        """
        try:
            import wave
            import numpy as np
            
            # Create a more musical placeholder
            sample_rate = 44100
            frequency = 440  # A4 note
            amplitude = 0.5  # Reduced amplitude
            
            # Calculate number of frames
            num_frames = int(duration * sample_rate)
            audio_data = np.zeros(num_frames)
            
            # Generate a more natural musical tone
            for i in range(num_frames):
                t = i / sample_rate
                
                # Create a richer tone with harmonics
                tone = 0
                # Fundamental
                tone += np.sin(2 * np.pi * frequency * t) * 0.6
                # Second harmonic
                tone += np.sin(2 * np.pi * frequency * 2 * t) * 0.3
                # Third harmonic
                tone += np.sin(2 * np.pi * frequency * 3 * t) * 0.2
                
                # Apply envelope
                envelope = 1.0
                attack_time = num_frames * 0.1
                release_time = num_frames * 0.2
                
                if i < attack_time:
                    envelope = i / attack_time
                elif i > num_frames - release_time:
                    envelope = (num_frames - i) / release_time
                
                audio_data[i] = tone * envelope * amplitude
            
            # Convert to 16-bit PCM
            audio_data = audio_data * 16384
            audio_data = np.clip(audio_data, -32767, 32767).astype(np.int16)
            
            with wave.open(wav_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _wav_to_base64(self, wav_path: str) -> str:
        """
        Convert WAV file to base64 for Streamlit audio component.
        """
        try:
            with open(wav_path, 'rb') as f:
                wav_data = f.read()
                return base64.b64encode(wav_data).decode('utf-8')
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ""
    
    def _get_wav_duration(self, wav_path: str) -> float:
        """
        Get the actual duration of a WAV file in seconds.
        """
        try:
            import wave
            with wave.open(wav_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / sample_rate
                return round(duration, 1)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return 2.0  # Default duration
    
    def _create_midi_template(self, staff: abjad.Staff, tempo: int) -> str:
        """
        Create a LilyPond template optimized for MIDI generation.
        Based on LilyPond documentation: https://lilypond.org/doc/v2.24/Documentation/learning/index.html
        """
        lilypond_code = abjad.lilypond(staff)
        template = f"""\\version "2.24.0"

\\score {{
    \\new Staff {{
        \\tempo 4 = {tempo}
        {lilypond_code}
    }}
    \\midi {{ }}
    \\layout {{ }}
}}
"""
        return template
    
    def _midi_to_base64(self, midi_path: str) -> str:
        """
        Convert MIDI file to base64 for Streamlit audio component.
        Note: Streamlit doesn't directly support MIDI, so we'll need to convert.
        """
        try:
            with open(midi_path, 'rb') as f:
                midi_data = f.read()
                return base64.b64encode(midi_data).decode('utf-8')
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ""
    
    def _estimate_duration(self, staff: abjad.Staff, tempo: int) -> float:
        """
        Estimate the duration of the music in seconds.
        """
        try:
            # Count total beats (quarter note = 1 beat)
            total_beats = 0
            for component in staff:
                if hasattr(component, 'written_duration'):
                    # Convert duration to beats
                    duration = component.written_duration
                    if hasattr(duration, 'numerator') and hasattr(duration, 'denominator'):
                        beats = 4 * duration.numerator / duration.denominator  # Fixed: quarter note = 1 beat
                        total_beats += beats
            
            # Convert beats to seconds
            beats_per_second = tempo / 60.0
            duration_seconds = total_beats / beats_per_second
            
            return max(duration_seconds, 1.0)  # Minimum 1 second
        except:
            return 3.0  # Default duration
    
    def generate_audio_explanation(self, question_type: str, 
                                 correct_answer: str) -> str:
        """
        Generate audio explanation text for different question types.
        """
        explanations = {
            'interval': f"This interval is a {correct_answer}. Listen to how the notes sound together.",
            'chord': f"This is the {correct_answer} chord. Notice the harmonic structure.",
            'scale': f"This is the {correct_answer} scale. Hear the ascending pattern.",
            'key_signature': f"This key signature shows {correct_answer}. Listen to the tonal center.",
            'time_signature': f"This time signature is {correct_answer}. Feel the rhythmic pattern.",
            'note_identification': f"This note is {correct_answer}. Listen to its pitch."
        }
        
        return explanations.get(question_type, f"Listen to this musical example: {correct_answer}")
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.endswith('.ly') or file.endswith('.mid') or file.endswith('.wav'):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _get_instrument_parameters(self, instrument: str) -> Dict[str, Any]:
        """
        Get instrument-specific synthesis parameters for realistic sound generation.
        """
        # Default parameters for Music Theory (piano-like)
        default_params = {
            'fundamental_amplitude': 0.4,
            'harmonics': [
                {'frequency_multiplier': 2, 'amplitude': 0.2},  # Octave
                {'frequency_multiplier': 3, 'amplitude': 0.1},  # Perfect fifth
                {'frequency_multiplier': 4, 'amplitude': 0.05}, # Second octave
                {'frequency_multiplier': 5, 'amplitude': 0.03}, # Major third
            ],
            'inharmonicity': 1.001,
            'noise_level': 0.005,
            'attack_time': 0.02,  # 2% attack
            'decay_time': 0.08,   # 8% decay
            'sustain_level': 0.7,  # 70% sustain
            'release_time': 0.3,   # 30% release
            'filter_cutoff': 8000, # Hz
            'overall_amplitude': 0.3
        }
        
        # Instrument-specific parameters
        instrument_params = {
            "Music Theory": default_params,  # Piano-like
            "Piano": {
                **default_params,
                'fundamental_amplitude': 0.5,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.25},
                    {'frequency_multiplier': 3, 'amplitude': 0.15},
                    {'frequency_multiplier': 4, 'amplitude': 0.08},
                    {'frequency_multiplier': 5, 'amplitude': 0.04},
                ],
                'overall_amplitude': 0.4
            },
            "Violin": {
                'fundamental_amplitude': 0.6,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.3},
                    {'frequency_multiplier': 3, 'amplitude': 0.2},
                    {'frequency_multiplier': 4, 'amplitude': 0.1},
                    {'frequency_multiplier': 5, 'amplitude': 0.05},
                ],
                'inharmonicity': 1.0005,  # Less inharmonicity for strings
                'noise_level': 0.003,
                'attack_time': 0.01,  # Quick attack
                'decay_time': 0.05,
                'sustain_level': 0.8,  # Longer sustain
                'release_time': 0.4,
                'filter_cutoff': 12000,  # Higher frequencies for strings
                'overall_amplitude': 0.35
            },
            "Guitar": {
                'fundamental_amplitude': 0.5,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.3},
                    {'frequency_multiplier': 3, 'amplitude': 0.2},
                    {'frequency_multiplier': 4, 'amplitude': 0.1},
                    {'frequency_multiplier': 5, 'amplitude': 0.05},
                ],
                'inharmonicity': 1.002,  # More inharmonicity for guitar
                'noise_level': 0.008,
                'attack_time': 0.03,
                'decay_time': 0.1,
                'sustain_level': 0.6,
                'release_time': 0.5,
                'filter_cutoff': 6000,
                'overall_amplitude': 0.3
            },
            "Flute": {
                'fundamental_amplitude': 0.7,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.4},
                    {'frequency_multiplier': 3, 'amplitude': 0.2},
                    {'frequency_multiplier': 4, 'amplitude': 0.1},
                ],
                'inharmonicity': 1.0001,  # Very little inharmonicity
                'noise_level': 0.002,
                'attack_time': 0.05,  # Slower attack
                'decay_time': 0.1,
                'sustain_level': 0.9,  # Very long sustain
                'release_time': 0.6,
                'filter_cutoff': 15000,  # Very high frequencies
                'overall_amplitude': 0.25
            },
            "Clarinet": {
                'fundamental_amplitude': 0.6,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.3},
                    {'frequency_multiplier': 3, 'amplitude': 0.4},  # Strong third harmonic
                    {'frequency_multiplier': 4, 'amplitude': 0.2},
                    {'frequency_multiplier': 5, 'amplitude': 0.1},
                ],
                'inharmonicity': 1.0003,
                'noise_level': 0.004,
                'attack_time': 0.02,
                'decay_time': 0.08,
                'sustain_level': 0.8,
                'release_time': 0.3,
                'filter_cutoff': 10000,
                'overall_amplitude': 0.3
            },
            "Trumpet": {
                'fundamental_amplitude': 0.5,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.4},
                    {'frequency_multiplier': 3, 'amplitude': 0.3},
                    {'frequency_multiplier': 4, 'amplitude': 0.2},
                    {'frequency_multiplier': 5, 'amplitude': 0.1},
                ],
                'inharmonicity': 1.0002,
                'noise_level': 0.006,
                'attack_time': 0.01,  # Very quick attack
                'decay_time': 0.05,
                'sustain_level': 0.9,
                'release_time': 0.2,
                'filter_cutoff': 12000,
                'overall_amplitude': 0.4
            },
            "Voice": {
                'fundamental_amplitude': 0.6,
                'harmonics': [
                    {'frequency_multiplier': 2, 'amplitude': 0.3},
                    {'frequency_multiplier': 3, 'amplitude': 0.2},
                    {'frequency_multiplier': 4, 'amplitude': 0.1},
                    {'frequency_multiplier': 5, 'amplitude': 0.05},
                ],
                'inharmonicity': 1.0005,
                'noise_level': 0.01,  # More noise for voice
                'attack_time': 0.03,
                'decay_time': 0.1,
                'sustain_level': 0.7,
                'release_time': 0.4,
                'filter_cutoff': 8000,
                'overall_amplitude': 0.3
            }
        }
        
        return instrument_params.get(instrument, default_params)

# Test the audio renderer
if __name__ == "__main__":
    import abjad
    
    # Create a simple test staff
    staff = abjad.Staff()
    staff.append(abjad.Note("c'4"))
    staff.append(abjad.Note("d'4"))
    staff.append(abjad.Note("e'4"))
    staff.append(abjad.Note("f'4"))
    
    renderer = AudioRenderer()
    result = renderer.render_staff_to_midi(staff, "test_scale")
    
    if result.get('success', False):
        print(f"✅ Audio generated successfully!")
        print(f"   Duration: {result.get('duration', 0):.1f} seconds")
        print(f"   Tempo: {result.get('tempo', 120)} BPM")
        print(f"   WAV Path: {result.get('wav_path', 'N/A')}")
    else:
        print(f"❌ Audio generation failed: {result.get('error', 'Unknown error')}")
