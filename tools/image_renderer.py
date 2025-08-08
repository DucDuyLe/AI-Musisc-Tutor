import abjad
import tempfile
import os
import subprocess
from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

class ImageRenderer:
    """
    Handles rendering Abjad staff objects to PNG images using LilyPond.
    Integrated with the modular music theory system.
    """
    
    def __init__(self):
        self.lilypond_path = self._find_lilypond()
        self.temp_dir = tempfile.gettempdir()
    
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
    
    def render_staff_to_image(self, staff: abjad.Staff, 
                             filename: Optional[str] = None,
                             dpi: int = 300,
                             target_height: int = 512) -> Dict[str, Any]:
        """
        Render an Abjad staff to a PNG image.
        
        Args:
            staff: Abjad Staff object
            filename: Optional filename for output
            dpi: Resolution for rendering
            target_height: Target height in pixels
        
        Returns:
            Dictionary with image path and metadata
        """
        try:
            if not staff:
                return {'error': 'No staff provided'}
            
            # Generate LilyPond code
            lilypond_code = abjad.lilypond(staff)
            
            # Create optimized LilyPond template
            full_lilypond_code = self._create_optimized_template(lilypond_code)
            
            # Generate temporary files
            if filename is None:
                filename = f"notation_{hash(lilypond_code) % 10000}"
            
            ly_path = os.path.join(self.temp_dir, f"{filename}.ly")
            png_path = os.path.join(self.temp_dir, f"{filename}.png")
            
            # Write LilyPond file
            with open(ly_path, 'w', encoding='utf-8') as f:
                f.write(full_lilypond_code)
            
            print(f"📁 Created LilyPond file: {ly_path}")
            
            # Run LilyPond
            result = subprocess.run([
                self.lilypond_path,
                '-dpreview',
                '-dresolution=300',
                '--png',
                '--output=' + png_path.replace('.png', ''),
                ly_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ LilyPond error: {result.stderr}")
                return {'error': f'LilyPond failed: {result.stderr}'}
            
            # Find the generated PNG file
            preview_path = png_path.replace('.png', '.preview.png')
            if os.path.exists(preview_path):
                final_path = preview_path
            elif os.path.exists(png_path):
                final_path = png_path
            else:
                return {'error': 'No PNG file generated'}
            
            print(f"✅ Generated PNG image: {final_path}")
            
            # Resize image to target height
            resized_path = self._resize_image(final_path, target_height)
            
            # Get image info
            with Image.open(resized_path) as img:
                width, height = img.size
                print(f"📏 Final image size: {width}x{height}")
            
            return {
                'success': True,
                'image_path': resized_path,
                'original_path': final_path,
                'lilypond_code': lilypond_code,
                'width': width,
                'height': height,
                'dpi': dpi
            }
            
        except Exception as e:
            print(f"❌ Error rendering image: {e}")
            return {'error': str(e)}
    
    def _create_optimized_template(self, lilypond_code: str) -> str:
        """Create optimized LilyPond template with proper paper settings"""
        return f"""\\version "2.24.4"

\\paper {{
    indent = 0
    line-width = 140\\mm
    top-margin = 0\\mm
    bottom-margin = 0\\mm
    left-margin = 0\\mm
    right-margin = 0\\mm
    page-count = 1
    ragged-right = ##f
    page-limit-inter-system-space = ##f
    page-limit-inter-markup-space = ##f
    print-page-number = ##f
    bookTitleMarkup = \\markup {{ }}
    scoreTitleMarkup = \\markup {{ }}
    evenFooterMarkup = \\markup {{ }}
    oddFooterMarkup = \\markup {{ }}
    evenHeaderMarkup = \\markup {{ }}
    oddHeaderMarkup = \\markup {{ }}
}}

#(set-global-staff-size 26)

\\score {{
    {lilypond_code}
    \\layout {{
        \\context {{
            \\Score
            \\override SpacingSpanner.base-shortest-duration = #(ly:make-moment 1/8)
        }}
    }}
}}
"""
    
    def _resize_image(self, image_path: str, target_height: int) -> str:
        """Resize image to target height while maintaining aspect ratio"""
        try:
            with Image.open(image_path) as img:
                # Calculate new width to maintain aspect ratio
                aspect_ratio = img.width / img.height
                new_width = int(target_height * aspect_ratio)
                
                # Resize image
                resized_img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                resized_path = image_path.replace('.png', f'_resized_{target_height}.png')
                resized_img.save(resized_path, 'PNG')
                
                print(f"📐 Resized from {img.width}x{img.height} to ({new_width}, {target_height})")
                return resized_path
                
        except Exception as e:
            print(f"❌ Error resizing image: {e}")
            return image_path
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith('notation_') and file.endswith(('.ly', '.png')):
                    file_path = os.path.join(self.temp_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Warning: Could not cleanup temp files: {e}")

# Test the image renderer
if __name__ == "__main__":
    import abjad
    
    # Create a test staff
    staff = abjad.Staff()
    staff.append(abjad.Note('c4'))
    staff.append(abjad.Note('d4'))
    staff.append(abjad.Note('e4'))
    
    # Test rendering
    renderer = ImageRenderer()
    result = renderer.render_staff_to_image(staff)
    
    if result.get('success'):
        print(f"✅ Successfully rendered image: {result['image_path']}")
    else:
        print(f"❌ Failed to render image: {result.get('error')}")
