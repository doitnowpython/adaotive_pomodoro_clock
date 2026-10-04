import sqlite3
from contextlib import closing

with closing(
    sqlite3.connect(
        "/home/piyush/Projects/PomodoriClock/pomodoro.db"
        )
    )as connection:
    rows = connection.execute(
        "SELECT *FROM work_logs ORDER BY id DESC LIMIT 10"
    ).fetchall()


for row in rows:
    print(row)