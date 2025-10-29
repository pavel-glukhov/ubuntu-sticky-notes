# Ubuntu Sticky Notes v2.0.0 - Release Notes

**Release Date:** October 29, 2025  
**Tag:** v2.0.0  
**Commit:** e664d93

---

## 🎉 What's New in v2.0.0

This major release brings **Ubuntu Sticky Notes** to a production-ready, globally accessible state with professional features and rock-solid stability.

### 🌍 Multi-Language Support (10 Languages!)

Reach **4+ billion users** worldwide with native language support:

| Language | Native Name | Speakers |
|----------|-------------|----------|
| English | English | Global |
| Turkish | Türkçe | 88M |
| Spanish | Español | 559M |
| French | Français | 274M |
| German | Deutsch | 134M |
| Russian | Русский | 258M |
| Chinese | 中文 | 1.3B |
| Hindi | हिन्दी | 602M |
| Arabic | العربية | 274M |
| Bengali | বাংলা | 272M |

**Features:**
- ✅ Language selection menu in main window
- ✅ Persistent preference (survives app restart)
- ✅ Dynamic UI translation
- ✅ Professional native translations
- ✅ Easy to add more languages

---

### 📝 Comprehensive Error Logging

Never lose track of bugs again! Professional error logging system helps diagnose issues:

**Features:**
- 📊 Automatic log rotation (10MB per file, 5 backups)
- 🗓️ 30-day automatic cleanup
- ⚡ Performance monitoring
- 🔍 Freeze detection (>1 second warnings)
- 📱 UI-based viewer (Menu → Error Log)
- 📋 Copy-to-clipboard
- 🔒 Privacy-focused (note content never logged)

**Example Log:**
```
2025-10-29 01:35:20 | INFO | StickyWindow.__init__ starting | note_id=5
2025-10-29 01:35:20 | INFO | Performance: RichTextEditor creation | duration_ms=1.48
2025-10-29 01:35:22 | INFO | Performance: _save_now total | note_id=5 | duration_ms=10.95
```

---

### 🎨 Modern UI Overhaul

Beautiful, functional, and intuitive interface:

**Main Window:**
- ✨ Clean table layout (Name, Modified, Created)
- 🔽 6 sorting options
- 🗑️ Trash button for deleted notes
- 🌐 Language selection menu

**Rich Text Editor:**
- **B** Bold | _I_ Italic | <u>U</u> Underline | ~~S~~ Strikethrough
- 🎨 Text color picker
- 📏 Font size (8-72pt)
- ⬅️ Alignment (left, center, right, justify)
- • Bullet lists
- 1. Numbered lists
- ☐ Checklists

**Format Persistence:**
- All formatting saved as JSON
- Survives app restarts
- Fast serialization/deserialization

---

### 🐛 Critical Bug Fixes

#### **MAJOR: Freeze Bug Eliminated! 🎉**

**The Problem:**
- Creating a note and pressing Enter → app freezes
- Happened consistently on first note creation
- Users had to force-kill the app

**The Root Cause:**
GTK event loop deadlock:
```
Dialog activate signal → dialog.response("create")
  → on_response callback (still in dialog's event loop)
    → StickyWindow() creation (needs its own event loop)
      → DEADLOCK! 💥
```

**The Solution:**
```python
# Close dialog first
dialog.close()

# Defer window creation to next event loop iteration
GLib.timeout_add(150, open_sticky_window)
```

**Result:** ✅ Completely resolved! No more freezes!

#### **Other Fixes:**
- ✅ Duplicate window opening
- ✅ Infinite loop in tag iteration (10K char safety limit)
- ✅ Title display issues
- ✅ Empty buffer handling

---

### 📖 Professional Documentation

**New Documentation:**
- ✅ **README.md** - Comprehensive English guide
  - Feature overview
  - Architecture explanation
  - Installation instructions
  - Translation guide
  - Troubleshooting

- ✅ **ERROR_LOGGING.md** - Error logging guide
  - How to access logs
  - Log file management
  - Bug reporting guide
  - Developer usage

- ✅ **CHANGELOG.md** - Detailed version history

---

### ⚠️ Breaking Changes

#### System Tray Removed

The system tray feature has been **completely removed** for a cleaner, more focused experience.

**Why?**
- Complex implementation with minimal benefit
- Better UX with main window always accessible
- Simplified codebase

**Migration:**
- Use the main window instead of system tray icon
- No action needed - automatic migration

---

## 📊 Statistics

```
46 files changed
+5,232 lines added
-860 lines removed
10 translation files
195+ translated strings per language
```

---

## 🚀 Upgrade Guide

### For New Users

1. **Clone the repository:**
   ```bash
   git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
   cd ubuntu-sticky-notes
   ```

2. **Run the app:**
   ```bash
   python3 main.py
   ```

3. **Select your language:**
   - Menu → Language → Choose your language
   - Restart the app

### For Existing Users

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Database migration:**
   - Automatic! No action needed
   - Timestamps will be added to existing notes

3. **System tray removed:**
   - Use main window instead
   - Access via application menu

---

## 🐛 Bug Reports

Found a bug? Here's how to report it:

1. **Check error log:**
   - Menu → Error Log
   - Copy to clipboard

2. **Create GitHub issue:**
   - Include error log
   - Describe steps to reproduce
   - Include system info

3. **Fast response:**
   - With error logs, we can diagnose quickly!

---

## 🌟 What's Next?

Planned for future releases:

- [ ] Cloud sync (Nextcloud, Google Drive)
- [ ] Export/import notes
- [ ] Dark mode
- [ ] Note categories/tags
- [ ] Search across all notes
- [ ] Reminders/alarms
- [ ] Desktop widgets

---

## 🙏 Credits

### Contributors
- **omercngiz** - Project creator and maintainer

### Technologies
- **GTK4** - Modern UI framework
- **Libadwaita** - GNOME design patterns
- **Python 3** - Core language
- **SQLite** - Database backend
- **gettext** - Internationalization

### Special Thanks
- GTK/GNOME community
- Python community
- All users and contributors!

---

## 📥 Download

### Source Code
- [tar.gz](https://github.com/omercngiz/ubuntu-sticky-notes/archive/refs/tags/v2.0.0.tar.gz)
- [zip](https://github.com/omercngiz/ubuntu-sticky-notes/archive/refs/tags/v2.0.0.zip)

### Git
```bash
git clone --branch v2.0.0 https://github.com/omercngiz/ubuntu-sticky-notes.git
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub Repository:** https://github.com/omercngiz/ubuntu-sticky-notes
- **Issue Tracker:** https://github.com/omercngiz/ubuntu-sticky-notes/issues
- **Releases:** https://github.com/omercngiz/ubuntu-sticky-notes/releases

---

**Enjoy Ubuntu Sticky Notes v2.0.0! 🎉**

If you find this app useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 🌐 Contributing translations
- 📢 Sharing with others
