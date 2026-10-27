import sys
from asyncio import timeout
from email import message
from pathlib import Path
import sqlite3
from contextlib import closing
from tkinter import dialog
from urllib import request

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
    QTextEdit,
    QMessageBox,
    QHBoxLayout, QComboBox)
import time
import math
from PySide6.QtCore import (
    QTimer,
    Qt,
    QUrl,
    QSettings)
from PySide6.QtGui import (
    QFont, QIcon)
from PySide6.QtMultimedia import (
    QSoundEffect)
import json
import history_window
from database import (
    save_session_record,
    fetch_recent_sessions,
    initialize_work_logs,
    fetch_today_summary,
    save_break_review,
    initialize_tasks,
    get_active_tasks)
from history_window import HistoryWindow


def save_pending_notes():
    pending_notes = {
        "session_ids" : pending_log_sessions_ids,
        "task_id" : task_selector.currentData(),
        "task" : task_name_input.text(),
        "remarks" : remarks_input.toPlainText()
    }

    settings.setValue("pending_notes", json.dumps(pending_notes))
    settings.sync()

    if settings.status() != QSettings.Status.NoError:
        log_feedback_label.setText(
            "Could not autosave draft. keep this window open."
        )

def schedule_notes_autosave():
    notes_autosave_timer.start()

def save_timer_state():
    if not active_plan or current_session_index >= len(active_plan):
        settings.remove("timer_state")
    else:
        elapsed = elapsed_before_pause

        if started_at is not None:
            elapsed += time.monotonic() - started_at

        state = {
            "plan" : active_plan,
            "index" : current_session_index,
            "elapsed" : min(
                get_session_duration(),
                max(0.0, elapsed)
            ),
            "break_wait_started_at" : break_wait_started_at,
            "plan_window" : plan_window
        }

        settings.setValue("timer_state", json.dumps(state))

    settings.sync()
    #Testing
    if active_plan and current_session_index < len(active_plan):
        saved_remaining = math.ceil(
            active_plan[current_session_index][1] * 60
            - state["elapsed"]
        )
        #print(
        #    f"[SAVE] time ={time.strftime('%H:%M:%S')} "
        #    f"block={state['index'] + 1} "
        #    f"elapsed={state['elapsed']:.3f}s "
        #    f"remaining={saved_remaining}s "
        #    f"status={settings.status()}",
        #    flush=True
        #)
    #Temp
    if break_wait_started_at is not None:
        print(
            f"Waiting after break: "
            f"{get_break_wait_seconds():.1f} seconds"
        )

def save_settings():
    settings.setValue("focus_minutes", focus_input.value())
    settings.setValue("break_minutes", break_input.value())
    settings.setValue("available_minutes", available_time_input.value())
    settings.setValue("compact_mode", is_compact)
    settings.setValue("window_position", window.pos())

    save_pending_notes()
    save_timer_state()

def start_focus():
    global started_at, active_plan, current_session_index
    global session_type, remaining_seconds
    global break_wait_started_at, plan_window

    if started_at is not None:
        return 

    # Create the plan only for a fresh start
    if not active_plan:
        active_plan = build_session_plan(
            available_time_input.value(),
            focus_input.value(),
            break_input.value()
        )
        current_session_index = 0
        preview_session_plan()

        #adding overflow for break
        original_start = time.time()
        requested_seconds = available_time_input.value() * 60

        plan_window = {
            "started_at" : original_start,
            "requested_seconds" : requested_seconds,
            "latest_finished_at" : original_start + requested_seconds * 1.5
        }

    if not active_plan or current_session_index >= len(active_plan):
        return

    if plan_window is not None:
        now = time.time()
        latest_finish = plan_window["latest_finished_at"]
        expected_finish = now + get_remaining_plan_seconds()

        if now >= latest_finish or expected_finish > latest_finish:
            timer.stop()

            session_label.setText("PLAN NEEDS REVIEW")
            status_label.setText(
                "The remaining sessions no longer fit"
                "within this plan's deadline."
            )

            start_button.setText("Review before continuing")
            start_button.setEnabled(True)
            pause_button.setEnabled(False)
            skip_button.setEnabled(True)

            update_plan_finish_display()
            save_timer_state()

            plan_data = get_revised_plan_data()
            preview_text = get_revised_plan_preview_text(plan_data)

            review_message = QMessageBox(window)
            review_message.setWindowTitle("Revised plan preview")
            review_message.setText(
                "The current schedule no longer fits before "
                "the original deadline."
            )
            review_message.setInformativeText(
                "Show Details to review the proposal.\n"
                "Apply will use this schedule and resume the timer."
            )
            review_message.setDetailedText(preview_text)

            apply_button = review_message.addButton(
                "Apply and resume",
                QMessageBox.ButtonRole.AcceptRole
            )
            cancel_button = review_message.addButton(
                QMessageBox.StandardButton.Cancel
            )
            review_message.setDefaultButton(cancel_button)
            review_message.setEscapeButton(cancel_button)

            apply_button.setEnabled(
                plan_data is not None and bool(plan_data["proposal"])
            )

            review_message.setStyleSheet(
                """
                    QLabel{
                        min-width: 500px;
                        font-size: 14px;
                    }
                    QTextEdit{
                        min-width: 500px;
                        min-height: 250px;
                        font-size: 14px;
                    }
                """
            )
            review_message.exec()

            if review_message.clickedButton() != apply_button:
                return False

            if plan_data is None:
                return False

            # Ensure the timer still matches the preview's snapshot.
            state_unchanged = (
                started_at is None
                and plan_window is not None
                and plan_window["latest_finished_at"]
                == plan_data["deadline"]
                and current_session_index == plan_data["session_index"]
                and [tuple(session) for session in active_plan]
                == plan_data["original_plan"]
                and elapsed_before_pause == plan_data["elapsed"]
            )

            if not state_unchanged:
                QMessageBox.information(
                    window,
                    "Preview needs refreshing",
                    "The timer state has changed. "
                    "Open the review again for a fresh proposal."
                )
                return False

            #Time kept passing while the dialog was open.
            if not revised_plan_still_fits(
                plan_data["proposal"],
                elapsed_current = plan_data["elapsed"],
                latest_finish = plan_data["deadline"]
            ):
                QMessageBox.information(
                    window,
                    "Proposal no longer fits",
                    "This proposal no longer fits before the deadline.\n"
                    "Your plan is unchanged. Open the review again. "
                )
                return False

            #Preserve completed session and replace unfinished ones.
            active_plan =(
                active_plan[:current_session_index]
                + list(plan_data["proposal"])
            )
            preview_session_plan()

            remaining_seconds = max(
                0.0,
                active_plan[current_session_index][1] * 60
                - elapsed_before_pause
            )
            save_timer_state()
            update_plan_finish_display()


    #Read the CURRENT block, not the first block
    session_type = active_plan[current_session_index][0]

    for widget in (
        focus_input,
        break_input,
        available_time_input,
        preview_plan_button
    ):
        widget.setEnabled(False)

    break_wait_started_at = None
    started_at = time.monotonic()


    total_of_type = sum(
        kind == session_type
        for kind,minutes in active_plan
    )

    current_of_type = sum(
        kind == session_type
        for kind,minutes in active_plan[:current_session_index + 1]
    )

    status_label.setText(
        f"{session_type.capitalize()} "
        f"{current_of_type} of {total_of_type}\n\n"
        f"Total Sessions : {current_session_index + 1}/{len(active_plan)}"
    )

    start_button.setText(f"{session_type.capitalize()} running")
    start_button.setEnabled(False)
    pause_button.setEnabled(True)
    skip_button.setEnabled(True)

    # Refresh the display whenever a session starts or resumes.
    if session_type == "focus":
        session_label.setText("FOCUS - TASK TIME")
        timer_label.setStyleSheet("color: #FBBF24;")
    else:
        session_label.setText("BREAK - REST TIME")
        timer_label.setStyleSheet("color: #16803C;")
    timer.start(100)
    update_countdown()
    save_timer_state()
    print_plan_window()
    return True

def reset_focus():
    global active_plan, current_session_index, session_type
    global started_at, elapsed_before_pause, remaining_seconds
    global break_wait_started_at, plan_window

    timer.stop()
    plan_window = None
    break_wait_started_at = None

    active_plan = []
    current_session_index = 0
    session_type = "focus"

    started_at = None
    elapsed_before_pause = 0.0
    remaining_seconds = focus_duration 

    for widget in (
       focus_input,
       break_input,
       available_time_input,
       preview_plan_button
    ):
       widget.setEnabled(True)

    timer_label.setText(format_time(remaining_seconds))

    session_label.setText("FOCUS - READY")
    timer_label.setStyleSheet("")

    status_label.setText("Ready!")
    start_button.setText("Start!")
    start_button.setEnabled(True)
    pause_button.setEnabled(False)
    skip_button.setEnabled(False)
    save_timer_state()
    preview_session_plan()



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

    session_label.setText(f"{session_type.upper()} - PAUSED")

    status_label.setText(f"Paused: {session_type}")
    start_button.setText("Resume!")
    start_button.setEnabled(True)
    pause_button.setEnabled(False)
    save_timer_state()

def toogle_compact():
    global is_compact,normal_size

    if not is_compact:
        normal_size = window.size()

    is_compact = not is_compact

    status_label.setVisible(not is_compact)
    reset_button.setVisible(not is_compact)
    skip_button.setVisible(not is_compact)
    focus_input.setVisible(not is_compact)
    break_input.setVisible(not is_compact)
    available_time_input.setVisible(not is_compact)
    preview_plan_button.setVisible(not is_compact)
    plan_preview.setVisible(not is_compact)
    history_button.setVisible(not is_compact)
    plan_finish_label.setVisible(not is_compact)

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
    if active_plan and current_session_index < len(active_plan):
        return active_plan[current_session_index][1] * 60

    if session_type == "focus":
        return focus_duration

    return break_duration

def finish_session(outcome = "completed"):
    global session_type, started_at, current_session_index
    global elapsed_before_pause, remaining_seconds
    global break_wait_started_at

    if not active_plan or current_session_index >= len(active_plan):
        return

    finished_type = session_type
    planned_seconds = get_session_duration()

    #Active time accumulated before the most recent pause.
    actual_seconds = elapsed_before_pause

    #Add the current running period, if clock is running.
    if started_at is not None:
        actual_seconds += time.monotonic() - started_at

    #Timer callbacks can arrive slightly after the deadline.
    actual_seconds = min(
        planned_seconds,
        max(0.0, actual_seconds)
    )

    session_record = {
        "session_type": finished_type,
        "outcome": outcome,
        "planned_seconds": planned_seconds,
        "actual_seconds": round(actual_seconds, 2)
    }

    print("Session record:", session_record)

    timer.stop()

    save_started = time.perf_counter()
    save_session_id = save_session_record(session_record)
    print(
        f"Database save : "
        f"{(time.perf_counter() - save_started) * 1000:.1f} ms"
    )

    if save_session_id is not None:
        print(f"Session saved with ID: {save_session_id}")

        try:
            print("Today's focus summary:" , fetch_today_summary())
        except sqlite3.Error as error:
            print("Could not load daily summary:", error)


    session_sound.play()

    started_at = None
    elapsed_before_pause = 0.0
    current_session_index += 1

    if current_session_index >= len(active_plan):
        remaining_seconds = 0
        timer_label.setText("00:00")
        status_label.setText("Hurray Plan Completed!")
        session_label.setText("Plan Completed")
        timer_label.setStyleSheet("")


        start_button.setText("Reset for a new plan")
        start_button.setEnabled(False)
        pause_button.setEnabled(False)
        skip_button.setEnabled(False)

        notify_user(
            "Plan complete",
            "Your Planned sessions are finished"
        )
    else:
        session_type = active_plan[current_session_index][0]
        remaining_seconds = get_session_duration()

        timer_label.setText(format_time(remaining_seconds))

        if session_type == "break":
            # Start the break automatically after focus.
            if start_focus():
                notify_user(
                    "Break Started",
                    f"Take a {remaining_seconds // 60}-minute break. "
                )

        else:
            # Prepare the next focus, but wait for Start.
            break_wait_started_at = time.time()

            session_label.setText("FOCUS - READY")
            timer_label.setStyleSheet("color: #FBBF24;")

            status_label.setText(
                f"Block {current_session_index + 1} of "
                f"{len(active_plan)}\n"
                "Click Start focus when you are ready."
            )
            start_button.setText("Start Focus")
            start_button.setEnabled(True)
            pause_button.setEnabled(False)
            skip_button.setEnabled(False)

            notify_user(
                "Focus ready",
                "Your break has ended. CLick Start focus to continue."
            )

    if finished_type == "focus" and save_session_id is not None:
        pending_log_sessions_ids.append(save_session_id)
        save_pending_notes()
        print("Notes queue after adding: ", pending_log_sessions_ids)
        show_work_log()

    save_timer_state()

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
    if not pending_log_sessions_ids:
        return

    session_id = pending_log_sessions_ids[0]

    log_window.setWindowTitle(
        f"Notes for focus session #{session_id}"
    )
    save_log_button.setEnabled(True)
    task_name_input.setEnabled(True)
    remarks_input.setEnabled(True)
    log_window.show()
    log_window.raise_()

def preview_work_log():
    task_name = task_name_input.text().strip()
    remarks = remarks_input.toPlainText().strip()

    if not task_name:
        log_feedback_label.setText("Please enter a task name")
        return

    work_log = {
        "task": task_name,
        "remarks": remarks
    }

    print(work_log)
    log_feedback_label.setText("Preview printed in the console. Not saved yet.")

def save_work_log():

    if not pending_log_sessions_ids:
        log_feedback_label.setText("No session waiting for notes.")
        return

    session_id = pending_log_sessions_ids[0]
    task_name = task_name_input.text().strip()
    remarks = remarks_input.toPlainText().strip()
    task_id = task_selector.currentData()
    # temp
    print(
        f"[TASK SAVE] option = {task_selector.currentText()!r} "
        f"task_id = {task_id!r}"
    )

    if not task_name:
        log_feedback_label.setText("Please enter a task name.")
        return

    try:
        with closing(sqlite3.connect(database_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            if task_id is None:
                existing_task = connection.execute(
                    """
                    SELECT id, name
                    FROM tasks
                    WHERE name = ? COLLATE NOCASE
                        AND status = 'active'
                    ORDER BY id
                    LIMIT 1
                    """, (task_name,)).fetchone()

                if existing_task is not None:
                    task_id = existing_task[0]
                    task_name = existing_task[1]
                else:
                    cursor = connection.execute(
                        "INSERT INTO tasks (name) VALUES (?)",
                        (task_name,)
                    )
                    task_id = cursor.lastrowid

            connection.execute("""
                INSERT INTO work_logs (
                    task,
                    remarks,
                    session_id,
                    task_id
                    )
                    VALUES (?,?,?,?)
                    """,(
                    task_name,
                    remarks,
                    session_id,
                    task_id
                ) )

            connection.commit()

    except sqlite3.Error as error:
        log_feedback_label.setText(
            "Could not save. Your notes are still here."
        )
        print("Save error:", error)
        return

    # Remove the pending ID only after saving succeeds.
    pending_log_sessions_ids.pop(0)
    print("Notes queue after saving: ", pending_log_sessions_ids)

    if task_selector.findData(task_id) == -1:
        task_selector.addItem(task_name, task_id)

    task_name_input.clear()
    task_selector.setCurrentIndex(0)
    remarks_input.clear()
    save_pending_notes()

    if pending_log_sessions_ids:
        show_work_log()
        log_feedback_label.setText(
            f"Saved notes for #{session_id}. "
            "Now showing the next pending session."
        )
    else:
        log_feedback_label.setText(
            f"Saved notes for #{session_id}. "
        )
        save_log_button.setEnabled(False)
        task_name_input.setEnabled(False)
        remarks_input.setEnabled(False)
        QTimer.singleShot(1500, close_work_log_if_done)

def close_work_log_if_done():
    if not pending_log_sessions_ids:
        log_window.close()

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

def build_revised_remaining_plan(
        remaining_plan,
        available_seconds,
        elapsed_current = 0.0
):
    budget = max(0.0,available_seconds)
    proposal =[]

    for index,(kind, minutes) in enumerate(remaining_plan):
        elapsed = elapsed_current if index == 0 else 0.0
        elapsed = min(minutes * 60, max(0.0, elapsed))

        if kind == "break":
            break_left = minutes * 60 - elapsed

            # keep the break only if some focus can follow it
            if budget < break_left + 60:
                break

            proposal.append((kind,minutes))
            budget -= break_left

        else:
            fitted_minutes = min (
                minutes,
                int(( budget + elapsed ) // 60 )
            )
            focus_left = fitted_minutes * 60 - elapsed

            if focus_left <= 0:
                break

            #Avoid proposing a newly shortened focus under one minute.
            if fitted_minutes < minutes and focus_left < 60:
                break

            proposal.append((kind, fitted_minutes))
            budget -= focus_left

            if fitted_minutes < minutes:
                break

        # A revised work schedule should not end with an unused break.
    if proposal and proposal[-1][0] == "break":
        proposal.pop()

    return proposal

def revised_plan_still_fits(
        proposal,
        elapsed_current,
        latest_finish,
        now = None
):
    if not proposal:
        return False

    if now is None:
        now = time.time()

    remaining_seconds = (
        sum(minutes * 60 for kind, minutes in proposal)
        - elapsed_current
    )

    if remaining_seconds <= 0 or now >= latest_finish:
        return False

    return now+remaining_seconds <= latest_finish

def get_revised_plan_data():
    if plan_window is None or started_at is not None:
        return None

    if not active_plan or current_session_index >= len(active_plan):
        return None

    deadline = plan_window["latest_finished_at"]
    available_seconds = max(0.0, deadline - time.time())

    remaining_plan = active_plan[current_session_index:]

    elapsed = min(
        remaining_plan[0][1] * 60,
        max(0.0, elapsed_before_pause)
    )

    proposal = build_revised_remaining_plan(
        remaining_plan,
        available_seconds,
        elapsed_current = elapsed
    )

    return {
        "original_plan" : [tuple(session) for session in active_plan],
        "session_index" : current_session_index,
        "elapsed": elapsed,
        "deadline" : deadline,
        "proposal" : proposal
    }

def get_revised_plan_preview_text(plan_data = None):
    if plan_data is None:
        plan_data = get_revised_plan_data()

    if plan_data is None:
        return (
            "A revised preview is not available. "
            "The timer must be paused with unfinished sessions "
            "and a saved deadline. "
        )

    remaining_plan = plan_data["original_plan"][plan_data["session_index"]:]
    elapsed = plan_data["elapsed"]
    proposal = plan_data["proposal"]

    if not proposal:
        return (
            "There is not enough time for a revised schedule "
            "under the current rules.\n\n"
            "Your current plan is unchanged. You can leave it "
            "paused or explicitly reset it to create a new plan"
        )

    original_focus_seconds = sum(
        minutes * 60
        for kind, minutes in remaining_plan
        if kind == "focus"
    )

    proposed_focus_seconds = sum(
        minutes * 60
        for kind, minutes in proposal
        if kind == "focus"
    )

    focus_left_out = original_focus_seconds - proposed_focus_seconds

    proposed_seconds =(
        sum(minutes *60 for kind, minutes in proposal) - elapsed
    )

    lines = [
        "Proposed remaining schedule:",
        ""
    ]

    for index, (kind, minutes) in enumerate(proposal):
        seconds_left = minutes * 60

        if index == 0:
            seconds_left -= elapsed

        lines.append(
            f"{index + 1}. {kind.capitalize()}: "
            f"{format_time(math.ceil(seconds_left))} remaining"
        )

    lines.extend([
        "",
        f"Total remaining: {format_time(math.ceil(proposed_seconds))}",
        f"Focus time left out: {format_time(focus_left_out)}",
        "",
        "Durations are shown as minutes:seconds.",
        "The original deadline stays fixed.",
        "Preview only - your plan has not been changed."
    ])

    return "\n".join(lines)


def preview_session_plan():
    if active_plan:
        plan = active_plan
        lines = ["Current plan:", ""]
    else:
        plan = build_session_plan(
            available_time_input.value(),
            focus_input.value(),
            break_input.value(),
        )
        lines = ["Plan preview:", ""]

    planned_minutes = 0

    for kind,minutes in plan:
        lines.append(f"{kind.capitalize()}: {minutes} min")
        planned_minutes += minutes

    lines.append(f"\nTotal scheduled: {planned_minutes} min")

    if not active_plan:
        unused_minutes = available_time_input.value() - planned_minutes
        lines.append(f"Unused: {unused_minutes} min")
    else:
        lines.append("Full block durations, including time already worked. ")

    plan_preview.setText("\n".join(lines))


def confirm_reset():
    answer = QMessageBox.question(
        window,
        "Reset plan?",
        "Are you sure you want to reset?\n\n"
        "This will stop the timer and clear the current plan.\n"
        "Saved work logs will stay saved.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )

    if answer == QMessageBox.StandardButton.Yes:
        reset_focus()

def skip_session():
    #Nothing to skip before starting or after the plan code
    if not active_plan:
        return

    if current_session_index >= len(active_plan):
        return

    finish_session(outcome="skipped")

def show_history():
    history_window.load_sessions()
    history_window.show()
    history_window.raise_()
    history_window.activateWindow()

def restore_pending_notes():
    saved_notes = settings.value("pending_notes","",type=str)

    if not saved_notes:
        return

    try:
        notes = json.loads(saved_notes)
        session_ids = [int(value) for value in notes["session_ids"]]
        task_id = notes["task_id"]
        task = notes["task"]
        remarks = notes["remarks"]

        if task_id is not None:
            if type(task_id) is not int or task_id <= 0:
                #raise ValueError("Invalid task ID")
                print(
                    "[NOTES RESTORE} Invalid task ID:",
                    repr(task_id),
                    "type:",
                    type(task_id).__name__,
                )
                task_id = None

        if not isinstance(task, str) or not isinstance(remarks, str):
            raise ValueError("Invalid note text")

    except (ValueError, TypeError, KeyError) as error:
        print ("Could not restore pending notes:", error)
        return

    pending_log_sessions_ids.clear()
    pending_log_sessions_ids.extend(session_ids)

    selected_index = (
        task_selector.findData(task_id)
        if task_id is not None
        else 0
    )

    if selected_index == -1:
        selected_index = 0

    widgets = (task_selector, task_name_input, remarks_input)
    previous_signal_states = [
        widget.blockSignals(True) for widget in widgets
    ]

    try:
        task_selector.setCurrentIndex(selected_index)
        task_name_input.setText(task)
        task_name_input.setReadOnly(selected_index > 0)
        remarks_input.setPlainText(remarks)
    finally:
        for widget, previous_state in zip(
            widgets, previous_signal_states
        ):
            widget.blockSignals(previous_state)
    #task_name_input.setText(task)
    #emarks_input.setPlainText(remarks)

    if pending_log_sessions_ids:
        show_work_log()

def restore_timer_state():
    global active_plan, current_session_index, session_type
    global started_at, elapsed_before_pause, remaining_seconds
    global break_wait_started_at, plan_window

    saved_state = settings.value("timer_state","",type=str)
    if not saved_state:
        return

    try:
        state = json.loads(saved_state)
        plan = state["plan"]
        index = state["index"]
        elapsed = float(state["elapsed"])
        saved_wait_started_at = state.get("break_wait_started_at")
        saved_plan_window = state.get("plan_window")

        if saved_plan_window is not None:
            saved_plan_window = {
                key: float(saved_plan_window[key])
                for key in (
                    "started_at",
                    "requested_seconds",
                    "latest_finished_at",
                )
            }

            if any (
                not math.isfinite(value) or value <= 0
                for value in saved_plan_window.values()
            ):
                raise ValueError("Invalid plan window")

            if (
                saved_plan_window["latest_finished_at"]
                <= saved_plan_window["started_at"]
            ):
                raise ValueError("Invalid latest finish.")

        if saved_wait_started_at is not None:
            saved_wait_started_at = float(saved_wait_started_at)

            if (
                not math.isfinite(saved_wait_started_at)
                or saved_wait_started_at <= 0
            ):
                raise ValueError("Invalid session start time")

        if not isinstance(plan, list) or not plan:
            raise ValueError("Invalid plan")

        for kind,minutes in plan:
            if kind not in ("focus", "break"):
                raise ValueError("Invalid session type")
            if type(minutes) is not int or minutes <= 0:
                raise ValueError("Invalid duration")

        if type(index) is not int or not 0 <= index < len(plan):
            raise ValueError("Invalid session index")

        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("Invalid elapsed time")

    except (ValueError, TypeError, KeyError) as error:
        print ("Could not restore timer: ", error)
        return

    timer.stop()
    active_plan = plan
    current_session_index = index
    session_type =  plan[index][0]
    started_at = None
    break_wait_started_at = saved_wait_started_at
    plan_window = saved_plan_window

    elapsed_before_pause = min(elapsed, get_session_duration())
    remaining_seconds = math.ceil(
        get_session_duration() - elapsed_before_pause
    )

    timer_label.setText(format_time(remaining_seconds))
    session_label.setText(f"{session_type.upper()} - PAUSED")

    colour = "#FBBF24" if session_type == "focus" else "#16803C"
    timer_label.setStyleSheet(f"color: {colour};")

    status_label.setText(
        f"Restored block {index + 1} of len {len(plan)}.\n"
        "Resume to continue, or Reset plan to discard."
    )

    start_button.setText("Resume!")
    start_button.setEnabled(True)
    pause_button.setEnabled(False)
    skip_button.setEnabled(True)

    for widget in (
        focus_input,
        break_input,
        available_time_input,
        preview_plan_button
    ):
        widget.setEnabled(False)

    preview_session_plan()
    print_plan_window()
    print(
        f"[RESTORE] time={time.strftime('%H:%M:%S')} "
        f"block={current_session_index + 1} "
        f"saved_elapsed={elapsed:.3f}s "
        f"restored_elapsed={elapsed_before_pause:.3f}s "
        f"remaining={remaining_seconds}s",
        flush=True
    )

def get_break_wait_seconds():
    if break_wait_started_at is None:
        return 0.0

    return max(0.0, time.time() - break_wait_started_at)

def get_break_buffer_seconds(break_minutes):
    if not 0 < break_minutes <= 120:
        raise ValueError("Break duration must be between 0 and 120 minutes.")

    if break_minutes < 10:
        return 10*60

    # (planned break minutes, extra buffer minutes)
    points = [
        (10,10),
        (15,10.5),
        (30,12),
        (60,15),
        (120,18)
    ]

    for (start, start_buffer), (end, end_buffer) in zip(
            points, points[1:]):
        if break_minutes <= end :
            fraction = (break_minutes - start) / (end - start)
            buffer_minutes = (
                start_buffer + fraction * (end_buffer - start_buffer)
            )
            return round(buffer_minutes * 60)

def is_break_review_due():
    if break_wait_started_at is None:
        return False

    if not 0 < current_session_index < len(active_plan):
        return False

    previous_type, previous_minutes = active_plan[current_session_index - 1]

    if previous_type != "break":
        return False

    buffer_seconds = get_break_buffer_seconds(previous_minutes)
    return get_break_wait_seconds() > buffer_seconds #  test overflow break

def check_break_review():
    if started_at is not None or not is_break_review_due():
        return

    #Identify this particular wait se we only ask once
    wait_id = str(break_wait_started_at)

    if settings.value("reviewed_break_wait", "", type= str) == wait_id:
        return

    # Remember before opening the popup to prevent repeated dialogs.
    settings.setValue("reviewed_break_wait", wait_id)
    settings.sync()

    dialog = QDialog(window)
    dialog.setWindowTitle("What happened?")
    dialog.resize(420,220)

    review_layout = QVBoxLayout(dialog)

    explanation = QLabel(
        "Your break has ended and you've been away a little longer. \n"
        "How would you like to continue?"
    )
    explanation.setWordWrap(True)
    review_layout.addWidget(explanation)

    review_layout.addWidget(QLabel("Reason (optional)"))

    reason_input = QComboBox()
    reason_input.addItems([
        "Prefer not to say",
        "Fall asleep",
        "Uregent work come up",
        "Needed a longer rest",
        "Got ditracted",
        "Office Work or something related office",
        "Somebody called you",
        "Other"
    ])
    review_layout.addWidget(reason_input)

    feedback = QLabel("")
    feedback.setWordWrap(True)
    review_layout.addWidget(feedback)

    continue_button = QPushButton("Continue plan")
    wait_button = QPushButton("Keep waiting")

    new_plan_button = QPushButton("Create a new plan")
    new_plan_button.setAutoDefault(False)

    new_plan_result = 2

    buttons = QHBoxLayout()
    buttons.addWidget(continue_button)
    buttons.addWidget(wait_button)
    buttons.addWidget(new_plan_button)
    review_layout.addLayout(buttons)

    continue_button.setAutoDefault(False)
    wait_button.setDefault(True)

    def submit_review(decision):
        if decision == "new_plan":
            answer = QMessageBox.question(
                dialog,
                "Replace unfinished plan?",
                "Discard the remaining schedule and prepare a new plan?\n\n"
                "Saved sessions, notes, and pending notes will be kept.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        reason = (
            reason_input.currentText()
            if reason_input.currentIndex() > 0
            else None
        )

        try:
            save_break_review(
                wait_id,
                reason,
                decision,
                get_break_wait_seconds(),
            )
        except sqlite3.Error as error:
            feedback.setText(
                "Could not save your choice. Please try again."
            )
            print("Could not save break review: ", error)
            return

        if decision == "continue":
            dialog.accept()
        elif decision == "new_plan":
            dialog.done(new_plan_result)
        else:
            dialog.reject()

    continue_button.clicked.connect(
        lambda: submit_review("continue")
    )
    wait_button.clicked.connect(
        lambda: submit_review("wait")
    )
    new_plan_button.clicked.connect(
        lambda : submit_review("new_plan")
    )

    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        start_focus()

    elif result == new_plan_result:
        reset_focus()

        if is_compact:
            toogle_compact()

        plan_preview.setText(
            "Choose your durations, then click Preview plan."
        )
        available_time_input.setFocus()

def get_remaining_plan_seconds():
    if not active_plan or current_session_index >= len(active_plan):
        return 0.0

    elapsed = elapsed_before_pause

    if started_at is not None:
        elapsed += time.monotonic() - started_at

    current_remaining = max(
        0.0,
        get_session_duration() - elapsed
    )

    future_seconds = sum(
        minutes * 60
        for kind, minutes
        in active_plan[current_session_index + 1:]
    )

    return current_remaining + future_seconds

def update_plan_finish_display():
    if not active_plan:
        plan_finish_label.setText(
            "Finish times will appear when you start a plan."
        )
        return

    if current_session_index >= len(active_plan):
        plan_finish_label.setText("Plan completed.")
        return

    now = time.time()
    expected_finish = now + get_remaining_plan_seconds()

    expected_text = time.strftime(
        "%d %b, %I:%M:%S %p",
        time.localtime(expected_finish)
    )

    heading = (
        "Expected finish"
        if started_at is not None
        else "Expected finish if resumed now"
    )

    if plan_window is None:
        latest_text = "Not available for this older plan"
        fit_message = "A deadline check is not available for this older plan."
    else:
        latest_finish = plan_window["latest_finished_at"]
        latest_text = time.strftime(
            "%d %b, %I:%M:%S %p",
            time.localtime(latest_finish)
        )
        spare_seconds = latest_finish - expected_finish

        if now >= latest_finish:
            fit_message = (
                "Deadline reached - the remaining plan needs review"
            )
        elif spare_seconds >= 0:
            spare_minutes = int(spare_seconds // 60)

            if spare_minutes == 0:
                fit_message = "Plan fits - less than 1 minute spare."
            else:
                fit_message = (
                    f"Plan fits - {spare_minutes} minutes spare."
                )
        else:
            overrun_minutes = math.ceil(-spare_seconds / 60)
            fit_message = (
                "Plan needs adjustment - expected finish is "
                f"about {overrun_minutes} min beyond the deadline. "
            )

    plan_finish_label.setText(
        f"{heading}: {expected_text}\n"
        f"Latest allowed finish: {latest_text}\n\n"
        f"{fit_message}"
    )
#testing function
def print_plan_window():
    if plan_window is None:
        print("No plan window stored.")
        return

    for key in ("started_at", "latest_finished_at"):
        readable_time = time.strftime(
            "%d %b %Y %H:%M:%S",
            time.localtime(plan_window[key])
        )
        print(f"{key}: {readable_time}")

def on_task_selected(index):
    task_id = task_selector.itemData(index)

    if task_id is None:
        task_name_input.setReadOnly(False)
        task_name_input.clear()
    else:
        task_name_input.setText(task_selector.itemText(index))
        task_name_input.setReadOnly(True)



#Simple Time conversion for refference
print(format_time(1500))
#print(format_time(1000))
print(format_time(90))
#print(format_time(7))
#print(format_time(0))
#print(format_time(125))

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
pending_log_sessions_ids = []
break_wait_started_at = None
plan_window = None

#app window creation
app = QApplication(sys.argv)

#
settings = QSettings("PiyushApps", "AdaptivePomodoroClock")

# adding Database table check -checks Schema each startup
initialize_tasks()
initialize_work_logs()


#app window settings
window = QWidget()
window.setWindowTitle("My Focus Clock")
window.resize(300, 650)

#history window linking
history_window = HistoryWindow(window)

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

plan_finish_label = QLabel(
    "Finish times will appear when you start a plan."
)
plan_finish_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
plan_finish_label.setWordWrap(True)

session_label = QLabel("FOCUS - READY")
session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
session_label.setStyleSheet(
    "font-size: 18px; font-weight: bold;"
)
start_button = QPushButton("Start!")
reset_button = QPushButton("Reset")
pause_button = QPushButton("Pause")
skip_button = QPushButton("Skip Session")
compact_button = QPushButton("Compact")
history_button = QPushButton("History")
focus_input = QSpinBox()

timer_font = QFont()
timer_font.setPointSize(40)
timer_font.setBold(True)

timer_label.setFont(timer_font)
timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

pause_button.setEnabled(False)
skip_button.setEnabled(False)

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
layout.addWidget(session_label)
layout.addWidget(timer_label)
layout.addWidget(status_label)
layout.addWidget(plan_finish_label)
layout.addWidget(start_button)
layout.addWidget(pause_button)
#layout.addWidget(skip_button)
layout.addWidget(compact_button)
layout.addWidget(focus_input)
layout.addWidget(break_input)
layout.addWidget(available_time_input)
layout.addWidget(preview_plan_button)
layout.addWidget(plan_preview)
layout.addWidget(history_button)


#Reset button window
reset_button.setText("Reset plan")

bottom_buttons = QHBoxLayout()
bottom_buttons.addWidget(skip_button)
bottom_buttons.addStretch()
bottom_buttons.addWidget(reset_button)

layout.addLayout(bottom_buttons)

#log window settings
log_window = QDialog(window)
log_window.setWindowTitle("Focus session notes")
log_window.resize(400,300)
log_window.setModal(False)

task_name_input = QLineEdit()
task_name_input.setPlaceholderText("What task were you working on?")

task_selector = QComboBox()
task_selector.addItem("New task / enter a name below", None)

for task in get_active_tasks():
    task_selector.addItem(task["name"], task["id"])



remarks_input = QTextEdit()
remarks_input.setPlaceholderText(
    "What did you complete, discover, or leave pending?"
)

log_layout = QVBoxLayout(log_window)
log_layout.addWidget(QLabel("Existing task"))
log_layout.addWidget(task_selector)
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

notes_autosave_timer = QTimer(window)
notes_autosave_timer.setSingleShot(True)
notes_autosave_timer.setInterval(500)

#connections
start_button.clicked.connect(start_focus)
reset_button.clicked.connect(confirm_reset)
pause_button.clicked.connect(pause_focus)
skip_button.clicked.connect(skip_session)
compact_button.clicked.connect(toogle_compact)
focus_input.valueChanged.connect(change_focus_duration)
break_input.valueChanged.connect(change_break_duration)
preview_plan_button.clicked.connect(preview_session_plan)
history_button.clicked.connect(show_history)
notes_autosave_timer.timeout.connect(save_pending_notes)
task_name_input.textChanged.connect(schedule_notes_autosave)
remarks_input.textChanged.connect(schedule_notes_autosave)
task_selector.currentIndexChanged.connect(on_task_selected)


#saved settings
focus_input.setValue(
    settings.value("focus_minutes", 25, type=int)
)
break_input.setValue(
    settings.value("break_minutes", 7, type=int)
)
available_time_input.setValue(
    settings.value("available_minutes", 90, type=int)
)
#save settings when the
app.aboutToQuit.connect(save_settings)

# testing
for minutes in (7,15,20,30,60,90,120):
    print(
        f"Break {minutes} min -> buffer"
        f"{get_break_buffer_seconds(minutes)}"
    )

example_remaining = [
    ("focus", 25),
    ("break", 7),
    ("focus", 25)
]

print(
    "Revised with 40 minutes:",
    build_revised_remaining_plan(example_remaining, 40 * 60)
)

print(
    "Revised with 30 minutes:",
    build_revised_remaining_plan(example_remaining, 30 * 60)
)

print(
    "Already worked 5 minutes; 20 minutes left:",
    build_revised_remaining_plan(
        example_remaining,
        20*60,
        elapsed_current= 5*60
    )
)

test_proposal = [("focus",2)]

print(
    "Proposal fits:",
    revised_plan_still_fits(
        test_proposal,
        elapsed_current = 2,
        latest_finish=1120,
        now=1000
    )
)

print(
    "Proposal become too late:",
    revised_plan_still_fits(
        test_proposal,
        elapsed_current = 2,
        latest_finish=1120,
        now=1003
    )
)

print(
    "Empty Proposal:",
    revised_plan_still_fits(
        [],
        elapsed_current = 0,
        latest_finish=1120,
        now=1000
    )
)

# window position and show
window.move(
    settings.value("window_position", window.pos())
)

#shoes the window
window.show()

# saves the last postion of the window
if settings.value("compact_mode", False, type= bool):
    toogle_compact()

# restore pending notes
restore_timer_state()
restore_pending_notes()

# added timer saved state after every 5 seconds
state_autosave_timer =QTimer(window)
state_autosave_timer.setInterval(5000)
state_autosave_timer.timeout.connect(save_timer_state)
state_autosave_timer.start()

#break overflow connection
break_review_timer = QTimer(window)
break_review_timer.setInterval(1000)
break_review_timer.timeout.connect(check_break_review)
break_review_timer.start()

#plan times for overflow
plan_display_timer = QTimer(window)
plan_display_timer.setInterval(1000)
plan_display_timer.timeout.connect(update_plan_finish_display)
plan_display_timer.start()

update_plan_finish_display()

#close the app
sys.exit(app.exec())




