# Adaptive Pomodoro Clock — Project Checkpoint

Last updated: 28 September 2026, Asia/Kolkata.
Owner and developer: Piyush Jain.
Purpose: Preserve scope, decisions, progress, and teaching approach if this conversation loses context.

## Resume instructions for the assistant

Read this document before continuing. This is a project checkpoint, not a replacement for the latest source code. Piyush is doing the coding in PyCharm and wants to continue learning in this same chat. Ask for current code when a change depends on unseen edits; do not assume the historical snippets are the latest version.

Continue from the working countdown, pause/resume, and reset. The immediate next task is a larger centred countdown, always-on-top behaviour, and transparency, followed by compact mode. Do not restart the project or jump straight to a complete generated application.

## Goals and working agreement

- Build a useful personal productivity clock for a Linux laptop.
- Practise Python through the real application.
- Piyush initially requested no code, then explicitly accepted small, explained GUI examples while writing and learning the logic himself.
- Teach incrementally: explain one concept, give a manageable change or exercise, review his code, and proceed after it works.
- Balance learning with getting a usable clock soon. Avoid lengthy documentation prerequisites or repeated trivial quizzes that stall progress.
- Piyush calls the assistant Airi.
- This clock is separate from the Family AI Planner; do not merge their scope.

## Environment and source of truth

| Item | Current information |
| --- | --- |
| OS | Linux Mint |
| Desktop | Cinnamon |
| Display session | X11 |
| Language | Python |
| IDE | PyCharm |
| GUI framework in use | PySide6 / Qt Widgets |
| Source backup | User reported updating the project on GitHub on 28 September 2026 |
| Repository URL, branch, commit | Not provided; assistant has not inspected the repository |
| Latest full source | Lives in the user's project; latest pause/resume integration was reported working but not pasted in full |

## Feature scope and status

| Feature | Intended behaviour | Status |
| --- | --- | --- |
| Desktop GUI | Main window for timer, task entry, settings, plans, and history | Basic window implemented |
| Countdown | Display MM:SS; stop at zero without negative values | User reports working |
| Start | Begin a session; repeated clicks must not restart it | User reports working |
| Pause/resume | Freeze work time; exclude paused time; resume with accumulated progress | User reports working |
| Reset | Stop the timer and restore the full duration | Fixed and confirmed working |
| Skip | Skip a focus or break block, preserve partial history, and adjust the remaining plan | Planned |
| Larger readable display | Large centred countdown | Next |
| Always-on-top | Remain above ordinary application windows | Next; test fullscreen behaviour separately |
| Transparency | Adjustable opacity with readable digits | Next; whole-window opacity versus translucent background remains an implementation choice |
| Compact widget | Small draggable, resizable view with countdown, task, mode, and essential controls | Planned |
| Return to full view | Expand without interrupting or duplicating the timer | Planned |
| Adjustable durations | Configure focus durations and minimum break | Planned |
| Budget-based planning | Divide a supplied time budget into focus and break blocks | Planned |
| Longer breaks | Suggest longer recovery after accumulated work, considering actual breaks | Planned |
| Time awareness | Use time of day, daily work history, and remaining budget | Planned |
| Task tracking | Record intended task/outcome, actual progress, and notes | Planned |
| Excel connection | User can enter task information; application records work sessions | Planned |
| Session history | Store planned/actual focus, breaks, pauses, skips, and outcomes | Planned |
| Daily summaries | Show progress and focus/break totals | Planned |
| Adaptive suggestions | Learn which patterns seem useful for the user | Planned |
| Recovery and sleep | Recover interrupted sessions; do not misclassify laptop sleep as focus | Planned, not handled by the basic timer alone |

## Current implementation checkpoint

The application is currently a small procedural script using functions and module-level state. A later class refactor can be a learning step; it is not required before the next visual improvement.

Imports in use: sys, time, math; QApplication, QWidget, QLabel, QPushButton, QVBoxLayout; QTimer.

Known functions:

- format_time(total_seconds): minutes = total_seconds // 60; seconds = total_seconds % 60; returns an f-string with two-digit fields.
- start_focus(): records a fresh monotonic start time, changes status, disables Start, enables Pause, refreshes the display, and starts QTimer.
- update_countdown(): calculates elapsed work, derives remaining seconds, updates the label, and stops at zero.
- pause_focus(): stores elapsed work before clearing started_at, stops refreshes, enables Start labelled Resume, and disables Pause.
- reset_focus(): stops refreshes, clears timing state, restores duration and button states.

State:

| Variable | Meaning |
| --- | --- |
| focus_duration | Full duration in seconds; 10 seconds used for testing; intended initial normal value 25 * 60 |
| remaining_seconds | Integer shown through format_time |
| started_at | Monotonic timestamp for the current running segment, or None |
| elapsed_before_pause | Floating-point seconds accumulated across earlier running segments; initially 0.0 |

Timing design:

1. QTimer requests display updates every 100 milliseconds via timeout.connect(update_countdown).
2. It is a refresh mechanism, not the source of elapsed time.
3. While running: elapsed_seconds = elapsed_before_pause + (time.monotonic() - started_at).
4. remaining_seconds = max(0, math.ceil(focus_duration - elapsed_seconds)).
5. Paused wall time is excluded by recording a new started_at on resume.
6. No time.sleep() in the GUI thread and no subtraction of one second per refresh.
7. Completion stops QTimer, shows Focus Complete, disables Pause, and requires Reset before a new session in the current design.

Known corrections already made:

- Removed duplicate window.show() and used app.exec().
- Fixed seconds calculation to total_seconds % 60.
- Used return, not print, in format_time so the GUI can consume its result.
- Reset initially missed remaining_seconds = focus_duration; user added it and confirmed the fix.
- Reset for pause/resume also clears elapsed_before_pause and started_at.

Verification reported by user: countdown, Reset, and pause/resume are working. This is user confirmation, not an independent execution by the assistant. No current full-source audit or automated test suite has been performed.

## Planning behaviour

The user supplies time, tasks, and a minimum break (example: 7 minutes). The clock should suggest a distribution, support manual adjustment, and eventually personalise it.

An unresolved decision: whether a time entry such as 100 minutes means total available time including breaks or focus time excluding breaks. Proposed design: support both, default to including breaks. The user's general acknowledgement did not explicitly choose this default; confirm when implementing the planner.

Example plans for 100 total minutes (illustrative, not scientifically optimal):

| Pattern | Distribution | Total |
| --- | --- | --- |
| Short blocks | 20 focus, 7 break, 20 focus, 7 break, 20 focus, 7 break, 19 focus | 100 minutes |
| Medium blocks | 28 focus, 7 break, 28 focus, 7 break, 30 focus | 100 minutes |
| Long blocks | 43 focus, 14 break, 43 focus | 100 minutes |

Planning constraints proposed:

- Automatic plans never shorten a break below the user minimum; explicit user skip remains available.
- Track focus since a substantial break as well as total focus today.
- Longer-break thresholds are configurable product rules, not medical recommendations. An initial example was a 15–20 minute break after roughly 90 accumulated focus minutes with only short breaks.
- Do not silently extend an agreed finish time. If a pause or longer break changes the budget, offer less remaining focus or a later finish.
- If a useful focus block and required break cannot fit, offer to finish or extend.
- Distinguish preserving an end time from preserving all target focus minutes.
- Do not assume every pause is a restful break, or that all work happens inside the app.

## Learning and adaptation

Start with rules and simple history statistics; no LLM or complex ML is required initially.

Potential inputs:

- Task category (coding, studying, writing, administration).
- Intended small outcome.
- Time of day and optional energy level.
- Planned and actual duration, pauses, skipped sessions, and breaks.
- Optional outcome feedback: done, some progress, blocked.
- Optional duration feedback: too short, comfortable, too long.
- Optional interruption reason to distinguish external interruption, tiredness, or early task completion.

Adaptation principles:

- Timer elapsed time is not proof of attention or productivity.
- Learn from repeated observations, not one unusual session.
- Prefer recent history, retain user limits, and adjust gradually.
- Short blocks or long blocks are hypotheses to evaluate, not universal goals.
- Explain suggestions in plain language and allow manual overrides, fixed schedules, and preference reset.
- Optimise meaningful progress and sustainable use, not maximum sitting time.
- Minimum data requirements, exact scoring, and model selection remain undecided.

## Data and Excel proposal

Proposed architecture, not implemented: SQLite as the reliable local record; openpyxl for Excel (.xlsx) import/export.

Suggested workbook sheets:

| Sheet | Contents |
| --- | --- |
| Tasks | Stable task ID, description, category, intended outcome, status, notes |
| Sessions | Stable session ID, linked task, planned/actual timing, pauses, skips, outcome |
| Daily Summary | Focus totals, breaks, outcomes, feedback |
| Manual Activity | Work or breaks outside the timer |

Begin with explicit Import tasks and Sync to Excel actions. Define ownership of editable fields, preserve user notes, and use stable IDs to avoid duplicates. Retain pending records if the workbook is open or a conflict occurs. Exact schema and sync conflict rules are not yet designed.

Once history exists, Reset must preserve a partial attempt rather than erase recorded work. The current prototype only resets in-memory state because persistence is not built yet.

## Delivery sequence

1. Basic GUI, countdown, start/reset, pause/resume — achieved as user-reported prototype.
2. Larger centred display, always-on-top, transparency — immediate next step.
3. Compact floating mode sharing the same timing state.
4. Configurable focus/break cycles, session transitions, skip.
5. Reliable local history and recovery, task entry, Excel integration.
6. Budget-based planning and daily longer-break rules.
7. Adaptive suggestions based on actual recorded history.

Implementation order can be refined with Piyush; do not treat future features as already present.

## Next-session checklist

- Resume with visual changes, not a new timer implementation.
- Explain Qt alignment/font/window settings in small pieces.
- Make always-on-top and transparency changes before showing the window where appropriate.
- Test on the user's Cinnamon/X11 desktop; do not guarantee behaviour over every fullscreen app.
- Keep timer state shared when adding the compact view; do not create a second countdown.
- Ask for current code if needed; GitHub has been mentioned but no repository location or access was supplied.
- After each meaningful milestone, update this checkpoint and recommend a Git commit.

## Checkpoint maintenance

This document captures the conversation through 28 September 2026, approximately 15:51 IST. Later user instructions and verified current source take precedence. Update the date, statuses, decisions, and next action when the project advances. Do not replace unknown details with guesses or mark planned functionality complete without evidence.
