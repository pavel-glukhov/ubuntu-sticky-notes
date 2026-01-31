# LinSticky

Modern sticky notes application built with Python, GTK4, and Libadwaita for Linux.

Version: 2.0.0-beta3
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
> 👉 [legacy branch](https://github.com/pavel-glukhov/linsticky/tree/legacy).



![example of app](https://github.com/pavel-glukhov/linsticky/blob/gtk/pic/example_2.0.0.png)

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
Use the app in multiple languages, including:
  - English
  - Русский
  - Español
  - Deutsch
  - Français
  - 简体中文
  - Português (Brasil)
  - Türkçe
  - Қазақша
- 🖥️ Modern GNOME Experience
A refreshed interface that follows current GNOME / Adwaita design guidelines for a native look and feel.

## Download:
You can download the beta deb package here:
https://github.com/pavel-glukhov/linsticky/releases/tag/v2.0.0-beta3
______________________________________________________________________________________

## Installation:

To install version 2.0.0-beta3, run the following commands in your terminal:

```bash
# 1. Download the package
curl -O -L https://github.com/pavel-glukhov/linsticky/releases/download/v2.0.0-beta3/linsticky_2.0.0-beta3_all.deb

# 2. Update and install system dependencies (GTK4 & Libadwaita)
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gettext

# 3. Install the package
sudo dpkg -i linsticky_2.0.0-beta3_all.deb
sudo apt-get install -f
```
## Troubleshooting Localization

If the app's language doesn't change after selection:
1.  **Install Language Pack:**
2. ```sh
    sudo apt install language-pack-[lang_code] 
    ```
2.  **Generate Locale:**
    ```sh
    sudo locale-gen [lang_code].UTF-8 
    ```
3.  **Restart:** Restart the application.

Check available locales: `locale -a`

## 🛠️ Backend & Positioning

By default, the app runs on Wayland. If you want your notes to remember their exact screen coordinates (X/Y), 
open Settings within the app, switch the backend to X11, and restart the application.

## Self build and Install (.deb package)

If you want to build the package from source:
```bash
# Clone the repository
git clone [https://github.com/pavel-glukhov/linsticky.git](https://github.com/pavel-glukhov/linsticky.git)
cd linsticky

# Make the script executable
chmod +x build_deb_package.sh

# Run the package build
./build_deb_package.sh

# Install the generated package
sudo apt install ./linsticky_<VERSION>_all.deb
```

## Credits

- Author: Pavel Glukhov
- Email: glukhov.p@gmail.com
- License: MIT License
