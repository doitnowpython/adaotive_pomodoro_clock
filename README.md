# Adaptive Pomodoro Clock

A Python desktop focus clock being built for personal productivity and, later, family use. It combines timed focus sessions, breaks, session history, and notes about the work completed.

The long-term goal is to keep ongoing tasks connected across sessions and plans, reduce repeated data entry, and suggest work and recovery schedules using task demands and user-reported fatigue.

**Status:** Active development. The core timer, logging, linked notes, History window, daily summary, saved preferences, draft autosave, and basic timer recovery are working. Recovery accuracy still has a known issue. Sleep/lock interruption handling, task-based adaptation, and family profiles remain planned.

**Roadmap updated:** 20 October 2026.

This README combines the existing GitHub roadmap with author-reported tests and design decisions through 20 October. Some locally tested corrections may be ahead of the latest pushed code. Features explicitly marked **planned** below are not yet implemented.

## Working features

- Adjustable focus and break durations; defaults of 25 and 7 minutes.
- Available-time planning with a preview of focus and break blocks.
- A shorter final focus block when required by the plan.
- Currently, automatic transitions between focus and break sessions, followed by a stop when the plan finishes. The planned interruption flow will require confirmation before the next focus starts after a break.
- Start, pause/resume, Skip Session, and Reset with confirmation.
- Elapsed-time calculation using a monotonic clock, excluding pauses.
- Always-on-top window, transparency, and Compact/Expand modes.
- Distinct focus/break labels and colours, plus session numbering.
- Session chime and desktop notifications where supported.
- SQLite records for completed and skipped focus/break sessions.
- Planned duration, actual active duration, and save timestamp for each recorded session.
- Task-name and remarks forms linked to individual focus-session IDs.
- A pending-notes queue that preserves the association of unfinished notes when another focus session ends.
- Draft text and pending session IDs persist across reopening; drafts autosave after approximately 500 ms without typing, and queue changes save immediately.
- After the last pending note saves, a confirmation remains for 1.5 seconds before the window closes. Editing is disabled during confirmation and enabled for the next pending note. Validation and save errors keep the form available.
- History window showing the latest 20 sessions, with Refresh and full-row selection.
- Read-only viewing of notes for a selected session.
- Daily focus summary: saved focus time, completed focus count, and skipped focus count.
- IST display, including conversion of older UTC timestamps.
- Focus, break, and available-time preferences restored through QSettings.
- Compact mode and approximate window position restored.
- Unfinished plans restored paused, preserving the current block and elapsed time.
- Timer-state saving on normal exit and state changes, with a five-second periodic autosave intended to support unexpected-close recovery. See the accuracy issue below.

Settings and draft persistence were tested by the author on 17 October. Normal-exit and unexpected-close timer recovery were tested on 19–20 October. On 20 October, the periodic autosave setup was moved out of the restore function so it also starts on fresh launches; the restore checks were corrected to reject `index == len(plan)` and allow zero elapsed seconds. These corrections were confirmed locally, but a remaining recovery-timing discrepancy is still open.

## Technology

| Component | Technology |
| --- | --- |
| Application | Python |
| Desktop interface | PySide6 / Qt Widgets |
| Timer refresh | QTimer |
| Active-time measurement | `time.monotonic()` |
| Session and note storage | SQLite through Python's `sqlite3` module |
| Preferences, drafts, and recovery snapshots | Qt QSettings; structured state serialized as JSON |
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
3. Click **Start**. The current implementation runs the plan automatically; the planned manual-start behaviour after breaks is described below.
4. Use **Pause/Resume**, **Skip Session**, or **Reset plan** as needed.
5. After a focus session, enter its task name and remarks. If several sessions are waiting, saving advances the same form to the next pending session.
6. Open **History** to view session records and today's focus summary.
7. Select a row and click **View Notes** to read its saved notes. Click **Refresh** to update history and the summary.
8. On reopening an unfinished plan, use **Resume** to continue or **Reset plan** to discard it. Reopening currently excludes time while the application was closed; sleep-aware timing is a separate planned change.

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
- Session records and saved notes are stored locally in `pomodoro.db` beside the application files. Preferences, pending drafts, and timer snapshots are stored separately in QSettings. Backing up the database alone does not preserve all application state. No account or cloud synchronization is implemented.
- Older notes can have an empty `session_id`; the app does not guess which session they belonged to.
- A task name in a note is not yet a reusable task. Cross-plan task grouping is still planned.
- Settings, active plans, pending-note queues, and drafts now restore after closing. Timer recovery reopens paused; it does not resume automatically.
- Resetting an active block does not currently save it as an interrupted session.
- **Known bug — recovery accuracy:** after an unexpected stop, the recovered countdown has differed by roughly 2–7 seconds and sometimes more than 10 seconds in author testing. A five-second autosave interval is not a proven maximum-loss guarantee. Record this as unresolved and investigate save timing, event-loop delays, and restored values.
- Laptop-sleep and screen-lock handling are not implemented. A stopped Python process cannot sound an alarm while the laptop is suspended.
- Database writes and QSettings snapshots are separate operations. Crash-safe duplicate prevention and reconciliation at session transitions still need work.
- Restored window position may be nearby rather than pixel-exact; this is accepted for now.
- Failed session saves are reported in the console; automatic retry and durable recovery are not implemented.
- History displays the latest 20 sessions. Browsing all records and date/task filters are planned.
- Daily totals include active time from both completed and skipped focus sessions. Breaks and the currently running block are excluded.
- A session's entire duration is assigned to its save date in IST. Sessions crossing midnight are not split between days.
- The daily summary updates when History opens or Refresh is clicked; it is not a live counter.
- Available time includes breaks. The planner can leave time unused when a full break would leave no time for another focus block.
- Pauses currently extend the wall-clock finish time; a fixed finish deadline is not enforced.
- The break control currently permits values below seven minutes. A mandatory minimum-break rule has not been finalized.
- Current session transitions auto-start the next block. The manual focus-start, interruption-review, and fatigue-aware readiness checks described below are planned.

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

## Planned sleep, lock, pause, and interruption handling

**Agreed on 20 October 2026; not implemented yet.** These rules extend the existing clock roadmap. They do not change the locked Family Planner V1 scope.

### Keep system power settings unchanged

- Do not schedule laptop wake-ups or modify sleep, lock, or power settings.
- Do not require the clock to run as root.
- Before a focus session starts, show its planned duration, expected finish time, and a reminder to set a phone backup timer if the laptop may sleep. This applies to manually configured and application-generated focus durations.
- Provide **Start focus** and **Cancel**; start counting only after confirmation.
- Show the session deadline, not a guessed laptop sleep deadline. Automatic sleep depends on the desktop configuration and activity.

### Count elapsed schedule time through sleep

When the laptop sleeps, the application cannot execute transitions or play sound. On resume, it will reconcile the schedule against real-world timestamps:

1. Let the active focus and its immediately following planned break elapse according to their deadlines.
2. Mark those blocks completed if their allocated time has passed. If the plan has no following break, do not invent one.
3. Do not automatically run through additional focus sessions. Stop before the next focus and wait for the user.
4. If the following break has not yet ended, show its remaining time; otherwise calculate extra time since its scheduled end.
5. Keep elapsed schedule time and sleep/away time distinguishable from confirmed focused work in records and summaries.

Example: focus ends at 2:25 PM, its break ends at 2:32 PM, and the user returns at 3:00 PM. The focus and break have elapsed, the next focus has not started, and extra time away is 28 minutes.

The same waiting/review flow applies when the screen is locked or the user does not respond after a break ends. The next focus requires a Start click. Normal focus-to-break progression remains planned; automatic break-to-focus progression will change.

### Hidden extra-time buffer

The buffer is an internal threshold for asking what happened. It is **not displayed to the user**, added to the displayed break, or treated as permission to automatically start another focus session.

| Allocated break | Initial buffer rule | Extra time before review |
| --- | --- | --- |
| 10 minutes or less | Fixed allowance | 10 minutes |
| 15 minutes | 70% of the allocated break | 10 minutes 30 seconds |
| 30 minutes | 40% of the allocated break | 12 minutes |
| 60 minutes | 25% of the allocated break | 15 minutes |
| 120 minutes | 15% of the allocated break | 18 minutes |

These are agreed starting examples/default anchors, not a finished scheduling algorithm. Above 10 minutes, the percentage decreases as the break grows, while extra minutes may increase. **There is no fixed ten-minute cap.** The interpolation between anchors and treatment of breaks above 120 minutes must be specified before implementation; avoid abrupt threshold jumps.

After a scheduled break ends, track extra time silently. Once the buffer is exceeded, offer an interruption review. If the laptop is asleep, perform this check when it resumes; do not wake it. If locked, present the actionable review when the user can interact, without bypassing the lock screen.

Later, the clock may adjust buffers using whole-day activity, task demands, fatigue feedback, and interruption history. Keep adjustments bounded and user-overridable/resettable. Repeated overruns alone must not automatically justify ever-longer buffers.

### Interruption review and replanning

Ask **“What happened, and how would you like to continue?”** An optional reason can include fell asleep, urgent work, longer rest, or another reason.

Offer three choices:

1. **Continue the remaining plan unchanged:** retain the unfinished session lengths and move the finish time later.
2. **Recalculate the remaining plan:** account for elapsed time and completed blocks, then fit remaining focus/break blocks into the original planned finish time. If that deadline has passed, request a new available-time budget. Preserve existing completed records and avoid creating duplicate sessions.
3. **Create a new plan:** retain completed records and replace the unfinished schedule.

Explicit **Pause** freezes the countdown and records interruption time separately. A long pause should offer the same review choices on resume; paused time must not silently become focused work. The exact pause-review threshold needs a separate definition because a focus pause has no allocated break duration to use as its percentage base.

### Alarm behaviour

- During a locked-but-awake session, support a louder repeating chime until the user dismisses it, with an adjustable volume and a **Stop alarm** control.
- A suspended laptop cannot play the chime. Reconcile elapsed sessions and notify on wake; the phone timer is the backup while asleep.
- Dismissing an alarm must not automatically start another focus session.
- Keep interruption prompts and the alarm from duplicating themselves on repeated timer callbacks or resume events.
- Finalize alarm timing across an unattended focus-to-break transition during implementation; do not let the alarm prevent the planned break from elapsing.

### Implementation sequence

1. Make break completion prepare the next focus without starting it; use Start to continue.
2. Record session deadlines and distinguish waiting, running, paused, and completed states.
3. Add the focus-start reminder and optional phone backup prompt.
4. Reconcile elapsed focus/break blocks after sleep and detect lock/away states.
5. Add hidden-buffer calculation and interruption review, then the three continuation/replanning choices.
6. Apply equivalent review to explicit pauses with a defined threshold.
7. Add the repeating alarm, dismissal, volume control, and workflow checks.
8. Investigate recovery accuracy and harden database/snapshot consistency.

## Roadmap status and earlier effort estimates

**Estimate baseline: 16 October 2026.** The original table is retained for scope continuity, but its hours and totals are historical, not a current remaining-work estimate. Settings, draft persistence, and basic timer recovery have since been implemented; the new interruption design adds work. A fresh estimate is needed after that design is broken into tested steps. Development time includes reading, explanations, implementation, and debugging; a recent recovery change took over an hour despite a 30-minute target.

Current progress against that baseline:

- **Settings:** core duration and display preferences implemented; exact window positioning remains a minor limitation.
- **Unfinished notes:** draft/queue persistence and autosave implemented; further failure/reconciliation checks remain.
- **Timer recovery:** normal-exit and periodic snapshot recovery implemented; accuracy is an open bug, and sleep/lock handling plus richer timing records remain.
- **Other sections:** retained below as planned work. The interruption rules belong to timer recovery, time-range scheduling, and reliability; do not count them as completed or add overlapping estimates twice.

| Section | Original scope (see progress above) | Original hours |
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
| **Historical total** | **Original expanded standalone clock scope, including basic family profiles** | **47–83** |

- The earlier **11–19-hour daily-use milestone** covered settings, unfinished notes, timer recovery, and reliability. Parts are now done, so this is not the remaining duration.
- The earlier expanded-clock planning allowance was **60–100 hours**, including contingency and the daily-use milestone. It has not been recalculated for the new requirements.
- The earlier **12–20 weeks at five hours/week** illustration was based on that historical allowance, not a current delivery forecast.

Current sequence: strengthen recovery and implement the interruption flow in small checkpoints; introduce reusable tasks and richer details; add adaptive suggestions; then expand family use. Retain all original scope items. Difficulty ratings, gentle happy/grumpy companion feedback, and the previously discussed ten-minute review/form prompt remain in the richer-log and companion backlog; their exact interaction design still needs clarification. Estimates will be revised as sections are specified and tested.

## Family use and future Family Planner integration

Basic family profiles mean selectable users on a single installation. They are not, by themselves, strong privacy or access-control boundaries.

Shared data across devices, authentication, permissions, household scheduling, and automatic task assignment are outside the estimates above.

The intended integration sequence is:

1. Complete and validate the standalone clock.
2. Complete and accept the separately approved Family AI Planner V1 scope.
3. Design the integration explicitly, including identities, permissions, task ownership, and synchronization.

The proposed responsibility split is that Family Planner manages household tasks, schedules, and approved assignments, while the clock runs focus sessions and records progress. Stable user/task/session IDs and an authenticated interface would connect them. This is a future proposal, not an implemented integration or a change to the locked Family Planner V1 scope.

## Next checkpoint

**Prepare the next focus after a break, but wait for the user to click Start.** Preserve focus-to-break progression and completed records. Then implement the internal buffer and interruption review in separate checkpoints.

Keep the unexpected-close recovery timing discrepancy on the known-bug list. Do not change laptop power settings or add wake-up scheduling. Work in short sessions with one concrete outcome and a small verification checklist.
