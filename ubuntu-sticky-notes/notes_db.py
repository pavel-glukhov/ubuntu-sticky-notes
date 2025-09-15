import sqlite3
from datetime import datetime

from config import get_app_paths

paths = get_app_paths()
DB_PATH = paths["DB_PATH"]


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
        - Creates tables if they do not exist.
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
        """
        Create the database schema if missing.

        Tables created:
            - notes: Stores all sticky note data (content, position, size, color, deleted state, etc.)
            - settings: Stores simple key-value application settings.
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    x INTEGER,
                    y INTEGER,
                    w INTEGER,
                    h INTEGER,
                    color TEXT DEFAULT '#FFF59D',
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
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

    def add(self, content="", x=300, y=200, w=260, h=200, color="#FFF59D", always_on_top=0):
        """
        Add a new sticky note to the database.

        Args:
            content (str): Initial content of the note.
            x, y, w, h (int): Position and size of the note.
            color (str): Background color in HEX.
            always_on_top (int): Whether the note is always on top (0 or 1).

        Returns:
            int: The newly created note's ID.
        """
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(content, x, y, w, h, color, always_on_top) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (content, x, y, w, h, color, always_on_top)
            )
            return cur.lastrowid

    def update(self, note_id, content, x, y, w, h, color, always_on_top=0):
        """
        Update an existing sticky note.

        Args:
            note_id (int): The ID of the note to update.
            content (str): New content.
            x, y, w, h (int): Updated position and size.
            color (str): Updated background color.
            always_on_top (int): Updated always-on-top flag (0 or 1).
        """
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
            )

    def get(self, note_id):
        """
        Retrieve a note by its ID.

        Args:
            note_id (int): Note ID to retrieve.

        Returns:
            sqlite3.Row: Row object representing the note, or None if not found.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self):
        """
        Retrieve all active (not deleted) notes.

        Returns:
            list[sqlite3.Row]: List of active notes containing id, content, and color.
        """
        cur = self.conn.execute("SELECT id, content, color FROM notes WHERE deleted=0")
        return cur.fetchall()

    def move_to_trash(self, note_id):
        """
        Mark a note as deleted (move to trash) with timestamp.

        Args:
            note_id (int): ID of the note to trash.
        """
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        """
        Retrieve all notes that are in the trash.

        Returns:
            list[sqlite3.Row]: List of notes marked as deleted.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        """
        Restore a note from trash back to active notes.

        Args:
            note_id (int): ID of the note to restore.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        """
        Permanently delete a note from the database.

        Args:
            note_id (int): ID of the note to remove.
        """
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def get_setting(self, key):
        """
        Retrieve a setting value by key.

        Args:
            key (str): Setting key.

        Returns:
            str or None: Setting value, or None if the key does not exist.
        """
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        """
        Set or update a setting in the settings table.

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
        Save whether the note is open or closed.

        Args:
            note_id (int): Note ID.
            state (int): 1 if open, 0 if closed.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self):
        """
        Retrieve all notes that were open during the last session.

        Returns:
            list[int]: List of note IDs that are currently marked as open and not deleted.
        """
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]
