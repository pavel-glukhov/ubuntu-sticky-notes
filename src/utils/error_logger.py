"""Error logging system for Ubuntu Sticky Notes.

Provides centralized error tracking with rotation and categorization.
Implements singleton pattern for consistent logging across the application.
"""

from __future__ import annotations
import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timedelta
import platform
from typing import Optional, Dict, List, Tuple

# Constants
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
LOG_BACKUP_COUNT = 5  # Keep 5 backup files (~60MB total)
LOG_RETENTION_DAYS = 30  # Delete logs older than 30 days


class ErrorLogger:
    """Centralized error logging with rotation and detailed context.
    
    Implements singleton pattern to ensure one logger instance across the app.
    Automatically rotates log files and cleans up old logs.
    """
    
    _instance: Optional[ErrorLogger] = None
    _initialized: bool = False
    
    def __new__(cls) -> ErrorLogger:
        if cls._instance is None:
            cls._instance = super(ErrorLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ErrorLogger._initialized:
            return
            
        # Create log directory
        self.log_dir = Path.home() / '.local' / 'share' / 'ubuntu-sticky-notes'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / 'errors.log'
        
        # Setup logger
        self.logger = logging.getLogger('UbuntuStickyNotes')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=MAX_LOG_FILE_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for development (only warnings and errors)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        ErrorLogger._initialized = True
        
        # Log system info on startup
        self._log_system_info()
        
        # Clean up old log files (older than 30 days)
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        """Remove log backup files older than 30 days."""
        try:
            import time
            from datetime import datetime, timedelta
            
            # Get current time
            now = time.time()
            cutoff = now - (30 * 24 * 60 * 60)  # 30 days in seconds
            
            # Check all backup files
            for i in range(1, 10):  # Check .1 through .9
                backup_file = Path(str(self.log_file) + f'.{i}')
                if backup_file.exists():
                    file_mtime = backup_file.stat().st_mtime
                    if file_mtime < cutoff:
                        backup_file.unlink()
                        self.logger.info(f"Cleaned up old log file: {backup_file.name} (age: {int((now - file_mtime) / 86400)} days)")
        except Exception as e:
            # Don't fail startup if cleanup fails
            self.logger.warning(f"Failed to cleanup old logs: {e}")
    
    def _log_system_info(self):
        """Log system information for debugging context."""
        self.logger.info("=" * 80)
        self.logger.info("Ubuntu Sticky Notes - Session Started")
        self.logger.info(f"Python Version: {sys.version}")
        self.logger.info(f"Platform: {platform.platform()}")
        self.logger.info(f"GTK Version: {self._get_gtk_version()}")
        self.logger.info(f"Log File: {self.log_file}")
        self.logger.info("=" * 80)
    
    def _get_gtk_version(self):
        """Get GTK version safely."""
        try:
            import gi
            gi.require_version('Gtk', '4.0')
            from gi.repository import Gtk
            return f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        except Exception:
            return "Unknown"
    
    def debug(self, message, **context):
        """Log debug information with optional context."""
        self.logger.debug(self._format_message(message, context))
    
    def info(self, message, **context):
        """Log informational message with optional context."""
        self.logger.info(self._format_message(message, context))
    
    def warning(self, message, **context):
        """Log warning with optional context."""
        self.logger.warning(self._format_message(message, context))
    
    def error(self, message, exception=None, **context):
        """Log error with optional exception and context."""
        msg = self._format_message(message, context)
        
        if exception:
            msg += f"\nException: {type(exception).__name__}: {str(exception)}"
            msg += f"\nTraceback:\n{traceback.format_exc()}"
        
        self.logger.error(msg)
    
    def critical(self, message, exception=None, **context):
        """Log critical error with optional exception and context."""
        msg = self._format_message(message, context)
        
        if exception:
            msg += f"\nException: {type(exception).__name__}: {str(exception)}"
            msg += f"\nTraceback:\n{traceback.format_exc()}"
        
        self.logger.critical(msg)
    
    def log_performance(self, operation, duration, **context):
        """Log performance metrics for operations."""
        context['duration_ms'] = f"{duration * 1000:.2f}"
        self.info(f"Performance: {operation}", **context)
    
    def log_freeze_warning(self, operation, details):
        """Specific logging for potential freeze scenarios."""
        self.warning(
            f"POTENTIAL FREEZE: {operation}",
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def _format_message(self, message, context):
        """Format message with context data."""
        if not context:
            return message
        
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        return f"{message} | {context_str}"
    
    def get_log_path(self):
        """Return the path to the error log file."""
        return str(self.log_file)
    
    def get_log_size_info(self):
        """Get information about log file sizes."""
        try:
            total_size = 0
            file_count = 0
            
            # Main log file
            if self.log_file.exists():
                total_size += self.log_file.stat().st_size
                file_count += 1
            
            # Backup files
            for i in range(1, 10):
                backup_file = Path(str(self.log_file) + f'.{i}')
                if backup_file.exists():
                    total_size += backup_file.stat().st_size
                    file_count += 1
            
            return {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'main_file': str(self.log_file) if self.log_file.exists() else None
            }
        except Exception:
            return {
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'file_count': 0,
                'main_file': None
            }
    
    def get_recent_logs(self, lines=100):
        """Get recent log entries."""
        try:
            if not self.log_file.exists():
                return "No log file found."
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent)
        except Exception as e:
            return f"Error reading log file: {e}"


# Singleton instance
error_logger = ErrorLogger()


# Convenience functions
def log_debug(message, **context):
    """Log debug message."""
    error_logger.debug(message, **context)


def log_info(message, **context):
    """Log info message."""
    error_logger.info(message, **context)


def log_warning(message, **context):
    """Log warning message."""
    error_logger.warning(message, **context)


def log_error(message, exception=None, **context):
    """Log error message."""
    error_logger.error(message, exception=exception, **context)


def log_critical(message, exception=None, **context):
    """Log critical error message."""
    error_logger.critical(message, exception=exception, **context)


def log_performance(operation, duration, **context):
    """Log performance metrics."""
    error_logger.log_performance(operation, duration, **context)


def log_freeze_warning(operation, details):
    """Log potential freeze scenario."""
    error_logger.log_freeze_warning(operation, details)


def get_log_path():
    """Get error log file path."""
    return error_logger.get_log_path()


def get_log_size_info():
    """Get log file size information."""
    return error_logger.get_log_size_info()


def get_recent_logs(lines=100):
    """Get recent log entries."""
    return error_logger.get_recent_logs(lines)
