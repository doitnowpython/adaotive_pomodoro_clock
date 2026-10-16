import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout, QTextEdit
)

from database import (
    fetch_recent_sessions,
    fetch_sessions_notes,
    fetch_today_summary
)

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

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            "font-size: 14px; font-weight:bold; padding: 8px;"
        )

        self.notes_window = QDialog(self)
        self.notes_window.resize(450,350)

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)

        notes_layout = QVBoxLayout(self.notes_window)
        notes_layout.addWidget(self.notes_text)

        self.table = QTableWidget(0,6)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Type",
            "Outcome",
            "Planned (min)",
            "Actual (sec)",
            "Saved at (IST)"
        ])
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_sessions)

        notes_button = QPushButton("View Notes")
        notes_button.clicked.connect(self.show_selected_notes)

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.feedback_label)
        layout.addWidget(self.table)

        layout.addWidget(notes_button)

        layout.addWidget(refresh_button)

    def load_sessions(self):
        self.load_summary()
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

    def show_selected_notes(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            self.feedback_label.setText(
                "Select a session in the table first."
            )
            return

        session_id = int(
            self.table.item(selected_row, 0).text()
        )

        try:
            notes = fetch_sessions_notes(session_id)
        except sqlite3.Error as error:
            self.feedback_label.setText(
                "Could not load notes. Please try again."
            )
            print("Notes error: ", error)
            return

        sections =[]

        for note in notes:
            remarks = note["remarks"] or "No remarks entered."

            sections.append(
                f"Task : {note['task']}\n\n"
                f"Remarks:\n{remarks}"
            )

        if sections:
            text = "\n\n---------------------------\n\n".join(sections)
        else:
            text = "No saved notes linked to this session."

        self.notes_text.setPlainText(text)
        self.notes_window.setWindowTitle(
            f"Notes for session #{session_id}"
        )
        self.notes_window.show()
        self.notes_window.raise_()
        self.notes_window.activateWindow()

    def load_summary(self):
        try:
            summary = fetch_today_summary()
        except sqlite3.Error as error:
            self.summary_label.setText(
                "Daily summary unavailable. Click Refresh to retry."
            )
            print("Summary error: ", error)
            return

        total_seconds = int(summary["focus_seconds"])
        minutes, seconds = divmod(total_seconds, 60)

        self.summary_label.setText(
            f"Today (IST) - Saved focus time: "
            f"{minutes} min {seconds:02d} sec\n"
            f"Focus sessions - Completed: {summary['completed']} | "
            f"Skipped: {summary['skipped']}"
        )