import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from PySide6.QtWidgets import(
    QAbstractItemView,
    QDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout
)

from database import fetch_recent_sessions

def format_saved_time(value):
    saved_time = datetime.fromisoformat(value)

    # Older records used SQLite's UTC timestamp without an offset.
    if saved_time.tzinfo is None:
        saved_time = saved_time.replace(tzinfo=timezone.utc)

    return saved_time.astimezone(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%d %b %Y, %H:%M:%S")

class HistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Session History")
        self.resize(850, 400)

        self.feedback_label = QLabel()

        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Type",
            "Outcome",
            "Planned (min)",
            "Actual (min)",
            "Saved at (IST)"
        ])
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_sessions)

        layout = QVBoxLayout(self)
        layout.addWidget(self.feedback_label)
        layout.addWidget(self.table)
        layout.addWidget(refresh_button)

    def load_sessions(self):
        self.table.setRowCount(0)

        try:
            records = fetch_recent_sessions(limit = 20)
        except sqlite3.Error as error:
            self.feedback_label.setText(
                "Could not load history. Click Refresh to try again"
            )
            print("History error: ", error)
            return

        self.table.setRowCount(len(records))

        for row_index, record in enumerate(records):
            values = [
                str(record["id"]),
                record["session_type"].capitalize(),
                record["outcome"].capitalize(),
                f'{record["planned_seconds"]/60:g}',
                f'{record["actual_seconds"]:.2f}',
                format_saved_time(record["saved_at"])
            ]

            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value)
                )

        self.table.resizeColumnsToContents()

        if records:
            self.feedback_label.setText(
                f"Latest {len(records)} sessions - newest first."
            )
        else:
            self.feedback_label.setText(
                "No sessions saved yet."
            )