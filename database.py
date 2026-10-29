from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sqlite3
from contextlib import closing

database_path = Path(__file__).resolve().parent/"pomodoro.db"

def save_session_record(record):
    try:
        with closing(sqlite3.connect(database_path)) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS sessions_records (
                    id INTEGER PRIMARY KEY,
                    session_type TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    planned_seconds INTEGER NOT NULL,
                    actual_seconds REAL NOT NULL,
                    saved_at Text NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            saved_at = datetime.now(
                ZoneInfo("Asia/Kolkata")
            ).isoformat(timespec="seconds")

            cursor = connection.execute("""
                INSERT INTO sessions_records (
                    session_type,
                    outcome,
                    planned_seconds,
                    actual_seconds,
                    saved_at
                )
                Values (?, ?, ?, ?, ?)
            """,(
                record["session_type"],
                record["outcome"],
                record["planned_seconds"],
                record["actual_seconds"],
                saved_at
            ))

            connection.commit()
            return cursor.lastrowid

    except sqlite3.Error as error:
        print("Couldn't save session: ", error)
        print("Unsaved session record: ", record)
        return None

def fetch_recent_sessions(limit = 20):
    if not database_path.exists():
        return []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        # A new installation may not have a session yet.
        table_exists = connection.execute("""
              Select name
              From sqlite_master
              where type = 'table'
              AND name =  'sessions_records'
              """).fetchone()

        if table_exists is None:
            return []

        rows = connection.execute("""
            Select
            id,
            session_type,
            outcome,
            planned_seconds,
            actual_seconds,
            saved_at
            FROM sessions_records
            order by id DESC
            limit ?
            """, (limit,)).fetchall()

        return rows


def initialize_work_logs():
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                remarks TEXT NOT NULL,
                session_id INTEGER REFERENCES sessions_records(id)
            )
        """)

        columns = {
            row[1]
            for row in connection.execute(
            "PRAGMA table_info(work_logs)"
            )
        }

        if "session_id" not in columns:
            connection.execute("""
               ALTER TABLE work_logs
               ADD COLUMN session_id INTEGER
               REFERENCES sessions_records(id)
           """)

        if "task_id" not in columns:
            connection.execute(
                """
                ALTER TABLE work_logs
                ADD COLUMN task_id INTEGER REFERENCES tasks(id)
                """
            )

        connection.commit()

def fetch_sessions_notes(session_id):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        return connection.execute("""
            SELECT task, remarks
            FROM work_logs
            WHERE session_id = ?
            ORDER BY id
            """, (session_id,)).fetchall()


def fetch_today_summary():
    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()

    empty_summary = {
        "focus_seconds": 0.0,
        "completed": 0,
        "skipped": 0
    }

    if not database_path.exists():
        return empty_summary

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        table_exists = connection.execute("""
                                          SELECT name
                                          FROM sqlite_master
                                          Where type = 'table'
                                          AND name =  'sessions_records'
                                          """).fetchone()
        print("Summary database: ", database_path)
        print("Summary date: ", today)
        print("Table found: ", table_exists)

        if table_exists is None:
            return empty_summary

        rows = connection.execute("""
                    SELECT
                    COALESCE(SUM(actual_seconds),0) AS focus_seconds,
                    COUNT(
                          CASE WHEN outcome = "completed" THEN 1 END
                    ) AS completed,
                    COUNT(
                          CASE WHEN outcome = "skipped" THEN 1 END
                    ) AS skipped
                    FROM sessions_records
                    where session_type = 'focus'
                    AND date(saved_at, '+5 hours', '+30 minutes') = ?
                    """, (today,)).fetchone()

        return dict(rows)

def save_break_review(wait_id, reason, decision, extra_seconds):
    saved_at = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).isoformat(timespec='seconds')

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS break_reviews (
                wait_id TEXT PRIMARY KEY,
                reason TEXT,
                decision TEXT NOT NULL,
                extra_seconds REAL NOT NULL,
                saved_at TEXT NOT NULL
            )
       """)

        connection.execute("""
            INSERT INTO break_reviews (
            wait_id, reason, decision, extra_seconds, saved_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(wait_id) DO UPDATE SET
                reason = excluded.reason,
                decision = excluded.decision,
                extra_seconds = excluded.extra_seconds,
                saved_at = excluded.saved_at
        """,(wait_id, reason, decision, extra_seconds, saved_at))

        connection.commit()

def fetch_break_reviews(limit=20):
    if not database_path.exists():
        return []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        table_exists = connection.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'break_reviews'
        """).fetchone()

        if table_exists is None:
            return []

        return connection.execute("""
            SELECT reason, decision, extra_seconds, saved_at
            FROM break_reviews
            ORDER BY saved_at DESC, rowid DESC
            LIMIT ?
        """, (limit,)).fetchall()

def initialize_tasks():
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'completed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP 
            )
            """)
        connection.commit()

def create_task(name):
    name = name.strip()

    if not name:
        raise ValueError("Task name cannot be empty.")

    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (name) VALUES (?)",
            (name,)
        )
        connection.commit()

        return cursor.lastrowid

def get_active_tasks():
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, name
            FROM tasks
            WHERE status = ?
            ORDER BY id DESC
            """,
            ("active",)
        ).fetchall()

        return [dict(row) for row in rows]

def fetch_task_remarks(task_id):
    if task_id is None:
        return []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                w.id AS note_id,
                w.session_id,
                w.remarks,
                s.saved_at
                FROM work_logs AS w
                LEFT JOIN sessions_records AS s
                    ON s.id = w.session_id
                WHERE w.task_id = ?
                ORDER BY w.id DESC
                """, (task_id,)).fetchall()

        return [dict(row) for row in rows]

def initialize_task_notes():
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_notes (
            id INTEGER PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_task_notes_task_id
            ON task_notes (task_id)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_note_sources (
                task_note_id INTEGER NOT NULL
                    REFERENCES task_notes(id) ON DELETE CASCADE,
                work_log_id INTEGER NOT NULL
                    REFERENCES work_logs(id) ,
                PRIMARY KEY (task_note_id, work_log_id)
                )
            """
        )

def create_task_note(task_id, content):
    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Working note cannot be empty. ")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                INSERT INTO task_notes (task_id, content)
                VALUES (?, ?)
                """, (task_id, content.strip()))

            note_id = cursor.lastrowid

    return note_id

def fetch_task_notes(task_id):
    if task_id is None:
        return []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
            id,
            task_id,
            content,
            created_at,
            updated_at
            FROM task_notes
            WHERE task_id = ?
            AND deleted_at IS NULL
            ORDER BY id DESC
            """, (task_id,)).fetchall()

    return [dict(row) for row in rows]