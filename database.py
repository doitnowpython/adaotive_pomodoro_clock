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
