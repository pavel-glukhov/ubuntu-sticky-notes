# Ubuntu Sticky Notes

Simple sticky notes application built with Python and PyQt5 for Ubuntu.

Version: 1.1.0
_______________

![example of app](https://github.com/pavel-glukhov/ubuntu_sticky_notes/blob/main/pic/example_1.1.0.png)

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

- ℹ️ **About Dialog**  
  Displays app info, version, author, and license.


## Download:
You can download deb packet here:
https://github.com/pavel-glukhov/ubuntu_sticky_notes/releases/tag/1.1.0

## Installation:


```bash
    sudo apt update
    sudo apt install -y python3-pyqt5
    curl -L -o ubuntu-sticky-notes.deb https://github.com/pavel-glukhov/ubuntu_sticky_notes/releases/download/1.1.0/ubuntu-sticky-notes-1.1.0.deb \
        && sudo apt install ./ubuntu-sticky-notes.deb -y
```
## Usage
Run the application after installation to start creating and managing sticky notes.
