import sqlite3
from datetime import datetime
from config.config import get_app_paths
from config.config_manager import ConfigManager


class NotesDB:
    """Manages the SQLite database for sticky notes."""

    def __init__(self, path: str):
        """
        Initializes the database connection and ensures tables are created.
        Args:
            path (str): The absolute path to the SQLite database file.
        """
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def _create_table(self):
        """
        Creates necessary tables and performs schema migrations if needed.
        """
        with self.conn:
            self.conn.execute("""
                              CREATE TABLE IF NOT EXISTS notes
                              (
                                  id INTEGER PRIMARY KEY,
                                  title TEXT,
                                  content TEXT,
                                  x INTEGER DEFAULT 0,
                                  y INTEGER DEFAULT 0,
                                  w INTEGER DEFAULT 300,
                                  h INTEGER DEFAULT 300,
                                  color TEXT DEFAULT '#FFF59D',
                                  deleted INTEGER DEFAULT 0,
                                  deleted_at TEXT,
                                  always_on_top INTEGER DEFAULT 0,
                                  is_open INTEGER DEFAULT 0,
                                  is_pinned INTEGER DEFAULT 0
                              )
                              """)

            # Migrations
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
            if "is_pinned" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN is_pinned INTEGER DEFAULT 0")

    def add(self, title: str = None, content: str = "",
            x: int = 300, y: int = 200,
            w: int = 260, h: int = 200,
            color: str = "#FFF59D",
            always_on_top: int = 0) -> int:
        """
        Adds a new note to the database.
        Args:
            title (str, optional): The title of the note. Defaults to "Sticker X".
            content (str, optional): The content of the note. Defaults to "".
            x (int, optional): X-coordinate of the note window. Defaults to 300.
            y (int, optional): Y-coordinate of the note window. Defaults to 200.
            w (int, optional): Width of the note window. Defaults to 260.
            h (int, optional): Height of the note window. Defaults to 200.
            color (str, optional): Background color of the note. Defaults to "#FFF59D".
            always_on_top (int, optional): Whether the note is always on top (0 or 1). Defaults to 0.
        Returns:
            int: The ID of the newly added note.
        """
        if title is None:
            cur = self.conn.execute("SELECT COUNT(*) FROM notes WHERE deleted = 0")
            count = cur.fetchone()[0]
            title = f"Sticker {count + 1}"
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(title, content, x, y, w, h, color, always_on_top) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, content, x, y, w, h, color, always_on_top)
            )
            return cur.lastrowid

    def update(self, note_id: int, content: str,
               x: int, y: int, w: int,
               h: int, color: str,
               always_on_top: int = 0):
        """
        Updates an existing note's properties in the database.
        Args:
            note_id (int): The ID of the note to update.
            content (str): The content of the note.
            x (int): X-coordinate of the note window.
            y (int): Y-coordinate of the note window.
            w (int): Width of the note window.
            h (int): Height of the note window.
            color (str): Background color of the note.
            always_on_top (int, optional): Whether the note is always on top (0 or 1). Defaults to 0.
        """
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
            )

    def get(self, note_id: int) -> sqlite3.Row:
        """
        Retrieves a single note by its ID.
        Args:
            note_id (int): The ID of the note to retrieve.
        Returns:
            sqlite3.Row: A row object representing the note, or None if not found.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self, full: bool = False) -> list[sqlite3.Row]:
        """
        Retrieves all non-deleted notes, optionally with full content.
        Args:
            full (bool, optional): If True, retrieves all columns. If False, only ID and title. Defaults to False.
        Returns:
            list[sqlite3.Row]: A list of row objects for the notes.
        """
        if full:
            query = "SELECT * FROM notes WHERE deleted = 0 ORDER BY is_pinned DESC, id DESC"
        else:
            query = "SELECT id, title FROM notes WHERE deleted = 0 ORDER BY is_pinned DESC, id DESC"
        return self.conn.execute(query).fetchall()

    def toggle_pin_status(self, note_id: int):
        """
        Toggles the 'is_pinned' status for a given note.
        Args:
            note_id (int): The ID of the note to toggle.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET is_pinned = (is_pinned - 1) * -1 WHERE id = ?", (note_id,))

    def move_to_trash(self, note_id: int):
        """
        Moves a note to the trash by setting its 'deleted' flag and 'deleted_at' timestamp.
        Args:
            note_id (int): The ID of the note to move to trash.
        """
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self) -> list[sqlite3.Row]:
        """
        Retrieves all notes currently in the trash.
        Returns:
            list[sqlite3.Row]: A list of row objects for the trashed notes.
        """
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id: int):
        """
        Restores a note from the trash.
        Args:
            note_id (int): The ID of the note to restore.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id: int):
        """
        Deletes a note permanently from the database.
        Args:
            note_id (int): The ID of the note to delete.
        """
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def update_color(self, note_id: int, color: str):
        """
        Updates the background color of a specific note.
        Args:
            note_id (int): The ID of the note to update.
            color (str): The new hexadecimal color string.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET color = ? WHERE id = ?", (color, note_id))

    def set_open_state(self, note_id: int, state: int):
        """
        Sets the open/closed state of a note.
        Args:
            note_id (int): The ID of the note.
            state (int): The state (0 for closed, 1 for open).
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self) -> list[int]:
        """
        Retrieves the IDs of all currently open and non-deleted notes.
        Returns:
            list[int]: A list of note IDs.
        """
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]

    def update_title(self, note_id: int, title: str):
        """
        Updates the title of a specific note.
        Args:
            note_id (int): The ID of the note to update.
            title (str): The new title string.
        """
        with self.conn:
            self.conn.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))