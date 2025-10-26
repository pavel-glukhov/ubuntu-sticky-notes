# Ubuntu Sticky Notes

Simple sticky notes application built with Python and PyQt6 for Ubuntu.

Version: 1.3.1
_______________

![example of app](https://github.com/pavel-glukhov/ubuntu_sticky_notes/blob/main/pic/example_1.3.0.png)

## ✨ Features

- 📝 **Sticky Notes**  
  Create, edit, move and resize notes that are automatically saved.

- 🎨 **Customization**  
  Change background colors and format text (bold, italic, strikethrough, bullet lists).

- 📌 **Pin on Top**  
  Keep individual notes or all notes always visible above other windows.

- 🔍 **Searchable List**  
  Manage all notes in a searchable list with quick open and color change options.

- 🗑 **Trash Bin**  
  Deleted notes go to Trash where they can be restored or permanently removed.

- 🖥 **System Tray Integration**  
  Quick access to show/hide notes, open all at once, or exit the app.

- 💾 **Persistent Storage**  
  Notes and settings are stored in a local SQLite database.


## Download:
You can download deb packet here:
https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/tag/1.3.1
______________________________________________________________________________________
## Installation:
```bash
curl -O -L https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/1.3.1/ubuntu-sticky-notes_1.3.1_all.deb
sudo apt update
sudo apt install -y python3-pyqt6
sudo dpkg -i ubuntu-sticky-notes_1.3.1_all.deb
```

### ⚠️ Important
> This application will start in the system tray. 
![example of app](https://github.com/pavel-glukhov/ubuntu-sticky-notes/tree/main/pic/tray_example.png)
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
```

## Usage
Run the application after installation to start creating and managing sticky notes.
