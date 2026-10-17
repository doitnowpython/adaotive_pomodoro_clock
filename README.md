# Adaptive Pomodoro Clock

A Python desktop focus clock being built for personal productivity and, later, family use. It combines timed focus sessions, breaks, session history, and notes about the work completed.

The long-term goal is to keep ongoing tasks connected across sessions and plans, reduce repeated data entry, and suggest work and recovery schedules using task demands and user-reported fatigue.

**Status:** Active development. The core timer, session logging, linked notes, History window, and daily summary are working. Task-based adaptation, recovery, and family profiles are planned.

**Roadmap updated:** 16 October 2026.

## Working features

- Adjustable focus and break durations; defaults of 25 and 7 minutes.
- Available-time planning with a preview of focus and break blocks.
- A shorter final focus block when required by the plan.
- Automatic transitions between focus and break sessions, followed by a stop when the plan finishes.
- Start, pause/resume, Skip Session, and Reset with confirmation.
- Elapsed-time calculation using a monotonic clock, excluding pauses.
- Always-on-top window, transparency, and Compact/Expand modes.
- Distinct focus/break labels and colours, plus session numbering.
- Session chime and desktop notifications where supported.
- SQLite records for completed and skipped focus/break sessions.
- Planned duration, actual active duration, and save timestamp for each recorded session.
- Task-name and remarks forms linked to individual focus-session IDs.
- An in-memory queue that preserves the association of unfinished notes when another focus session ends.
- Notes window closes after the final pending note saves successfully; errors keep the form available.
- History window showing the latest 20 sessions, with Refresh and full-row selection.
- Read-only viewing of notes for a selected session.
- Daily focus summary: saved focus time, completed focus count, and skipped focus count.
- IST display, including conversion of older UTC timestamps.

The daily-summary display and row-selection changes were confirmed locally by the author on 16 October 2026. Ensure those code changes are committed alongside this README.

## Technology

| Component | Technology |
| --- | --- |
| Application | Python |
| Desktop interface | PySide6 / Qt Widgets |
| Timer refresh | QTimer |
| Active-time measurement | `time.monotonic()` |
| Storage | SQLite through Python's `sqlite3` module |
| Sound | Qt Multimedia / QSoundEffect |
| Time zones | Python `datetime` and `zoneinfo` |

The development environment is Linux Mint Cinnamon on X11, using PyCharm. Other operating systems have not yet been verified.

## Getting started

Use Python 3.12 or newer for the development setup. Dependency versions are not yet pinned.

```bash
git clone https://github.com/doitnowpython/adaotive_pomodoro_clock.git
cd adaotive_pomodoro_clock
python3 -m venv clock_env
source clock_env/bin/activate
python -m pip install PySide6
python main.py
```

Keep `sound/session_chime.wav` in its existing location. Desktop notifications depend on the desktop environment's system-tray support.

### Basic workflow

1. Set focus minutes, break minutes, and available minutes.
2. Click **Preview plan** to inspect the proposed blocks and any unused time.
3. Click **Start**. The clock runs the plan automatically.
4. Use **Pause/Resume**, **Skip Session**, or **Reset plan** as needed.
5. After a focus session, enter its task name and remarks. If several sessions are waiting, saving advances the same form to the next pending session.
6. Open **History** to view session records and today's focus summary.
7. Select a row and click **View Notes** to read its saved notes. Click **Refresh** to update history and the summary.

## Project structure

| Path | Responsibility |
| --- | --- |
| `main.py` | Application setup, timer state, plan execution, main controls, and note-entry flow |
| `database.py` | Session storage, schema initialization, history queries, note retrieval, and daily-summary query |
| `history_window.py` | History interface, daily-summary display, and notes viewer |
| `database_fetch.py` | Development helper for inspecting records; currently contains a machine-specific database path |
| `sound/session_chime.wav` | Session-transition sound |
| `Pomodoro_Clock_Project_Checkpoint.md` | Earlier project checkpoint; may not reflect the latest progress |
| `pomodoro.db` | Local runtime data, created by the application |

Some work-log SQL and plan-building logic remain in `main.py`. Further separation will happen gradually while preserving working behaviour.

## Data and current limitations

- `sessions_records` stores timing records and outcomes; `work_logs` stores notes linked through `session_id`.
- Data is stored locally in `pomodoro.db` beside the application files. No account or cloud synchronization is implemented.
- Older notes can have an empty `session_id`; the app does not guess which session they belonged to.
- A task name in a note is not yet a reusable task. Cross-plan task grouping is still planned.
- Settings, active plans, pending-note queues, and unsaved drafts are not yet restored after closing the app.
- Resetting an active block does not currently save it as an interrupted session.
- Laptop-sleep behaviour and crash recovery need further work.
- Failed session saves are reported in the console; automatic retry and durable recovery are not implemented.
- History displays the latest 20 sessions. Browsing all records and date/task filters are planned.
- Daily totals include active time from both completed and skipped focus sessions. Breaks and the currently running block are excluded.
- A session's entire duration is assigned to its save date in IST. Sessions crossing midnight are not split between days.
- The daily summary updates when History opens or Refresh is clicked; it is not a live counter.
- Available time includes breaks. The planner can leave time unused when a full break would leave no time for another focus block.
- Pauses currently extend the wall-clock finish time; a fixed finish deadline is not enforced.
- The break control currently permits values below seven minutes. A mandatory minimum-break rule has not been finalized.
- Current session transitions auto-start the next block. The proposed fatigue-aware readiness checks are not implemented yet.

### Keep personal data out of Git

The database can contain personal task names and remarks. Keep it and its SQLite sidecar files out of version control. Suggested root `.gitignore` entries:

```gitignore
pomodoro.db*
clock_env/
.venv/
__pycache__/
*.py[cod]
```

Adding an ignore rule does not untrack a file already committed. Review `git status` before staging changes.

## Planned task-based workflow

The next major data-model improvement is a reusable task with a permanent ID.

| Item | Purpose |
| --- | --- |
| Task | Ongoing work, with reusable details and progress |
| Plan | A particular available-time budget or future time range |
| Session | One focus or break block; focus blocks can reference a task |
| Session note | What changed during that specific focus block |

Multiple focus sessions across plans and days will share a task ID. Their durations will remain separate while task totals are grouped together.

At plan creation, the user will choose an existing task or create one. After focus, the proposed choices are **Continue task**, **Switch task**, and **Task completed**, with optional notes. Continuing will reuse the task's details without copying old remarks into new records.

### Planned task details

- **Category:** Learning, Work, Home, Shopping/Admin, Personal.
- **Activity:** Learning, Practising/Creating, Researching/Deciding, Organising/Cleaning, Reflecting.
- **Methods, allowing multiple selections:** Video/Audio, Reading, Writing/Typing, Hands-on.
- **Reported mental and physical effort:** Separate ratings rather than a single combined score.
- **Progress:** Optional completion percentage, findings, pending work, and a concrete next action.
- **Task demands:** Screen exposure, concentration, hand use, prolonged posture, standing/walking, lifting/repetition, and emotional effort.

Choices are an initial design, not a finalized taxonomy. Completion percentage will remain optional for open-ended work such as journaling or research.

## Planned work and recovery behaviour

The clock will choose break durations using task demands, recent work, and brief user feedback. Users will be able to report **Okay**, **Tired**, or **Pain/discomfort**, with one or more affected areas.

Design goals:

- Use feedback rather than claiming to measure fatigue from timer data alone.
- Account for eyes, hands/wrists, neck/back, legs/feet, general physical effort, concentration, and emotional effort.
- Consider all reported areas together before suggesting a break activity or another task.
- Preserve the current task and its next action to make returning easier.
- Distinguish needing more recovery from finding it difficult to restart.
- Do not shorten future breaks merely because the user returned late.
- Suggest alternative tasks with suitable demands while respecting priorities and avoiding endless switching.
- Pause the relevant demanding activity when pain is reported; do not treat an expired countdown as proof of recovery.
- Keep pause/stop controls available. Task switching remains a suggestion.

This is a productivity feature, not a medical assessment. The app will not diagnose symptoms, prescribe exercises, or guarantee that a break duration prevents pain or injury. Initial durations will be product defaults to evaluate, not medically validated recovery prescriptions.

## Remaining roadmap and effort estimates

Estimates are additional hands-on development hours at the current learning pace, including explanations, implementation, and ordinary debugging. They are not delivery commitments.

| Section | Remaining work | Hours |
| --- | --- | ---: |
| Remember settings | Restore durations, available time, and display preferences | 1–2 |
| Reusable tasks | Persistent task IDs, continuation across plans, grouped progress and totals | 4–7 |
| Richer task/session details | Categories, activities, methods, effort, progress, findings, and next actions | 3–5 |
| Preserve unfinished notes | Durable drafts and queues, restoration, and access to pending notes | 3–5 |
| Timer recovery and timing records | Interrupted plans, sleep handling, start/end times, and pauses | 4–7 |
| Task demands and recovery rules | Fatigue feedback, automatic break selection, recovery checks, and pain-related pause behaviour | 6–10 |
| Adaptive work and suggestions | Focus-length adjustment, suitable task suggestions, priority handling, and return support | 4–7 |
| Time-range scheduling | Finish deadlines, expected end time, and replanning after pauses/skips | 4–7 |
| History improvements | Edit notes, browse older records, filters, and task totals | 2–4 |
| Excel support | Export records/notes and validate a defined import format | 3–5 |
| Companion and reminders | Gentle feedback, review prompts, and next-action reminders | 3–6 |
| Basic family profiles | Separate tasks, history, settings, and feedback on one shared installation | 5–9 |
| Reliability checks | Failed-save handling, duplicate prevention, reset/exit behaviour, and end-to-end checks | 3–5 |
| Cleanup and easy launching | Code organization, setup documentation, dependencies, launcher, and release preparation | 2–4 |
| **Total** | **Expanded standalone clock, including basic family profiles** | **47–83** |

- **Dependable daily-use milestone:** approximately **11–19 hours** for settings, unfinished notes, timer recovery, and reliability.
- **Planning allowance for the expanded clock:** **60–100 hours**, including contingency for harder bugs and design changes. This includes the daily-use milestone; it is not additional to it.
- At five focused development hours per week, the planning allowance is approximately **12–20 weeks**.

Recommended sequence: remember settings; introduce reusable tasks and richer details; strengthen persistence and recovery; add adaptive suggestions; then expand family use. Estimates will be revised as these sections are specified and tested.

## Family use and future Family Planner integration

Basic family profiles mean selectable users on a single installation. They are not, by themselves, strong privacy or access-control boundaries.

Shared data across devices, authentication, permissions, household scheduling, and automatic task assignment are outside the estimates above.

The intended integration sequence is:

1. Complete and validate the standalone clock.
2. Complete and accept the separately approved Family AI Planner V1 scope.
3. Design the integration explicitly, including identities, permissions, task ownership, and synchronization.

The proposed responsibility split is that Family Planner manages household tasks, schedules, and approved assignments, while the clock runs focus sessions and records progress. Stable user/task/session IDs and an authenticated interface would connect them. This is a future proposal, not an implemented integration or a change to the locked Family Planner V1 scope.

## Next checkpoint

Remember focus duration, break duration, and available time between application launches. Keep implementing and verifying one small checkpoint at a time.
