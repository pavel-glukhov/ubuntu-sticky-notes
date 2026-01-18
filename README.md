# Ubuntu Sticky Notes

Modern sticky notes application built with Python, GTK4, and Libadwaita for Ubuntu.

Version: 2.0.0-beta
_______________

> [!IMPORTANT]
> **This is the new GTK4/Libadwaita version.**
> If you are looking for the original PyQt6 version (v1.4.1), please switch to the [legacy branch](https://github.com/pavel-glukhov/ubuntu-sticky-notes/tree/legacy).

![example of app](https://github.com/pavel-glukhov/ubuntu-sticky-notes/blob/main/pic/example_2.0.0.png)

## ✨ Features

- 📝 **Modern UI** Built with **GTK4** and **Libadwaita** for a native GNOME look and feel with smooth animations and adaptive design.

- 🎨 **Rich Customization** Change background colors and format text (bold, italic, underline, strikethrough, custom text colors, and various font sizes).

- 🖥️ **Wayland & X11 Support** Native Wayland support for modern Ubuntu versions, with an optional X11 mode for precise window position saving.

- 📌 **Always on Top** Keep notes visible above other windows (supported via XWayland/X11 mode).

- ⚙️ **Advanced Settings** Easily switch display backends (Wayland/X11) and customize the SQLite database location directly from the UI.

- 🗑 **Trash Bin** Manage deleted notes in a dedicated view where they can be restored or permanently erased.

- 🖥 **Isolated System Tray** A stable tray icon running in a background process for quick access to all notes.

- 💾 **Persistent Storage** Uses SQLite for data. Configuration is stored in `~/.config/ubuntu-sticky-notes/usn.conf`.


## Download:
You can download the beta deb package here:
https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/2.0.0-beta/ubuntu-sticky-notes_2.0.0-beta_all.deb
______________________________________________________________________________________

## Installation:

To install version 2.0.0-beta, run the following commands in your terminal:

```bash
# 1. Download the package
curl -O -L [https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/2.0.0-beta/ubuntu-sticky-notes_2.0.0-beta_all.deb](https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/2.0.0-beta/ubuntu-sticky-notes_2.0.0-beta_all.deb)

# 2. Update and install system dependencies (GTK4 & Libadwaita)
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1

# 3. Install the package
sudo dpkg -i ubuntu-sticky-notes_2.0.0-beta_all.deb
sudo apt-get install -f
```

## 🛠️ Backend & Positioning

By default, the app runs on Wayland. If you want your notes to remember their exact screen coordinates (X/Y), 
open Settings within the app, switch the backend to X11, and restart the application.

## Self build and Install (.deb package)

If you want to build the package from source:
```bash
# Clone the repository
git clone [https://github.com/pavel-glukhov/ubuntu-sticky-notes.git](https://github.com/pavel-glukhov/ubuntu-sticky-notes.git)
cd ubuntu-sticky-notes

# Make the script executable
chmod +x build_deb_package.sh

# Run the package build
./build_deb_package.sh

# Install the generated package
sudo apt install ./ubuntu-sticky-notes_<VERSION>_all.deb
```

## Credits

- Author: Pavel Glukhov
- Email: glukhov.p@gmail.com
- License: MIT License