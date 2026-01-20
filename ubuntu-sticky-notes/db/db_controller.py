"""Database controller module for Ubuntu Sticky Notes.

Provides SQLite database operations for notes management including CRUD operations,
trash functionality, and settings persistence.
"""

import sqlite3
from datetime import datetime
from config.config import get_app_paths

paths = get_app_paths()
DB_PATH = paths["DB_PATH"]


class NotesDB:
    """Database controller for sticky notes.
    
    Manages all database operations including note creation, updates, deletion,
    trash management, and application settings. Uses SQLite with automatic
    schema migrations.
    
    Attributes:
        conn: SQLite database connection with row factory.
    """
    def __init__(self, path=DB_PATH):
        """Initialize database connection and create tables.
        
        Args:
            path: Path to SQLite database file.
        """
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        if self.get_setting("always_on_top") is None:
            self.set_setting("always_on_top", "0")

    def _create_table(self):
        """Create database tables and run schema migrations.
        
        Creates notes and settings tables if they don't exist, then adds
        missing columns through automatic migration checks.
        """
        with self.conn:
            self.conn.execute("""
                              CREATE TABLE IF NOT EXISTS notes
                              (
                                  id
                                  INTEGER
                                  PRIMARY
                                  KEY,
                                  title
                                  TEXT,
                                  content
                                  TEXT,
                                  x
                                  INTEGER
                                  DEFAULT
                                  0,
                                  y
                                  INTEGER
                                  DEFAULT
                                  0,
                                  w
                                  INTEGER
                                  DEFAULT
                                  300,
                                  h
                                  INTEGER
                                  DEFAULT
                                  300,
                                  color
                                  TEXT
                                  DEFAULT
                                  '#FFF59D',
                                  deleted
                                  INTEGER
                                  DEFAULT
                                  0,
                                  deleted_at
                                  TEXT,
                                  always_on_top
                                  INTEGER
                                  DEFAULT
                                  0,
                                  is_open
                                  INTEGER
                                  DEFAULT
                                  0
                              )
                              """)

            self.conn.execute("""
                              CREATE TABLE IF NOT EXISTS settings
                              (
                                  key
                                  TEXT
                                  PRIMARY
                                  KEY,
                                  value
                                  TEXT
                              )
                              """)

            # Check for missing columns and add them
            cur = self.conn.execute("PRAGMA table_info(notes)")
            columns = [row[1] for row in cur.fetchall()]

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

            if "x" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN x INTEGER DEFAULT 0")
            if "y" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN y INTEGER DEFAULT 0")
            if "w" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN w INTEGER DEFAULT 300")
            if "h" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN h INTEGER DEFAULT 300")

    def add(self, title=None, content="", x=300, y=200, w=260, h=200, color="#FFF59D", always_on_top=0):
        """Create a new note.
        
        Args:
            title: Note title. Auto-generated if None.
            content: Note content (hex-encoded JSON).
            x: X position on screen.
            y: Y position on screen.
            w: Note width.
            h: Note height.
            color: Background color (hex code).
            always_on_top: Whether note stays on top (0 or 1).
            
        Returns:
            ID of the newly created note.
        """
        if title is None:
            cur = self.conn.execute("SELECT COUNT(*) FROM notes")
            count = cur.fetchone()[0]
            title = f"Sticker {count + 1}"
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(title, content, x, y, w, h, color, always_on_top) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, content, x, y, w, h, color, always_on_top)
            )
            return cur.lastrowid

    def update(self, note_id, content, x, y, w, h, color, always_on_top=0):
        """Update note content and properties.
        
        Args:
            note_id: ID of the note to update.
            content: New content (hex-encoded JSON).
            x: X position.
            y: Y position.
            w: Width.
            h: Height.
            color: Background color.
            always_on_top: Always on top state (0 or 1).
        """
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
            )

    def get(self, note_id):
        """Get a single note by ID.
        
        Args:
            note_id: ID of the note to retrieve.
            
        Returns:
            sqlite3.Row object with note data, or None if not found.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self, full=False):
        """Get all non-deleted notes.
        
        Args:
            full: If True, includes title, color, and content. Otherwise only id and title.
            
        Returns:
            List of sqlite3.Row objects.
        """
        if full:
            query = "SELECT id, title, color, content FROM notes WHERE deleted = 0 ORDER BY id DESC"
        else:
            query = "SELECT id, title FROM notes WHERE deleted = 0 ORDER BY id DESC"
        return self.conn.execute(query).fetchall()

    def move_to_trash(self, note_id):
        """Move a note to trash.
        
        Args:
            note_id: ID of the note to delete.
        """
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        """Get all deleted notes in trash.
        
        Returns:
            List of sqlite3.Row objects.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        """Restore a note from trash.
        
        Args:
            note_id: ID of the note to restore.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        """Permanently delete a note from database.
        
        Args:
            note_id: ID of the note to delete.
        """
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def get_setting(self, key):
        """Get a setting value by key.
        
        Args:
            key: Setting key.
            
        Returns:
            Setting value as string, or None if not found.
        """
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        """Set or update a setting value.
        
        Args:
            key: Setting key.
            value: Setting value.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value)
            )

    def update_color(self, note_id: int, color: str):
        """Update note background color.
        
        Args:
            note_id: ID of the note.
            color: New color (hex code).
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET color = ? WHERE id = ?", (color, note_id))

    def set_open_state(self, note_id, state: int):
        """Set note open/closed state.
        
        Args:
            note_id: ID of the note.
            state: Open state (1 for open, 0 for closed).
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self):
        """Get IDs of all currently open notes.
        
        Returns:
            List of note IDs.
        """
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]

    def update_title(self, note_id: int, title: str):
        """Update note title.
        
        Args:
            note_id: ID of the note.
            title: New title.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))

    def set_always_on_top(self, note_id: int, state: int):
        """Set note always-on-top state.
        
        Args:
            note_id: ID of the note.
            state: Always on top state (1 for enabled, 0 for disabled).
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET always_on_top = ? WHERE id = ?", (state, note_id))