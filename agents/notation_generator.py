import abjad
import os
import tempfile
from openai import OpenAI

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

def generate_custom_lilypond_code(question_text, is_answer=False):
    """Generate optimized LilyPond template for all cases"""
    
    # Always return the optimized template - let Abjad handle the specific content
    return r"""
\version "2.24.4"

#(set-global-staff-size 26)

\paper {
  indent = 0
  line-width = 800\mm
  top-margin = 0\mm
  bottom-margin = 0\mm
  left-margin = 0\mm
  right-margin = 0\mm
  page-count = 1
  ragged-right = ##f
  page-limit-inter-system-space = ##f
  page-limit-inter-markup-space = ##f
  print-page-number = ##f
  print-first-page-number = ##f
  bookTitleMarkup = \markup { }
  scoreTitleMarkup = \markup { }
  evenFooterMarkup = \markup { }
  oddFooterMarkup = \markup { }
  evenHeaderMarkup = \markup { }
  oddHeaderMarkup = \markup { }
}
"""

def generate_abjad_notation(question_text, is_answer=False):
    """Generate musical notation using Abjad based on question text"""
    
    client = get_openai_client()
    
    # Sanitize question text to avoid layout weirdness
    question_text = question_text.replace('\n', ' ').strip()
    
    prompt = f"""
    You are a professional musician and LilyPond/Abjad expert. Your task has TWO STEPS:

    STEP 1: INTERPRET THE QUESTION
    Analyze this music theory question to understand EXACTLY what notes/chords it's asking about:
    
    Question: {question_text}
    Is Answer: {is_answer}
    
    First, identify:
    - What specific notes or chords are mentioned?
    - What key is being discussed?
    - What harmonic progression is described?
    - What musical concept is being tested?
    
    STEP 2: GENERATE CORRECT ABAJAD CODE
    Based on your interpretation, create Abjad code that accurately represents the musical content.
    
    CRITICAL REQUIREMENTS:
    - You MUST show EXACTLY what the question is asking about
    - If the question mentions specific notes, show those notes
    - If the question mentions a chord, show that chord
    - If the question mentions an interval, show both notes of the interval
    - If the question mentions a scale, show the scale
    - If the question mentions a progression, show the progression
    - Use ONLY: abjad.Staff(), abjad.Note(), abjad.Chord(), abjad.Rest()
    - For single notes: abjad.Note("c4")
    - For chords: abjad.Chord(["c", "e", "g"], (1, 4))
    - Use proper pitch names: "c", "d", "e", "f", "g", "a", "b"
         - For accidentals: Use base notes only - "c", "d", "e", "f", "g", "a", "b" (accidentals handled by key signatures)
     - For flats: Use base notes only - "c", "d", "e", "f", "g", "a", "b" (accidentals handled by key signatures)
    
    EXAMPLES:
    
    For "What is the note on the second line from the bottom in the treble clef?":
    staff = abjad.Staff()
    staff.append(abjad.Note("g4"))  # G on the second line
    
    For "What is the interval between C and E?":
    staff = abjad.Staff()
    staff.append(abjad.Note("c4"))
    staff.append(abjad.Note("e4"))
    
    For "What is the quality of the interval formed between the notes G and D?":
    staff = abjad.Staff()
    staff.append(abjad.Note("g4"))
    staff.append(abjad.Note("d4"))
    
    For "What is the vii° chord in A minor?":
    staff = abjad.Staff()
    staff.append(abjad.Chord(["g", "b", "d"], (1, 4)))  # G-B-D in A minor
    
    For "What is the iii chord in C major?":
    staff = abjad.Staff()
    staff.append(abjad.Chord(["e", "g", "b"], (1, 4)))  # E-G-B (E minor) in C major
    
    For "What are the notes in a C major triad?":
    staff = abjad.Staff()
    staff.append(abjad.Chord(["c", "e", "g"], (1, 4)))
    
    For "What is the G major scale?":
    staff = abjad.Staff()
    staff.append(abjad.Note("g'4"))
    staff.append(abjad.Note("a'4"))
    staff.append(abjad.Note("b'4"))
    staff.append(abjad.Note("c''4"))
    staff.append(abjad.Note("d''4"))
    staff.append(abjad.Note("e''4"))
         staff.append(abjad.Note("f''4"))  # F (F# handled by key signature)
    staff.append(abjad.Note("g''4"))
    
    For harmonic progression (I-IV-V-I):
    staff = abjad.Staff()
    staff.append(abjad.Chord(["c", "e", "g"], (1, 4)))
    staff.append(abjad.Rest((1, 4)))
    staff.append(abjad.Chord(["f", "a", "c"], (1, 4)))
    staff.append(abjad.Rest((1, 4)))
    staff.append(abjad.Chord(["g", "b", "d"], (1, 4)))
    staff.append(abjad.Rest((1, 4)))
    staff.append(abjad.Chord(["c", "e", "g"], (1, 4)))
    
    CRITICAL: You MUST show ALL the notes/chords that the question mentions. If the question asks about a chord, show ALL the notes in that chord. If the question asks about an interval, show BOTH notes. If the question asks about a scale, show ALL the scale notes. Do not show partial or incomplete notation.
    
    Return ONLY the Python code, no explanations
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        code = response.choices[0].message.content.strip()
        
        # Clean up the code - remove markdown if present
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
        
        # Debug output removed for cleaner logs
        
        # Execute the generated code
        exec_globals = {'abjad': abjad}
        exec(code, exec_globals)
        
        # Get the staff from the executed code
        staff = exec_globals.get('staff')
        if not staff:
            # Try to find any abjad object
            for key, value in exec_globals.items():
                if isinstance(value, abjad.Staff):
                    staff = value
                    break
        
        if not staff:
            raise Exception("No Abjad staff found in generated code")
        
        return staff
        
    except Exception as e:
        print(f"Error generating Abjad notation: {e}")
        return None

def export_notation_image(staff, question_text="", is_answer=False):
    """Export Abjad staff as PNG image using LilyPond with cropping options"""
    
    if not staff:
        return None
    
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.ly', delete=False) as ly_file:
            ly_path = ly_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as png_file:
            png_path = png_file.name
        
        print(f"📁 Creating files at: {ly_path}")
        
        # Always use the optimized template and let Abjad handle the specific content
        lilypond_header = generate_custom_lilypond_code(question_text, is_answer)
        
        # Get basic LilyPond code from Abjad (just the staff content)
        lilypond_code = abjad.lilypond(staff)
        
        # Combine header with staff code and wrap in score block
        full_lilypond_code = lilypond_header + "\n\\score {\n" + lilypond_code + "\n\\layout { }\n}"
        
        # Write the code to .ly file
        with open(ly_path, 'w') as f:
            f.write(full_lilypond_code)
        
        print(f"✅ Created LilyPond file: {ly_path}")
        
        # Convert to PNG using LilyPond with full path
        try:
            import subprocess
            import os
            
            # Full path to LilyPond executable - stable installation
            lilypond_path = r"C:\Program Files\lilypond-2.24.4\bin\lilypond.exe"
            
            print(f"🎵 Using LilyPond at: {lilypond_path}")
            
            result = subprocess.run([
                lilypond_path,
                '-dpreview',
                '-dresolution=300',
                '-dno-point-and-click',
                '-dpreview-format=png',
                '--output=' + png_path.replace('.png', ''),
                ly_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if preview PNG was created
                preview_path = png_path.replace('.png', '.preview.png')
                if os.path.exists(preview_path):
                    print(f"✅ Generated preview PNG image: {preview_path}")
                    return preview_path
                elif os.path.exists(png_path):
                    print(f"✅ Generated PNG image: {png_path}")
                    return png_path
                else:
                    # Try alternative path
                    alt_path = png_path.replace('.png', '.png')
                    if os.path.exists(alt_path):
                        print(f"✅ Generated PNG image: {alt_path}")
                        return alt_path
                    else:
                        print(f"❌ PNG not found, using LilyPond file instead")
                        return ly_path
            else:
                print(f"❌ LilyPond error: {result.stderr}")
                return ly_path
                
        except Exception as e:
            print(f"❌ LilyPond error: {e}")
            return ly_path
        
    except Exception as e:
        print(f"Error exporting notation image: {e}")
        return None

def resize_notation_image(image_path):
    """Resize notation image to 512px height without cropping"""
    
    if not image_path or not image_path.endswith('.png'):
        return image_path
    
    try:
        from PIL import Image
        
        # Open the image
        img = Image.open(image_path)
        width, height = img.size
        
        print(f"📏 Original image size: {width}x{height}")
        
        # Resize to fixed height of 512px while maintaining aspect ratio
        target_height = 512
        aspect_ratio = width / height
        target_width = int(target_height * aspect_ratio)
        
        # Resize the image
        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Save the resized image
        resized_img.save(image_path)
        print(f"📐 Resized from {width}x{height} to {resized_img.size}")
        return image_path
        
    except ImportError:
        print("❌ PIL not available, using original image")
        return image_path
    except Exception as e:
        print(f"❌ Error resizing image: {e}")
        return image_path

def generate_notation_from_question(question_text, is_answer=False):
    """Generate notation image from question text using Abjad"""
    
    print(f"🔍 Generating notation for: {question_text[:50]}...")
    
    # Generate the Abjad staff
    staff = generate_abjad_notation(question_text, is_answer)
    
    if not staff:
        print("❌ Failed to generate Abjad staff")
        return None
    
    print(f"✅ Generated staff with {len(staff)} elements")
    
    # Export image
    img_path = export_notation_image(staff, question_text, is_answer)
    
    if img_path:
        # Resize to 512px height without cropping
        resized_path = resize_notation_image(img_path)
        
        return {
            'image_path': resized_path,
            'staff': staff
        }
    
    print("❌ Failed to export notation")
    return None

if __name__ == "__main__":
    # Test the notation generator with different question types
    test_questions = [
        "What is the interval between C and E in the treble clef?",
        "What are the notes in a C major triad?",
        "What is the G major scale?"
    ]
    
    for i, question in enumerate(test_questions):
        print(f"\n🧪 Test {i+1}: {question}")
        result = generate_notation_from_question(question)
        
        if result:
            print(f"✅ Generated notation:")
            print(f"  Image: {result['image_path']}")
        else:
            print("❌ Failed to generate notation") 
