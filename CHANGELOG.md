# Changelog

All notable changes to Ubuntu Sticky Notes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-29

### 🌍 Added - Internationalization
- **10-language support**: English, Turkish, Spanish, French, German, Russian, Chinese, Hindi, Arabic, Bengali
- Language selection menu in main window
- Persistent language preference (saved in database)
- Dynamic UI label translation
- Translation compilation system (`compile_translations.py`)
- Reaches 4+ billion users worldwide

### 📝 Added - Error Logging System
- Comprehensive error logging with rotating file handler
- Automatic log rotation (10MB per file, 5 backup files maximum)
- 30-day automatic cleanup of old log files
- Performance monitoring for critical operations
- Freeze detection with detailed warnings (>1 second operations)
- UI-based log viewer (Menu → Error Log)
- Copy-to-clipboard functionality
- Log file size display in UI
- Privacy-focused: note content never logged, only metadata
- System information logged on startup (Python version, GTK version, platform)

### 🎨 Added - UI Improvements
- Modern table-based main window layout
- Three columns: Note Name, Modified Date, Created Date
- Sortable columns (6 sorting options: name/created/modified × ascending/descending)
- Rich text editor with GTK4 TextTag system
- Format toolbar with bold, italic, underline, strikethrough
- Font size selection (8-72pt)
- Text color picker
- Text alignment options (left, center, right, justify)
- Bullet lists, numbered lists, and checklists
- Format persistence via JSON serialization
- Trash window with restore and permanent delete
- Updated screenshots (pic/1.png, pic/2.png, pic/3.png)

### 📖 Added - Documentation
- Comprehensive English README for global audience
- ERROR_LOGGING.md with detailed usage guide
- Architecture overview section
- Installation instructions (system Python + venv with --system-site-packages)
- Translation guide for contributors
- Troubleshooting section
- Uninstall instructions

### 🐛 Fixed - Critical Bugs
- **MAJOR**: Fixed chronic freeze bug when creating notes with Enter key
  - Root cause: GTK event loop deadlock between dialog response and window creation
  - Solution: Close dialog first, then use GLib.timeout_add() to defer window creation
- Fixed duplicate window opening issues
- Fixed infinite loop in tag iteration (added 10,000 character safety limit)
- Fixed title display in sticky windows
- Fixed empty buffer handling in format serialization
- Fixed tag processing for newly created empty notes

### 🔧 Changed - Database
- Added `created_at` timestamp column (immutable, set on creation)
- Added `updated_at` timestamp column (updated on edit)
- Automatic database migration for existing databases
- Timestamps stored in ISO 8601 format
- Date display in main window table

### ⚠️ Removed - Breaking Changes
- **System tray feature completely removed**
  - Removed `src/utils/status_notifier.py`
  - Removed `src/utils/system_tray.py`
  - Use main window instead of system tray icon
- Removed old screenshots (example_1.2.3.png, example_1.3.0.png, tray_example.png)
- Removed verbose debug print statements

### 🛠️ Technical Improvements
- Try-except blocks with detailed error logging in critical operations
- Performance metrics for:
  - StickyWindow initialization
  - Rich text editor creation
  - Note loading from database
  - Format serialization/deserialization
  - Database operations
  - Autosave cycles
- Character-by-character tag iteration with safety mechanisms
- Processed tags set to avoid duplicates
- Emergency breaks for runaway operations
- Context tracking (note_id, operation type, timing)

### 📊 Statistics
- 46 files changed
- +5,232 lines added
- -860 lines removed
- 10 translation files (.po/.mo) with 195+ strings each

---

## [1.x.x] - Previous Versions

### Earlier releases
- Basic sticky note functionality
- SQLite database backend
- System tray integration
- Note creation, editing, deletion
- Trash functionality
- GTK4/Libadwaita UI

---

## Release Notes

### Version 2.0.0 Highlights

This is a **major release** that transforms Ubuntu Sticky Notes into a globally accessible, production-ready application.

**Why upgrade to 2.0.0?**
1. **Global reach**: Support for 10 languages reaching 4+ billion people
2. **Reliability**: Chronic freeze bug finally solved
3. **Debugging**: Comprehensive error logging helps diagnose issues
4. **Modern UI**: Clean table layout with rich text editing
5. **Professional**: Well-documented, maintainable codebase

**Migration Notes:**
- Database will be automatically migrated to add timestamp columns
- Old notes will have `created_at` and `updated_at` set to current time
- No manual intervention required
- System tray removed - use main window instead

**Known Issues:**
- None! All critical bugs resolved in this release

**Next Steps:**
1. Download the latest release from GitHub
2. Run `python3 main.py` or install via .deb package
3. Select your language from Menu → Language
4. Enjoy a bug-free, multi-language sticky notes experience!

---

## Download

- **GitHub Release**: [v2.0.0](https://github.com/omercngiz/ubuntu-sticky-notes/releases/tag/v2.0.0)
- **Source Code**: [tar.gz](https://github.com/omercngiz/ubuntu-sticky-notes/archive/refs/tags/v2.0.0.tar.gz) | [zip](https://github.com/omercngiz/ubuntu-sticky-notes/archive/refs/tags/v2.0.0.zip)

## Contributors

Special thanks to all contributors who made this release possible!

---

**For full commit history**: https://github.com/omercngiz/ubuntu-sticky-notes/commits/main
