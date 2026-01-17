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
        """
        Create or migrate the database schema.

        - If the database is new → creates `notes` with `title` and all modern fields.
        - If the database is old → validates schema via PRAGMA and
          adds missing fields via ALTER TABLE.
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

    def add(self, title=None, content="", x=300, y=200, w=260, h=200, color="#FFF59D", always_on_top=0):
        """
        Insert a new sticky note into the database.

        Args:
            title (str): Title of the note. If None, a default "Sticker N" is used.
            content (str): Initial HTML/text content.
            x, y, w, h (int): Position and dimensions of the note.
            color (str): Background color in HEX.
            always_on_top (int): Whether the note is pinned on top (0 or 1).

        Returns:
            int: The newly created note's ID.
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
        """
        Update an existing sticky note by ID.

        Args:
            note_id (int): ID of the note to update.
            content (str): Updated HTML/text content.
            x, y, w, h (int): Updated position and dimensions.
            color (str): Updated HEX color.
            always_on_top (int): Whether the note is pinned on top.
        """
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
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
            full (bool): If True, returns id, title, color, content.
                         If False, returns only id and title.

        Returns:
            list[sqlite3.Row]: List of active notes.
        """
        if full:
            query = "SELECT id, title, color, content FROM notes WHERE deleted = 0 ORDER BY id DESC"
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

    def update_color(self, note_id: int, color: str):
        """
        Update only the color of a note.

        Args:
            note_id (int): Note ID.
            color (str): New HEX color string.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET color = ? WHERE id = ?", (color, note_id))

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

    def set_always_on_top(self, note_id: int, state: int):
        """
        Set the always_on_top flag for a specific note.

        Args:
            note_id (int): Note ID.
            state (int): 1 for pinned (top), 0 for normal.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET always_on_top = ? WHERE id = ?", (state, note_id))