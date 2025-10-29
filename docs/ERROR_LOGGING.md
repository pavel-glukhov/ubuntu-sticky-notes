# Error Logging System

## Overview

Ubuntu Sticky Notes now includes a comprehensive error logging system to help track and diagnose issues, especially recurring bugs like the freeze problem.

## Quick Summary

- 📁 **Location**: `~/.local/share/ubuntu-sticky-notes/errors.log`
- 💾 **Max Size**: 60 MB total (10 MB per file, 6 files max)
- 🗓️ **Auto-Cleanup**: Files older than 30 days automatically deleted
- 🔄 **Rotation**: Automatic when file reaches 10 MB
- 📊 **View in UI**: Menu → Error Log (shows size & file count)
- 🔒 **Privacy**: NO note content logged, only metadata

## Log File Location

```
~/.local/share/ubuntu-sticky-notes/errors.log
```

## Features

### 1. **Automatic Error Tracking**
- All critical operations are logged with timing information
- Exceptions are automatically captured with full stack traces
- Performance metrics for slow operations

### 2. **Categorized Logging**
- **INFO**: Normal operations (window creation, note loading, autosave)
- **WARNING**: Performance issues, potential problems
- **ERROR**: Exceptions and failures
- **CRITICAL**: Severe errors that affect functionality

### 3. **Performance Monitoring**
- Tracks execution time for:
  - StickyWindow initialization
  - Rich text editor creation
  - Note loading from database
  - Format serialization (get_formatted_content)
  - Format deserialization (set_formatted_content)
  - Database operations
  - Autosave cycles

### 4. **Freeze Detection**
- Warns when operations take too long:
  - Window initialization > 1 second
  - Content formatting > 0.5 seconds
  - Character iteration > 2 seconds
- Logs progress every 1000 characters during tag processing

### 5. **Log Rotation**
- Maximum log file size: **10 MB** per file
- Keeps **5 backup files** (errors.log.1 through errors.log.5)
- **Total maximum size: ~60 MB** (10 MB × 6 files)
- Automatic rotation when file reaches limit
- Old backup files (older than **30 days**) are automatically deleted
- Prevents disk space issues from unlimited logging

## Accessing Logs

### Method 1: Through the UI
1. Open Ubuntu Sticky Notes
2. Click the **Menu** button (⋮)
3. Select **Error Log**
4. View log file location, size, and number of files
5. Copy to clipboard or save the log

The UI displays:
- **Log file location**: Full path to errors.log
- **Total size**: Combined size of all log files in MB
- **File count**: Number of log files (main + backups)

### Method 2: Direct File Access
```bash
# View recent logs
tail -100 ~/.local/share/ubuntu-sticky-notes/errors.log

# View all logs
cat ~/.local/share/ubuntu-sticky-notes/errors.log

# Search for specific errors
grep "ERROR" ~/.local/share/ubuntu-sticky-notes/errors.log

# Search for freeze warnings
grep "FREEZE" ~/.local/share/ubuntu-sticky-notes/errors.log

# Search for performance issues
grep "Performance" ~/.local/share/ubuntu-sticky-notes/errors.log
```

## What Gets Logged

### On Application Startup
```
2025-10-29 01:21:40 | INFO | Ubuntu Sticky Notes - Session Started
2025-10-29 01:21:40 | INFO | Python Version: 3.12.3
2025-10-29 01:21:40 | INFO | Platform: Linux-6.14.0-33-generic
2025-10-29 01:21:40 | INFO | GTK Version: 4.14.5
2025-10-29 01:21:40 | INFO | Log File: /home/omer/.local/share/ubuntu-sticky-notes/errors.log
```

### On Note Creation/Opening
```
2025-10-29 01:22:15 | INFO | StickyWindow.__init__ starting | note_id=42
2025-10-29 01:22:15 | INFO | Creating RichTextEditor
2025-10-29 01:22:15 | INFO | Performance: RichTextEditor creation | duration_ms=15.23
2025-10-29 01:22:15 | INFO | Loading note from DB | note_id=42
2025-10-29 01:22:15 | INFO | Performance: Note load from DB | duration_ms=8.45 | note_id=42
2025-10-29 01:22:15 | INFO | Performance: StickyWindow.__init__ COMPLETE | duration_ms=45.67 | note_id=42
```

### On Autosave
```
2025-10-29 01:22:20 | INFO | _save_now called | note_id=42
2025-10-29 01:22:20 | INFO | Performance: get_formatted_content in _save_now | duration_ms=12.34 | content_length=256 | note_id=42
2025-10-29 01:22:20 | INFO | Updating existing note | note_id=42
2025-10-29 01:22:20 | INFO | Performance: Database update | duration_ms=3.21 | note_id=42
2025-10-29 01:22:20 | INFO | Performance: _save_now total | duration_ms=18.76 | note_id=42
```

### On Errors
```
2025-10-29 01:23:45 | ERROR | Error in get_formatted_content | text_length=5234
Exception: IndexError: string index out of range
Traceback:
  File "/path/to/rich_text_editor.py", line 123, in get_formatted_content
    char = text[index]
IndexError: string index out of range
```

### On Freeze Detection
```
2025-10-29 01:24:10 | WARNING | POTENTIAL FREEZE: get_formatted_content slow | details={'char_count': 1500, 'max_chars': 5000, 'elapsed_seconds': '2.15', 'tags_found': 45}
```

## Bug Reporting

When reporting bugs, especially freeze or crash issues:

1. **Access the error log** via Menu → Error Log
2. **Copy to clipboard** using the Copy button
3. **Paste the log** into your bug report
4. Include:
   - What you were doing when the issue occurred
   - How to reproduce the problem
   - The relevant portion of the error log

The log file contains:
- System information (Python version, GTK version, platform)
- Timing information (helps identify slow operations)
- Exception stack traces (helps identify code issues)
- Performance metrics (helps identify bottlenecks)

## Privacy Note

The error log contains:
- ✅ System information (Python version, platform)
- ✅ Performance metrics (timing, character counts)
- ✅ Error messages and stack traces
- ✅ Note IDs (numerical identifiers)
- ❌ **NO** note content (your actual text is never logged)
- ❌ **NO** personal information

The log is safe to share for debugging purposes.

## For Developers

### Using the Logger

```python
from src.utils.error_logger import log_info, log_error, log_performance, log_freeze_warning

# Log informational messages
log_info("Operation started", note_id=42, operation="save")

# Log errors with exceptions
try:
    risky_operation()
except Exception as e:
    log_error("Operation failed", exception=e, note_id=42)

# Log performance metrics
import time
start = time.time()
do_work()
log_performance("Operation name", time.time() - start, note_id=42, items_processed=100)

# Log potential freeze scenarios
log_freeze_warning("Long operation detected", {
    "duration_seconds": "3.45",
    "note_id": 42,
    "items_count": 1000
})
```

### Logger Configuration

Location: `src/utils/error_logger.py`

Settings:
- Max file size: **10 MB** per file
- Backup count: **5** files (total ~60 MB)
- Auto-cleanup: Files older than **30 days**
- Log level: DEBUG (file), WARNING (console)
- Format: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`

**Disk space guarantee**: Log files will never exceed 60 MB total, and old files are automatically cleaned up after 30 days.

## Troubleshooting

### Log file too large?
The rotation system automatically manages this:
- Each log file is limited to 10 MB
- Maximum 6 files total (~60 MB)
- Files older than 30 days are automatically deleted
- Old logs are moved to:
  - `errors.log.1` (most recent backup)
  - `errors.log.2`
  - `errors.log.3`
  - `errors.log.4`
  - `errors.log.5` (oldest backup)

When errors.log reaches 10 MB:
1. errors.log.5 is deleted (if exists)
2. errors.log.4 → errors.log.5
3. errors.log.3 → errors.log.4
4. errors.log.2 → errors.log.3
5. errors.log.1 → errors.log.2
6. errors.log → errors.log.1
7. New errors.log is created

### Can't find the log file?
Check: `~/.local/share/ubuntu-sticky-notes/errors.log`

If it doesn't exist, the application may not have been started since the error logging system was added.

### How to clear the log?
```bash
rm ~/.local/share/ubuntu-sticky-notes/errors.log*
```
A new log will be created next time the application starts.

## Future Improvements

Potential enhancements:
- [ ] Export logs as text file
- [ ] Filter logs by severity level in UI
- [ ] Search functionality in log viewer
- [ ] Automatic bug report generation
- [ ] Email logs directly from the app
- [ ] Integration with crash reporters

---

**Note**: This logging system was added to help diagnose the recurring freeze bug and other issues. It provides detailed insight into application behavior without compromising note privacy.
