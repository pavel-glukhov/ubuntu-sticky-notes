#!/usr/bin/env python3
"""
Ubuntu Sticky Notes Application Entry Point (GTK/libadwaita)

Adds the src directory to sys.path and launches the GTK application.
If GTK GI bindings are missing, prints installation instructions and exits.
"""

import os
import sys


def _ensure_src_on_path():
	current_dir = os.path.dirname(os.path.abspath(__file__))
	src_path = os.path.join(current_dir, "src")
	if src_path not in sys.path:
		sys.path.insert(0, src_path)


def main():
	_ensure_src_on_path()
	
	# Initialize i18n
	try:
		from core.i18n import init_translation
		init_translation()
	except Exception as e:
		print(f"Warning: Failed to initialize translations: {e}", file=sys.stderr)
	
	try:
		import gi
		gi.require_version("Gtk", "4.0")
		gi.require_version("Adw", "1")
		from gi.repository import Gtk, Adw
	except ImportError as e:
		msg = (
			"GTK4/libadwaita bindings are required but not found.\n"
			f"Import error: {e}\n\n"
			"IMPORTANT: PyGObject (gi) requires system packages and cannot be installed via pip in a venv.\n\n"
			"Please run this application using the system Python with these packages installed:\n"
			"  1. Install system packages:\n"
			"     sudo apt update\n"
			"     sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1\n\n"
			"  2. Run the application with system Python (not venv):\n"
			"     python3 main.py\n\n"
			"Or alternatively, use --system-site-packages when creating your venv:\n"
			"  python3 -m venv --system-site-packages .venv\n"
			"  source .venv/bin/activate\n"
			"  python main.py\n"
		)
		print(msg, file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"Unexpected error during import: {e}", file=sys.stderr)
		sys.exit(1)
	
	try:
		from gtk_app.gtk_application import main as gtk_main
		return gtk_main()
	except Exception as e:
		import traceback
		print(f"Error starting application: {e}", file=sys.stderr)
		traceback.print_exc()
		sys.exit(1)


if __name__ == "__main__":
	main()
