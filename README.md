# Ubuntu Sticky Notes

Modern sticky notes application built with Python, GTK4, and Libadwaita for Ubuntu.

Version: 2.0.0-beta2
_______________

> [!IMPORTANT]
> **This is the new GTK4/Libadwaita version and it is a BETA release.**  
> It is under active development and may contain bugs or incomplete features.  
>  
> ⚠️ **Backward compatibility notice:**  
> This version is **NOT compatible with stickers created in previous versions** (PyQt6 v1.x).  
> Existing stickers **will not be migrated automatically**, so please **save or export any important text in advance** before installing this version.  
>  
> If you are looking for a **stable version**, please use the original **PyQt6 version (v1.4.1)** available in the  
> 👉 [legacy branch](https://github.com/pavel-glukhov/ubuntu-sticky-notes/tree/legacy).



![example of app](https://github.com/pavel-glukhov/ubuntu-sticky-notes/blob/gtk/pic/example_2.0.0.png)

## ✨ Features

- 📝 Smart Sticky Notes
Create, edit, and organize your notes in a clean, distraction-free interface designed for daily use.
- 📌 Pinned Notes
Pin important notes to the top of the list so they are always within reach.
- 🎨 Custom Color Palette
Personalize your notes by choosing colors that match your workflow and mood.
- ✍️ Rich Text Preservation
All text formatting is reliably saved, so your notes always look exactly as intended.
- 🌍 Multilingual Support
Use the app in multiple languages, including Russian, and switch languages anytime in settings.
- 🖥️ Modern GNOME Experience
A refreshed interface that follows current GNOME / Adwaita design guidelines for a native look and feel.

## Download:
You can download the beta deb package here:
https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/v2.0.0-beta2/com.ubuntu.sticky.notes_2.0.0.beta2_all.deb
______________________________________________________________________________________

## Installation:

To install version 2.0.0-beta, run the following commands in your terminal:

```bash
# 1. Download the package
curl -O -L https://github.com/pavel-glukhov/ubuntu-sticky-notes/releases/download/v2.0.0-beta2/com.ubuntu.sticky.notes_2.0.0.beta2_all.deb

# 2. Update and install system dependencies (GTK4 & Libadwaita)
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1

# 3. Install the package
sudo dpkg -i ubuntu-sticky-notes_2.0.0.beta2_all.deb
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