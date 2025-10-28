# Ubuntu Sticky Notes

Simple sticky notes application built with Python and GTK4/libadwaita for Ubuntu.

Version: 2.0.0 (GTK4 Edition)
_______________

![example of app](https://github.com/pavel-glukhov/ubuntu_sticky_notes/blob/main/pic/example_1.3.0.png)

## ✨ Features

- 📝 **Sticky Notes**  
  Create, edit, and manage notes that are automatically saved.

- 🎨 **Customization**  
  Change background colors for better organization.

- 📌 **Pin on Top**  
  Keep individual notes visible (planned feature).

- 🔍 **Searchable List**  
  Manage all notes in a searchable list with quick access.

- 🗑 **Trash Bin**  
  Deleted notes go to Trash where they can be restored or permanently removed.

- 🖥 **Background Operation**  
  The app runs in the background when closed. Use the Quit option from the menu to exit.

- 💾 **Persistent Storage**  
  Notes and settings are stored in a local SQLite database.


## Installation

### System Requirements

```bash
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

### Running from Source

```bash
# Clone the repository
git clone https://github.com/pavel-glukhov/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes

# Run with system Python (recommended)
python3 main.py
```

### ⚠️ Important Notes

> **Background Operation:** When you close the main window, the app continues running in the background.  
> To completely exit the application, use the **Quit** option from the application menu (☰).

> **System Tray Support:** The app supports StatusNotifierItem protocol for system tray integration.  
> On Ubuntu/GNOME, you need to enable the AppIndicator extension for the tray icon to appear:
> ```bash
> sudo apt install -y gnome-shell-extension-appindicator
> gnome-extensions enable ubuntu-appindicators@ubuntu.com
> ```
> After enabling, you may need to restart GNOME Shell (Alt+F2, type 'r', press Enter) or log out and back in.  
> The system tray icon allows quick access to show/hide the main window by clicking it.


## Development (GTK4/libadwaita)

Run locally with Python 3.12+ and GTK4/libadwaita (GI bindings provided by system packages):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional; GTK comes from system packages
python main.py  # runs GTK UI by default
```

VS Code:
- Use the launch config "Run Ubuntu Sticky Notes (Refactored)" (calls main.py)
- Or Tasks: "Run Ubuntu Sticky Notes (Refactored)"

### GTK4/libadwaita preview (work-in-progress)

A new GNOME HIG-compliant UI is being implemented with GTK4/libadwaita. You can try it locally:

- Install system dependencies (Ubuntu/Debian):
  - python3-gi
  - gir1.2-gtk-4.0
  - gir1.2-adw-1

- Run with the GTK UI:
  - Temporarily via CLI flag: `python main.py --gtk`
  - Or via env var: `STICKY_NOTES_UI=gtk python main.py`

If GTK dependencies are missing, the app will automatically fall back to the existing PyQt UI.

_____________________________________________________________________________________
## Self build and Install Ubuntu Sticky Notes (.deb package)

``` bash
# Clone the repository
git clone https://github.com/pavel-glukhov/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes
# Make the script executable
chmod +x build_deb_package.sh
# Run the package build
./build_deb_package.sh
# Install the package
sudo apt install -y python3-pyqt6
sudo dpkg -i ubuntu-sticky-notes_<VERSION OF APPLICATION>_all.deb
sudo apt-get install -f
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

## Usage
Run the application after installation to start creating and managing sticky notes.
