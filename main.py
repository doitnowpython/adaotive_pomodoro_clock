import sys
from pathlib import Path
import sqlite3
from contextlib import closing
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QSpinBox,
    QSystemTrayIcon,
    QStyle,
    QDialog,
    QLineEdit,
    QTextEdit)
import time
import math
from PySide6.QtCore import (
    QTimer,
    Qt,
    QUrl)
from PySide6.QtGui import (
    QFont, QIcon)
from PySide6.QtMultimedia import (
    QSoundEffect)


def start_focus():
    global started_at

    if started_at is not None:
        return 

    focus_input.setEnabled(False)
    break_input.setEnabled(False)

    started_at = time.monotonic()

    if session_type == "focus":
        status_label.setText("Focusing!")
        start_button.setText("Focus running")

    else:
        status_label.setText("Break time!")
        start_button.setText("Break running")


    start_button.setEnabled(False)
    pause_button.setEnabled(True)

    timer.start(100)
    update_countdown()

def reset_focus():
    global remaining_seconds
    global started_at
    global elapsed_before_pause
    global session_type

    timer.stop()
    QApplication.beep()
    session_type = "focus"
    started_at = None
    elapsed_before_pause = 0.0
    remaining_seconds = focus_duration #restores the full duration

    focus_input.setEnabled(True)
    break_input.setEnabled(True)
    timer_label.setText(format_time(remaining_seconds))
    status_label.setText("Ready!")
    start_button.setText("Start!")
    start_button.setEnabled(True)
    pause_button.setEnabled(False)

def format_time(total_seconds):
    # Calculate complete minutes
    # Calculate leftover seconds
    # Return Text in MM:SS format
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def update_countdown():
    global remaining_seconds

    if started_at is None:
        return

    elapsed_seconds = (
        elapsed_before_pause
        + (time.monotonic() - started_at)
    )
    remaining_seconds = max(
        0,
        math.ceil(get_session_duration()-elapsed_seconds)
    )

    timer_label.setText(format_time(remaining_seconds))

    if remaining_seconds == 0 :
        finish_session()


def pause_focus():
    global started_at,elapsed_before_pause

    if started_at is None:
        return

    previous_session = session_type
    update_countdown()

    # Updating may have finished the session
    if session_type != previous_session or started_at is None:
        return


    elapsed_before_pause += time.monotonic() - started_at
    started_at = None
    timer.stop()
    QApplication.beep()

    status_label.setText(f"Paused: {session_type}")
    start_button.setText("Resume!")
    start_button.setEnabled(True)
    pause_button.setEnabled(False)

def toogle_compact():
    global is_compact,normal_size

    if not is_compact:
        normal_size = window.size()

    is_compact = not is_compact

    status_label.setVisible(not is_compact)
    reset_button.setVisible(not is_compact)
    focus_input.setVisible(not is_compact)
    break_input.setVisible(not is_compact)
    available_time_input.setVisible(not is_compact)
    preview_plan_button.setVisible(not is_compact)
    plan_preview.setVisible(not is_compact)

    font = timer_label.font()

    if is_compact:
        font.setPointSize(28)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(4)
        compact_button.setText("Expand")
    else:
        font.setPointSize(40)
        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(12)
        compact_button.setText("Compact")

    timer_label.setFont(font)
    layout.activate()
    if is_compact:
        window.resize(220,180)
    else:
        window.resize(normal_size)

def change_focus_duration(minutes):
    global focus_duration, remaining_seconds

    focus_duration = minutes * 60
    remaining_seconds = focus_duration

    timer_label.setText(format_time(remaining_seconds))

def change_break_duration(minutes):
    global break_duration

    break_duration = minutes * 60

def get_session_duration():
    if session_type == "focus":
        return focus_duration
    return break_duration

def finish_session():
    global session_type, started_at
    global elapsed_before_pause, remaining_seconds

    timer.stop()
    session_sound.play()
    # Choose the next Session
    if session_type == "focus":
        session_type = "break"
    else:
        session_type = "focus"

    #Give the new session a fresh timing state.
    started_at = None
    elapsed_before_pause = 0.0
    remaining_seconds = get_session_duration()

    timer_label.setText(format_time(remaining_seconds))

    #Automatically start the next session.
    start_focus()

    if session_type == ("break"):
        notify_user(
            "Break started",
            f"Focus complete! Take a {break_duration //60
            }-minutes break."
        )
        show_work_log()
    else:
        notify_user(
            "Focus started",
            f"Break complete! Your {focus_duration //60
            }-minutes focus session has started."
        )

def notify_user(title, message):
    if (
        QSystemTrayIcon.isSystemTrayAvailable()
        and QSystemTrayIcon.supportsMessages()
    ):
        tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
        5000
        )
    else:
        print(f"{title}: {message}")

def show_work_log():
    print("Opening work log window")
    log_window.show()
    log_window.raise_()

def preview_work_log():
    task_name = task_name_input.text().strip()
    remarks = remarks_input.toPlainText().strip()

    if not task_name:
        log_feedback_label.setText("Please enter a task name")
        return

    work_log ={
        "task": task_name,
        "remarks": remarks
    }

    print(work_log)
    log_feedback_label.setText("Preview printed in the console. Not saved yet.")

def save_work_log():
    task_name = task_name_input.text().strip()
    remarks = remarks_input.toPlainText().strip()

    if not task_name:
        log_feedback_label.setText("Please enter a task name.")
        return

    try:
        with closing(
                sqlite3.connect(database_path
                )) as connection:
            connection.execute("""
            CREATE TABLE IF NOT EXISTS work_logs(
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                remarks TEXT NOT NULL
                )
                """)
            connection.execute(
                "INSERT INTO work_logs (task, remarks) VALUES (?, ?)",
                (task_name, remarks)
            )

            connection.commit()

    except sqlite3.Error as error:
        log_feedback_label.setText(
            "Could not save. Your notes are still here."
        )
        print("Save error:", error)
        return

    log_feedback_label.setText("Work log saved.")
    task_name_input.clear()
    remarks_input.clear()
def build_session_plan(total_minutes, focus_minutes, break_minutes):
    if total_minutes < 0:
        raise ValueError("Available time cannot be negative.")

    if focus_minutes <= 0 or break_minutes <= 0:
        raise ValueError("Focus and break durations must be positive.")

    plan = []
    remaining_minutes = total_minutes

    while remaining_minutes > 0:
        #Use a full focus block, or whatever time remaining.
        current_focus = min(focus_minutes, remaining_minutes)

        plan.append(("focus", current_focus))
        remaining_minutes -= current_focus

        #Stop if a complete break would leave no time for focus.
        if remaining_minutes <= break_minutes:
            break

        plan.append(("break", break_minutes))
        remaining_minutes -= break_minutes

    return plan

def preview_session_plan():
    available_minutes = available_time_input.value()

    plan = build_session_plan(
        available_minutes,
        focus_input.value(),
        break_input.value()
    )

    lines = []
    planned_minutes = 0

    for session_kind, minutes in plan:
        lines.append(f"{session_kind.capitalize()}: {minutes} min")
        planned_minutes += minutes

    unused_minutes = available_minutes - planned_minutes
    lines.append(f"\nPlanned: {planned_minutes} min")
    lines.append(f"Unused: {unused_minutes} min")

    plan_preview.setText("\n".join(lines))

#Simple Time conversion for refference
print(format_time(1500))
print(format_time(1000))
print(format_time(90))
print(format_time(7))
print(format_time(0))
print(format_time(125))

print("90 minutes:", build_session_plan(90,25,7))
print("50 minutes:", build_session_plan(50,25,7))
print("20 minutes:", build_session_plan(20,25,7))

#intilzie Database
database_path = Path(__file__).resolve().parent/"pomodoro.db"

#focus intials
sound_path = Path(__file__).resolve().parent / "sound/session_chime.wav"
started_at = None
focus_duration = 25 * 60 # 60 for seconds
remaining_seconds = focus_duration
elapsed_before_pause = 0.0
is_compact = False
normal_size = None
break_duration = 7 * 60
session_type = "focus"
active_plan = []
current_session_index = 0

#app window creation
app = QApplication(sys.argv)

#app window settings
window = QWidget()
window.setWindowTitle("My Focus Clock")
window.resize(300, 200)

#app siund settings
session_sound = QSoundEffect(window)
session_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
session_sound.setVolume(0.7)
session_sound.setLoopCount(1)

#app notification settings
tray_icon = QSystemTrayIcon(window)
tray_icon.setIcon(
    window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
)
tray_icon.setToolTip("My Focus Clock")
tray_icon.show()

#timer settings
timer = QTimer(window)
timer.timeout.connect(update_countdown)

#timer status settings
status_label = QLabel("Ready!")
timer_label = QLabel(format_time(remaining_seconds))

status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

start_button = QPushButton("Start!")
reset_button = QPushButton("Reset")
pause_button = QPushButton("Pause")
compact_button = QPushButton("Compact")
focus_input = QSpinBox()

timer_font = QFont()
timer_font.setPointSize(40)
timer_font.setBold(True)

timer_label.setFont(timer_font)
timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

pause_button.setEnabled(False)

focus_input.setRange(1,180)
focus_input.setValue(focus_duration // 60)
focus_input.setPrefix("Focus: ")
focus_input.setSuffix(" min")

break_input = QSpinBox()
break_input.setRange(1,120)
break_input.setValue(break_duration // 60)
break_input.setPrefix("Break: ")
break_input.setSuffix(" min")

available_time_input = QSpinBox()
available_time_input.setRange(1,1440)
available_time_input.setValue(90)
available_time_input.setPrefix("Available: ")
available_time_input.setSuffix(" min")

preview_plan_button = QPushButton("Preview plan")

plan_preview = QLabel("Your session plan will appear here.")
plan_preview.setWordWrap(True)

layout = QVBoxLayout()
layout.setContentsMargins(20, 20, 20, 20)
layout.setSpacing(12)
layout.addWidget(status_label)
layout.addWidget(timer_label)
layout.addWidget(start_button)
layout.addWidget(pause_button)
layout.addWidget(reset_button)
layout.addWidget(compact_button)
layout.addWidget(focus_input)
layout.addWidget(break_input)
layout.addWidget(available_time_input)
layout.addWidget(preview_plan_button)
layout.addWidget(plan_preview)

#log window settings
log_window = QDialog(window)
log_window.setWindowTitle("Focus session notes")
log_window.resize(400,300)
log_window.setModal(False)

task_name_input = QLineEdit()
task_name_input.setPlaceholderText("What task were you working on?")

remarks_input = QTextEdit()
remarks_input.setPlaceholderText(
    "What did you complete, discover, or leave pending?"
)

log_layout = QVBoxLayout(log_window)
log_layout.addWidget(QLabel("Task"))
log_layout.addWidget(task_name_input)
log_layout.addWidget(QLabel("Findings and remarks"))
log_layout.addWidget(remarks_input)

save_log_button = QPushButton("Save log")
log_feedback_label = QLabel("")

log_layout.addWidget(save_log_button)
log_layout.addWidget(log_feedback_label)

save_log_button.clicked.connect(save_work_log)

window.setLayout(layout)
window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
window.setWindowOpacity(0.9)

start_button.clicked.connect(start_focus)
reset_button.clicked.connect(reset_focus)
pause_button.clicked.connect(pause_focus)
compact_button.clicked.connect(toogle_compact)
focus_input.valueChanged.connect(change_focus_duration)
break_input.valueChanged.connect(change_break_duration)
preview_plan_button.clicked.connect(preview_session_plan)


window.show()
sys.exit(app.exec())




