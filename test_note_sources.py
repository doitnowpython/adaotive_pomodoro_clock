import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import database as db

class NoteSourceTests(unittest.TestCase):
    def test_copied_note_keeps_its_source(self):
        with TemporaryDirectory() as folder:
            test_path = Path(folder) / "test.db"

            with patch.object(db,"database_path", test_path):
                db.initialize_tasks()
                db.initialize_work_logs()
                db.initialize_task_notes()
                db.initialize_task_note_groups()

                task_id = db.create_task("Python practice")

                session_id = db.save_session_record({
                    "session_type" : "focus",
                    "outcome": "completed",
                    "planned_seconds" : 60,
                    "actual_seconds" : 60,
                })
                self.assertIsNotNone(session_id)

                with closing(sqlite3.connect(test_path)) as connection:
                    connection.execute("PRAGMA foreign_keys = ON")

                    with connection:
                        source_id = connection.execute(
                            """
                            INSERT INTO work_logs (
                            id, task, remarks, session_id, task_id
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (17,
                             "Python practice",
                             "Practised generators.",
                             session_id,
                             task_id)
                        ).lastrowid

                note_id = db.create_task_note_from_work_log(
                    task_id, source_id
                )

                sources = db.fetch_task_note_sources(note_id, task_id)

                self.assertEqual(len(sources), 1)
                self.assertEqual(sources[0]["work_log_id"], source_id)
                self.assertEqual(
                    sources[0]["remarks"], "Practised generators."
                )
                self.assertEqual(sources[0]["session_id"], session_id)

if __name__ == "__main__":
    unittest.main()


