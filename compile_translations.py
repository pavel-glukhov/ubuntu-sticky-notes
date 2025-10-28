#!/usr/bin/env python3
"""
Compile .po files to .mo files for gettext
"""
import os
import subprocess
from pathlib import Path

LOCALE_DIR = Path(__file__).parent / "locale"

def compile_translations():
    """Compile all .po files to .mo files"""
    po_files = list(LOCALE_DIR.glob("*.po"))
    
    if not po_files:
        print("No .po files found in locale directory")
        return
    
    for po_file in po_files:
        lang = po_file.stem  # Get filename without extension (e.g., 'tr', 'en')
        mo_dir = LOCALE_DIR / lang / "LC_MESSAGES"
        mo_dir.mkdir(parents=True, exist_ok=True)
        
        mo_file = mo_dir / "ubuntu-sticky-notes.mo"
        
        print(f"Compiling {po_file.name} → {mo_file.relative_to(LOCALE_DIR)}")
        
        try:
            # Use msgfmt to compile .po to .mo
            result = subprocess.run(
                ["msgfmt", str(po_file), "-o", str(mo_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"  ✓ Success")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error: {e.stderr}")
        except FileNotFoundError:
            print("  ✗ Error: msgfmt not found. Install gettext package:")
            print("    sudo apt install gettext")
            break

if __name__ == "__main__":
    print("Ubuntu Sticky Notes - Translation Compiler")
    print("=" * 50)
    compile_translations()
    print("\nDone!")
