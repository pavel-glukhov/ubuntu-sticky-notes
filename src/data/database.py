"""SQLite database handler for sticky notes application.

This module provides the NotesDB class for managing sticky notes data,
including CRUD operations, trash management, and user settings.
"""

from __future__ import annotations
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.config import get_app_paths

paths = get_app_paths()
DB_PATH = paths["DB_PATH"]

# Default window dimensions and position
DEFAULT_X = 300
DEFAULT_Y = 200
DEFAULT_WIDTH = 260
DEFAULT_HEIGHT = 200
DEFAULT_COLOR = "#FFF59D"


class NotesDB:
    """
    SQLite database handler for sticky notes.

    Provides methods to add, update, delete, restore, query notes,
    and manage simple key-value settings.
    """

    def __init__(self, path=DB_PATH):
        """
        Initialize the NotesDB instance.

        - Connects to the SQLite database.
        - Creates or updates tables if they do not exist.
        - Ensures default settings are set (e.g., always_on_top).

        Args:
            path (str): Path to the SQLite database file. Defaults to DB_PATH.
        """
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        if self.get_setting("always_on_top") is None:
            self.set_setting("always_on_top", "0")

    def _create_table(self):
        """Create or migrate the database schema.

        Creates tables if they don't exist, and adds missing columns
        to existing tables for backward compatibility.
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    x INTEGER,
                    y INTEGER,
                    w INTEGER,
                    h INTEGER,
                    color TEXT DEFAULT '#FFF59D',
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    always_on_top INTEGER DEFAULT 0,
                    is_open INTEGER DEFAULT 0
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            cur = self.conn.execute("PRAGMA table_info(notes)")
            columns = [row[1] for row in cur.fetchall()]

            # Add missing columns for backward compatibility with old databases
            if "title" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN title TEXT")
            if "always_on_top" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN always_on_top INTEGER DEFAULT 0")
            if "is_open" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN is_open INTEGER DEFAULT 0")
            if "deleted" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN deleted INTEGER DEFAULT 0")
            if "deleted_at" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN deleted_at TEXT")
            if "created_at" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN created_at TEXT")
            if "updated_at" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN updated_at TEXT")
            
            # Populate timestamps for existing notes that lack them
            now = datetime.now().isoformat()
            self.conn.execute("UPDATE notes SET created_at = ? WHERE created_at IS NULL", (now,))
            self.conn.execute("UPDATE notes SET updated_at = ? WHERE updated_at IS NULL", (now,))

    def add(
        self,
        title: Optional[str] = None,
        content: str = "",
        x: int = DEFAULT_X,
        y: int = DEFAULT_Y,
        w: int = DEFAULT_WIDTH,
        h: int = DEFAULT_HEIGHT,
        color: str = DEFAULT_COLOR,
        always_on_top: int = 0
    ) -> int:
        """Insert a new sticky note into the database.

        Args:
            title: Title of the note. If None, auto-generates "Sticker N".
            content: Initial HTML/text content.
            x, y, w, h: Position and dimensions of the note window.
            color: Background color in HEX format.
            always_on_top: Whether the note is pinned on top (0 or 1).

        Returns:
            The newly created note's ID.
        """
        if title is None:
            cur = self.conn.execute("SELECT COUNT(*) FROM notes")
            count = cur.fetchone()[0]
            title = f"Sticker {count + 1}"
        
        now = datetime.now().isoformat()
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(title, content, x, y, w, h, color, always_on_top, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, content, x, y, w, h, color, always_on_top, now, now)
            )
            return cur.lastrowid


    def update(self, note_id, content, x, y, w, h, color, always_on_top=0):
        """
        Update an existing sticky note by ID.

        Args:
            note_id (int): ID of the note to update.
            content (str): Updated HTML/text content.
            x, y, w, h (int): Updated position and dimensions.
            color (str): Updated HEX color.
            always_on_top (int): Whether the note is pinned on top.
        """
        now = datetime.now().isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=?, updated_at=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, now, note_id)
            )

    def get(self, note_id):
        """
        Fetch a single note by ID.

        Args:
            note_id (int): Note ID.

        Returns:
            sqlite3.Row | None: Row representing the note, or None if not found.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self, full=False):
        """
        Retrieve all active (non-deleted) notes.

        Args:
            full (bool): If True, returns all fields including dates.
                         If False, returns only id and title.

        Returns:
            list[sqlite3.Row]: List of active notes.
        """
        if full:
            query = "SELECT id, title, color, content, created_at, updated_at FROM notes WHERE deleted = 0 ORDER BY id DESC"
        else:
            query = "SELECT id, title FROM notes WHERE deleted = 0 ORDER BY id DESC"
        return self.conn.execute(query).fetchall()

    def move_to_trash(self, note_id):
        """
        Soft-delete a note (mark as deleted and set a timestamp).

        Args:
            note_id (int): Note ID to trash.
        """
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        """
        Retrieve all notes currently in the trash.

        Returns:
            list[sqlite3.Row]: List of trashed notes.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        """
        Restore a note from trash back to active state.

        Args:
            note_id (int): Note ID to restore.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        """
        Permanently delete a note from the database.

        Args:
            note_id (int): Note ID to remove.
        """
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def get_setting(self, key):
        """
        Retrieve a setting value by key.

        Args:
            key (str): Setting key.

        Returns:
            str | None: Setting value, or None if not found.
        """
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        """
        Insert or update a setting in the settings table.

        Args:
            key (str): Setting key.
            value (str): Setting value.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value)
            )

    def set_open_state(self, note_id, state: int):
        """
        Persist whether a note is open or closed.

        Args:
            note_id (int): Note ID.
            state (int): 1 if open, 0 if closed.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self):
        """
        Retrieve all notes that were open in the last session.

        Returns:
            list[int]: List of note IDs that are currently marked as open and not deleted.
        """
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]

    def update_title(self, note_id: int, title: str):
        """
        Update the title of a note.

        Args:
            note_id (int): Note ID.
            title (str): New title string.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))
