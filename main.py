import sys
from PySide6.QtWidgets import (
QApplication,
QWidget,
QLabel,
QPushButton,
QVBoxLayout,
QSpinBox
)
import time
import math
from PySide6.QtCore import (
    QTimer,
    Qt
)
from PySide6.QtGui import (
QFont
)

def start_focus():
    global started_at

    if started_at is not None:
        return

    focus_input.setEnabled(False)
    break_input.setEnabled(False)
    started_at = time.monotonic()
    status_label.setText("Focusing!")
    start_button.setText("Running")
    start_button.setEnabled(False)
    pause_button.setEnabled(True)

    update_countdown()
    timer.start(100)

def reset_focus():
    global remaining_seconds
    global started_at
    global elapsed_before_pause

    timer.stop()
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
        math.ceil(focus_duration - elapsed_seconds)
    )

    timer_label.setText(format_time(remaining_seconds))

    if remaining_seconds == 0 :
        timer.stop()
        status_label.setText("Focus Complete!")
        start_button.setText("Reset to start again!")
        pause_button.setEnabled(False)

def pause_focus():
    global started_at,elapsed_before_pause

    if started_at is None:
        return

    update_countdown()

    if remaining_seconds == 0 :
        return

    elapsed_before_pause += time.monotonic() - started_at
    started_at = None
    timer.stop()

    status_label.setText("Paused!")
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


print(format_time(1500))
print(format_time(1000))
print(format_time(90))
print(format_time(7))
print(format_time(0))
print(format_time(125))

#focus intials
started_at = None
focus_duration = 25 * 60 # 60 for seconds
remaining_seconds = focus_duration
elapsed_before_pause = 0.0
is_compact = False
normal_size = None
break_duration = 7 * 60

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("My Focus Clock")
window.resize(300, 200)

timer = QTimer(window)
timer.timeout.connect(update_countdown)


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

layout = QVBoxLayout()
layout.setContentsMargins(20, 20, 20, 20)
layout.setSpacing(12)
layout.addWidget(status_label)
layout.addWidget(timer_label)
layout.addWidget(start_button)
layout.addWidget(pause_button)
layout.addWidget(reset_button)
layout.addWidget(compact_button)
layout.addWidget(timer_label)
layout.addWidget(focus_input)
layout.addWidget(break_input)

window.setLayout(layout)
window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
window.setWindowOpacity(0.9)

start_button.clicked.connect(start_focus)
reset_button.clicked.connect(reset_focus)
pause_button.clicked.connect(pause_focus)
compact_button.clicked.connect(toogle_compact)
focus_input.valueChanged.connect(change_focus_duration)
break_input.valueChanged.connect(change_break_duration)

window.show()
sys.exit(app.exec())

