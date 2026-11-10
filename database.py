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

def initialize_task_note_groups():
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            connection.execute("""
                CREATE TABLE IF NOT EXISTS task_note_groups (
                    id INTEGER PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES tasks(id),
                    name TEXT NOT NULL COLLATE NOCASE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (task_id, name)
                )
            """)

            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(task_notes)"
                )
            }

            if "group_id" not in columns:
                connection.execute("""
                    ALTER TABLE task_notes
                    ADD COLUMN group_id INTEGER
                        REFERENCES task_note_groups(id)
                        ON DELETE SET NULL
                """)
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

def update_task_note(note_id,task_id,content):
    if type(note_id) is not int or note_id <= 0:
        raise ValueError("Select a working note.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Working note cannot be empty. ")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                UPDATE task_notes
                SET content = ?,
                    updated_at = CURRENT_TIMESTAMP
                where id = ?
                    AND task_id = ?
                    AND deleted_at IS NULL
                """, (content.strip(), note_id, task_id))

            if cursor.rowcount != 1:
                raise ValueError(
                    "This working note is no longer available. "
                    "For this task"
                )

def fetch_task_notes(task_id, group_filter= "all"):
    if task_id is None:
        return []

    query = """
        SELECT 
            id,
            task_id,
            content,
            created_at,
            updated_at,
            group_id
        FROM task_notes
        Where task_id = ?
        AND deleted_at IS NULL
    """

    parameters = [task_id]

    if group_filter is None:
        query += " AND group_id IS NULL"
    elif type(group_filter) is int and group_filter > 0:
        query += " AND group_id = ?"
        parameters.append(group_filter)
    elif group_filter != "all":
        raise ValueError("Invalid group filter.")

    query += " ORDER BY id DESC"

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]

def trash_task_notes(note_id, task_id):
    if type(note_id) is not int or note_id <= 0:
        raise ValueError("Select a working note.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                UPDATE task_notes
                SET deleted_at = CURRENT_TIMESTAMP
                where id = ?
                AND task_id = ?
                AND deleted_at IS NULL
                """, (note_id, task_id)
            )
            if cursor.rowcount != 1:
                raise ValueError(
                    "This working note is no longer available. "
                    "for this task"
                )

def restore_task_notes(note_id, task_id):
    if type(note_id) is not int or note_id <= 0:
        raise ValueError("Select a working note.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                UPDATE task_notes
                SET deleted_at = NULL
                WHERE id = ?
                AND task_id = ?
                AND deleted_at IS NOT NULL
                """, (note_id, task_id)
            )
            if cursor.rowcount != 1:
                raise ValueError(
                    "This not is no longer in Trash "
                    "for this task. "
                )

def fetch_trashed_task_notes(task_id):
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
            updated_at,
            deleted_at
            FROM task_notes
            WHERE 
            task_id = ?
            AND deleted_at IS NOT NULL
            ORDER BY deleted_at DESC, id DESC
            """, (task_id,)
        ).fetchall()

    return [dict(row) for row in rows]

def create_task_note_group(task_id, name):
    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Group name cannot be empty. ")

    name = name.strip()

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                INSERT INTO task_note_groups (task_id, name)
                VALUES (?, ?)
                ON CONFLICT (task_id, name) DO NOTHING
                """, (task_id, name)
            )
            if cursor.rowcount != 1:
                raise ValueError(
                    "A group with this name already exists "
                    "for this task. "
                )

            group_id = cursor.lastrowid

        return group_id

def fetch_task_note_group(task_id):
    if task_id is None:
        return []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
            id,
            task_id,
            name,
            created_at
            FROM task_note_groups
            WHERE task_id = ?
            ORDER BY name COLLATE NOCASE, id
            """, (task_id,)
        ).fetchall()

    return [dict(row) for row in rows]

def move_task_note_to_group(note_id, task_id, group_id):
    if type(note_id) is not int or note_id <= 0:
        raise ValueError("Select a working note.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if group_id is not None:
        if type(group_id) is not int or group_id <= 0:
            raise ValueError("Select a valid group or Ungrouped.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            if group_id is not None:
                group = connection.execute(
                    """
                    SELECT id
                    FROM task_note_groups
                    WHERE id = ?
                    AND task_id = ?
                    """, (group_id, task_id)
                ).fetchone()

                if group is None:
                    raise ValueError(
                        "This group is not available for this task."
                    )

            cursor = connection.execute(
                """
                UPDATE task_notes
                SET group_id = ?
                WHERE id = ?
                    AND task_id = ?
                    AND deleted_at IS NULL
                """, (group_id,note_id, task_id)
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "This working note is no longer available. "
                    "for this task."
                )

def rename_task_note_group(group_id, task_id, name):
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Select an existing group.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Group name cannot be empty. ")

    name = name.strip()

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            duplicate = connection.execute(
                """
                SELECT id
                FROM task_note_groups
                WHERE task_id = ?
                    AND name = ? COLLATE NOCASE
                    AND id !=?
                """,
                (task_id, name, group_id)
            ).fetchone()

            if duplicate is not None:
                raise ValueError(
                    "A group with this name already exists "
                    "for this task."
                )

            cursor = connection.execute(
                """
                UPDATE task_note_groups
                SET name = ?
                WHERE id = ?
                    AND task_id = ?
                """,
                (name, group_id, task_id)
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "This group is no longer available "
                    "for this task."
                )

def delete_task_note_group(group_id, task_id):
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Select an existing group.")

    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                """
                DELETE FROM task_note_groups
                WHERE id = ?
                AND task_id = ?
                """,
                (group_id, task_id)
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "This group is no longer available "
                    "for this task. "
                )

def create_task_note_from_work_log(task_id, work_log_id):
    if type(task_id) is not int or task_id <= 0:
        raise ValueError("Select an existing task.")

    if type(work_log_id) is not int or work_log_id <= 0:
        raise ValueError("Select a saved session remark.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            source = connection.execute(
                """
                SELECT remarks
                FROM work_logs
                WHERE task_id = ?
                    AND task_id = ?
                """,
                (work_log_id, task_id)
            ).fetchone()

            if source is None:
                raise ValueError(
                    "This session remarks is not available "
                    "for this task."
                )

            content = source[0]

            if not content or not content.strip():
                raise ValueError(
                    "This session remark is empty."
                )

            cursor = connection.execute(
                """
                INSERT INTO task_notes (task_id, content)
                VALUES (?, ?)
                """,
                (task_id, content)
            )
            note_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO task_note_sources (
                task_note_id,
                work_log_id
                ) VALUES (?, ?)
                """,
                (note_id, work_log_id)
            )
        return note_id