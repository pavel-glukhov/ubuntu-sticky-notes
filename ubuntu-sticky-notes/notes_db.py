import sqlite3
from datetime import datetime
from config import get_app_paths

paths = get_app_paths()
DB_PATH = paths["DB_PATH"]


class NotesDB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        if self.get_setting("always_on_top") is None:
            self.set_setting("always_on_top", "0")

    def _create_table(self):
        """
        Создает таблицы и обновляет структуру (миграции).
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

            # МИГРАЦИИ: Проверяем, есть ли колонки, и добавляем, если нет
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

            # === ДОБАВЛЕНО: Миграция для координат и размеров ===
            if "x" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN x INTEGER DEFAULT 0")
            if "y" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN y INTEGER DEFAULT 0")
            if "w" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN w INTEGER DEFAULT 300")
            if "h" not in columns:
                self.conn.execute("ALTER TABLE notes ADD COLUMN h INTEGER DEFAULT 300")

    def add(self, title=None, content="", x=300, y=200, w=260, h=200, color="#FFF59D", always_on_top=0):
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
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
            )

    def get(self, note_id):
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self, full=False):
        if full:
            query = "SELECT id, title, color, content FROM notes WHERE deleted = 0 ORDER BY id DESC"
        else:
            query = "SELECT id, title FROM notes WHERE deleted = 0 ORDER BY id DESC"
        return self.conn.execute(query).fetchall()

    def move_to_trash(self, note_id):
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def get_setting(self, key):
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value)
            )

    def update_color(self, note_id: int, color: str):
        with self.conn:
            self.conn.execute("UPDATE notes SET color = ? WHERE id = ?", (color, note_id))

    def set_open_state(self, note_id, state: int):
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self):
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]

    def update_title(self, note_id: int, title: str):
        with self.conn:
            self.conn.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))

    def set_always_on_top(self, note_id: int, state: int):
        with self.conn:
            self.conn.execute("UPDATE notes SET always_on_top = ? WHERE id = ?", (state, note_id))