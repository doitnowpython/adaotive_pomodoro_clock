# Adaptive Pomodoro Clock

A Python desktop focus clock being built for personal productivity and, later, family use. It combines timed focus sessions, breaks, session history, and notes about the work completed.

The long-term goal is to keep ongoing tasks connected across sessions and plans, reduce repeated data entry, and suggest work and recovery schedules using task demands and user-reported fatigue.

**Status:** Active development. The core timer, logging, linked notes, History window, daily summary, saved preferences, draft autosave, post-break waiting, hidden-buffer checks, interruption reviews/history, and Create a new plan are implemented. Fixed plan deadlines, revised-plan previews, Apply and resume, and the corrected active-plan display are now implemented. Normal pause → close → reopen recovery was confirmed by the author on 26 October. Unexpected-close recovery accuracy, sleep/lock reconciliation, task-based adaptation, and family profiles remain open.

**Roadmap updated:** 26 October 2026.

This README reflects code through commit `c0691e1` (Fix active plan preview after revision and restore), author-reported tests through 26 October, and the retained scheduling decisions agreed on 20–22 October. Features explicitly marked **planned** below are not yet implemented. Completed portions of earlier designs are identified separately from remaining work.

The complete previous README is preserved unchanged in [the 22 October archive](docs/archive/README_2026-10-22.md). Existing design details, future scope, and historical estimates remain below; the archive preserves the exact earlier wording and status.

## Progress checkpoint — 26 October 2026

| Area | Current status |
| --- | --- |
| Replacement plan | Create a new plan asks for confirmation, clears the unfinished schedule, and retains saved records and pending notes. |
| Fixed maximum window | A fresh plan saves its start, requested duration, and latest finish at start + 1.5 × requested duration. Pause, resume, and reopening keep that deadline. |
| Finish display and checks | Expected finish and latest allowed finish are displayed; starting/resuming checks whether unfinished sessions fit. |
| Revised proposal | A paused plan can preview a shortened remaining schedule, current-block time left, and focus time left out. Previewing does not change the plan. |
| Apply and resume | Applies the displayed proposal only after checking the plan snapshot and current deadline; preserves completed blocks, elapsed work, and the original deadline. Cancel leaves the plan unchanged. |
| Schedule display | Shows the actual active plan after revision and restore; shows an input-based preview when no plan exists. Listed durations are full blocks, including time already worked. |
| Normal close/reopen | Author confirmed the revised schedule, remaining countdown, paused state on restore, and original deadline are preserved. |
| Still open | Crash/forced-stop timing accuracy, transition consistency, sleep/lock handling, optional earlier finish limits, and durable deferred-task tracking. |

Validation evidence: the author exercised Apply, Cancel, expiry while the review dialog was open, schedule refresh, and normal pause → close → reopen. Screenshots and logs show the revised single-focus plan and an unchanged deadline. The author separately confirmed remaining-time restoration. Earlier isolated function checks covered calculation, Apply/Cancel, deadline expiry, and save/restore with simulated UI/settings; they were not a full PySide6 GUI test. This checkpoint does not resolve the older unexpected-close timing discrepancy.

Recent implementation commits:

- `02c4050`: Apply revised plans with deadline validation and resume support.
- `c0691e1`: Fix active plan preview after revision and restore, including exact session-index matching in the proposal snapshot check.

## Working features

- Adjustable focus and break durations; defaults of 25 and 7 minutes.
- Available-time planning with a preview of focus and break blocks.
- A shorter final focus block when required by the plan.
- Automatic focus-to-break transitions; after a break, the next focus waits for a Start click. The clock stops when the plan finishes.
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
- Persisted post-break waiting timestamps and elapsed extra-time calculation.
- Hidden break-buffer calculation using interpolated defaults for breaks up to 120 minutes.
- A review prompt shown once per waiting period, with **Continue plan**, **Keep waiting**, and confirmed **Create a new plan** choices.
- Optional interruption reasons and decisions saved in SQLite, with review time and extra waiting seconds.
- **History → View Interruptions** displays recent saved reviews, including the reason, choice, extra time at review, and IST timestamp.
- Persisted original start, requested plan duration, and fixed 1.5× latest-finish deadline.
- Live expected-finish/latest-finish display and a deadline check before starting/resuming sessions.
- Revised-plan preview with remaining durations and focus time left out, in an enlarged review dialog.
- **Apply and resume** uses the displayed proposal after snapshot and fresh deadline validation; expired proposals are rejected without changing the plan.
- Completed blocks and current elapsed time are retained when replacing the unfinished schedule.
- Active-plan preview refreshes after Apply, reset, and restore, using the actual plan rather than regenerating the original schedule from input values.

Settings and draft persistence were tested by the author on 17 October. Normal-exit and unexpected-close timer recovery were tested on 19–20 October. On 20 October, the periodic autosave setup was moved out of the restore function so it also starts on fresh launches; the restore checks were corrected to reject `index == len(plan)` and allow zero elapsed seconds. These corrections were confirmed locally, but a remaining recovery-timing discrepancy is still open. On 26 October, the author confirmed normal pause → close → reopen recovery of a revised plan, including remaining time and the original deadline. Forced-stop recovery remains a separate unresolved issue.

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
3. Click **Start**. Focus completion starts the break automatically. After the break ends, click **Start focus** when ready to continue.
4. Use **Pause/Resume**, **Skip Session**, or **Reset plan** as needed.
5. After a focus session, enter its task name and remarks. If several sessions are waiting, saving advances the same form to the next pending session.
6. Open **History** to view session records and today's focus summary.
7. Select a row and click **View Notes** to read its saved notes. Click **Refresh** to update history and the summary.
8. On reopening an unfinished plan, use **Resume** to continue or **Reset plan** to discard it. Reopening currently excludes closed-app time from active-session progress; an already-started post-break wait uses a persisted timestamp and includes elapsed time while closed. Sleep-aware session reconciliation is a separate planned change.
9. If the hidden post-break buffer is exceeded, optionally provide a reason and choose **Continue plan**, **Keep waiting**, or **Create a new plan**. Keep waiting leaves focus stopped; creating a new plan requires confirmation and keeps saved records and pending notes.
10. Use **History → View Interruptions** to inspect saved reviews. Extra time is recorded at the moment a review is submitted; it is not necessarily the final total if the user keeps waiting.
11. At the first Start, the app fixes the latest allowed finish at 1.5 × the requested plan duration after that start. Pauses and closed-app time consume this window without being counted as active work.
12. If Start/Resume finds the remaining schedule no longer fits, open **Show Details** in the revised-plan dialog. Review the proposed remaining schedule and focus time left out. **Cancel** keeps the plan paused; **Apply and resume** updates and resumes it only if the same proposal still fits.
13. If the proposal expires while the dialog is open, reopen the review for a fresh proposal. If no valid schedule fits, leave it paused or explicitly reset to create a new plan. The old deadline is never silently extended.
14. The lower **Current plan** display lists full block durations, including elapsed work. The countdown shows the current block's remaining time. The input boxes retain their configured values and do not describe the revised schedule.

## Project structure

| Path | Responsibility |
| --- | --- |
| `main.py` | Application setup, timer state, plan execution, main controls, and note-entry flow |
| `database.py` | Session and interruption-review storage, schema initialization, history queries, note retrieval, and daily-summary query |
| `history_window.py` | History interface, daily-summary display, notes viewer, and interruption-review viewer |
| `database_fetch.py` | Development helper for inspecting records; currently contains a machine-specific database path |
| `sound/session_chime.wav` | Session-transition sound |
| `Pomodoro_Clock_Project_Checkpoint.md` | Earlier project checkpoint; may not reflect the latest progress |
| `docs/archive/README_2026-10-22.md` | Exact previous README, retained as historical documentation |
| `pomodoro.db` | Local runtime data, created by the application |

Some work-log SQL and plan-building logic remain in `main.py`. Further separation will happen gradually while preserving working behaviour.

## Data and current limitations

- `sessions_records` stores timing records and outcomes; `work_logs` stores notes linked through `session_id`; `break_reviews` stores optional reasons, choices, extra waiting seconds, and submission timestamps keyed by the waiting-period identifier.
- Session records and saved notes are stored locally in `pomodoro.db` beside the application files. Preferences, pending drafts, and timer snapshots are stored separately in QSettings. Backing up the database alone does not preserve all application state. No account or cloud synchronization is implemented.
- Older notes can have an empty `session_id`; the app does not guess which session they belonged to.
- A task name in a note is not yet a reusable task. Cross-plan task grouping is still planned.
- Settings, active plans, pending-note queues, and drafts now restore after closing. Timer recovery reopens paused; it does not resume automatically.
- Resetting an active block does not currently save it as an interrupted session.
- **Known bug — unexpected-close recovery accuracy:** after an unexpected stop, the recovered countdown has differed by roughly 2–7 seconds and sometimes more than 10 seconds in author testing. A five-second autosave interval is not a proven maximum-loss guarantee. Record this as unresolved and investigate save timing, event-loop delays, and restored values.
- Laptop-sleep and screen-lock handling are not implemented. A stopped Python process cannot sound an alarm while the laptop is suspended.
- Database writes and QSettings snapshots are separate operations. Crash-safe duplicate prevention and reconciliation at session transitions still need work.
- Restored window position may be nearby rather than pixel-exact; this is accepted for now.
- Failed session saves are reported in the console; automatic retry and durable recovery are not implemented.
- History displays the latest 20 sessions. Browsing all records and date/task filters are planned.
- Daily totals include active time from both completed and skipped focus sessions. Breaks and the currently running block are excluded.
- A session's entire duration is assigned to its save date in IST. Sessions crossing midnight are not split between days.
- The daily summary updates when History opens or Refresh is clicked; it is not a live counter.
- Available time includes breaks. The planner can leave time unused when a full break would leave no time for another focus block.
- Pauses and post-break waiting extend the expected finish within a fixed 1.5× maximum window. Start/Resume now blocks an unfitting plan and offers a revised proposal. The deadline display refreshes periodically, but proactive review before the ordinary post-break buffer expires and sleep-aware enforcement still need work.
- Revised proposals use whole-minute block lengths, account for elapsed current-block time, retain breaks only when focus can follow, and remove trailing unused breaks. Newly shortened focus remainders under one minute are not proposed; an unchanged current focus may have under one minute left.
- Focus time left out is disclosed before Apply, but removed work is not yet stored as a deferred task or durable revision history. Optional earlier availability limits and fitting the original expected finish remain planned.
- The break control currently permits values below seven minutes. A mandatory minimum-break rule has not been finalized.
- Focus-to-break transitions are automatic; break-to-focus transitions wait for user confirmation. Interruption review, **Create a new plan**, and deadline-constrained recalculation are implemented. Fatigue-aware readiness checks, separate pause-duration records, and a dedicated long-pause review threshold remain planned. A pause already triggers schedule review on Resume when the remaining plan no longer fits.
- The review prompt is marked as shown before it opens. Closing it with X/Escape does not save a response and leaves focus stopped; the same wait will not automatically prompt again. Review persistence and recovery still need broader reliability checks.

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

**Design agreed on 20 October 2026; progress updated through 26 October.** Manual focus start after breaks, waiting-time persistence, hidden-buffer checks, optional reasons, Continue/Wait/New plan choices, interruption history, and deadline-constrained revised-plan Apply/resume are implemented. Sleep/lock reconciliation, dedicated long-pause review, deferred-task persistence, and repeating alarms remain planned. The following sections retain the full intended design; sleep, lock, and alarm behaviour is not yet implemented. These rules do not change the locked Family Planner V1 scope.

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

The intended waiting/review flow also covers screen lock and non-response after a break. The next focus already requires a Start click, and focus-to-break progression is automatic. Explicit lock detection and sleep reconciliation still need implementation.

### Hidden extra-time buffer

The buffer is an internal threshold for asking what happened. It is **not displayed to the user**, added to the displayed break, or treated as permission to automatically start another focus session.

| Allocated break | Initial buffer rule | Extra time before review |
| --- | --- | --- |
| 10 minutes or less | Fixed allowance | 10 minutes |
| 15 minutes | 70% of the allocated break | 10 minutes 30 seconds |
| 30 minutes | 40% of the allocated break | 12 minutes |
| 60 minutes | 25% of the allocated break | 15 minutes |
| 120 minutes | 15% of the allocated break | 18 minutes |

The current calculation linearly interpolates the extra buffer minutes between these anchors, then converts to seconds. Above 10 minutes, the effective percentage decreases as the break grows, while extra minutes may increase. **There is no fixed ten-minute cap.** Breaks up to 10 minutes receive 10 minutes extra. The current function supports positive break durations up to 120 minutes; longer breaks need a defined rule before the limit is expanded. These defaults can be revised later through the planned adaptation features.

After a scheduled break ends, track extra time silently. Once the buffer is exceeded, offer an interruption review. If the laptop is asleep, perform this check when it resumes; do not wake it. If locked, present the actionable review when the user can interact, without bypassing the lock screen.

Later, the clock may adjust buffers using whole-day activity, task demands, fatigue feedback, and interruption history. Keep adjustments bounded and user-overridable/resettable. Repeated overruns alone must not automatically justify ever-longer buffers.

### Interruption review and replanning

Ask **“What happened, and how would you like to continue?”** An optional reason can include fell asleep, urgent work, longer rest, or another reason.

**Currently available:** Continue plan, Keep waiting, and confirmed Create a new plan, with optional reason capture and saved review history. If a start/resume attempt no longer fits, the revised-plan dialog adds Cancel and Apply and resume.

The original intended choices are retained below with their current status:

1. **Continue the remaining plan unchanged — implemented for start/resume:** preserve unfinished session lengths and shift their times forward by actual delays, provided the result fits within the fixed maximum finish time described below. Keeping session lengths unchanged does not mean unlimited deadline extensions.
2. **Recalculate the remaining plan — partially implemented:** with user confirmation, shorten or defer work to fit a chosen finish deadline, within the existing ceiling. The current implementation shortens/removes unfinished blocks to fit the existing latest-finish deadline after explicit Apply. Saving deferred work as tasks and choosing an earlier finish limit remain planned. Fitting the original expected finish time is an optional planned choice, not the automatic default. Preserve completed records and avoid duplicate sessions; crash-time duplicate prevention still needs strengthening.
3. **Create a new plan — implemented:** confirm before replacing the unfinished schedule; retain completed records, notes, and interruption history. A new plan and any new completion window must be explicitly chosen.
4. **Keep waiting — implemented:** leave focus stopped. Waiting continues to consume the existing real-world window; dismissing a prompt does not reset the ceiling.

Explicit **Pause** currently freezes the countdown and excludes paused time from active work. Resume checks the fixed plan deadline and offers revision if required. Separately recording pause duration and offering reason/recovery review after a long pause remain planned. The exact pause-review threshold needs a separate definition because a focus pause has no allocated break duration to use as its percentage base.

### Alarm behaviour

- During a locked-but-awake session, support a louder repeating chime until the user dismisses it, with an adjustable volume and a **Stop alarm** control.
- A suspended laptop cannot play the chime. Reconcile elapsed sessions and notify on wake; the phone timer is the backup while asleep.
- Dismissing an alarm must not automatically start another focus session.
- Keep interruption prompts and the alarm from duplicating themselves on repeated timer callbacks or resume events.
- Finalize alarm timing across an unattended focus-to-break transition during implementation; do not let the alarm prevent the planned break from elapsing.

### Implementation sequence

Completed foundations: manual focus start after breaks, persisted waiting timestamps, buffer calculation, one-time review prompts, optional reason/choice storage, and interruption history.

Original implementation sequence, with current progress:

1. **Done:** Create a new plan with confirmation, preserving saved records and pending notes.
2. **Core done:** Persist original plan start, requested duration, and fixed maximum finish time; expected finish is calculated live rather than stored as a separate original expected-finish timestamp.
3. **Core done:** Shift projected finish for delays and check the remaining schedule before start/resume. Sleep reconciliation and proactive prompting before the break-review buffer remain open.
4. **Partly done:** User-approved preview, shortening/removal, Apply/resume, and fresh deadline validation. Durable deferral of removed work and optional earlier finish targets remain open.
5. **Pending:** Focus-start reminder and optional phone backup prompt.
6. **Pending:** Reconcile elapsed focus/break blocks after sleep and detect lock/away states.
7. **Partly done:** Deadline review on Resume exists. A dedicated long-pause threshold, reason review, and separate pause-duration records remain pending.
8. **Pending:** Repeating alarm, dismissal, volume control, and workflow checks.
9. **Partly done:** Normal revised-plan pause/close/reopen confirmed. Unexpected-close accuracy and database/snapshot consistency remain open.

## Flexible schedule with a fixed maximum window

**Agreed on 22 October 2026; core implemented by 26 October.** One requested-duration input now builds a plan and fixes the maximum window at first Start. Expected-finish display, start/resume validation, revised preview, Apply/resume, and deadline persistence are implemented. Optional earlier availability limits, original-expected-finish targeting, durable deferred work, and sleep-aware reconciliation remain planned. The full agreed design below is retained, including those future parts. The user does not have to calculate a finish time or know exactly how long they will be available.

### Default setup and remaining availability options

- The user enters a requested plan duration, such as **4 hours**. This includes the planned focus and break blocks, not four hours of focus alone.
- The clock builds the sessions and calculates their expected finish time.
- When the user first clicks Start for the plan, establish an original start timestamp and a fixed maximum elapsed window of **1.5 × the requested duration**.
- A four-hour request therefore has a maximum six-hour real-world window. This is a ceiling, not a requirement to use all six hours or a prediction that the user is free for six hours.
- **Planned:** an **available until** constraint is optional. If the user knows they must leave at a particular time, use that earlier limit. An optional available-duration entry can also be converted into a finish limit when the plan starts.
- **Planned:** if a supplied availability limit cannot accommodate the initial plan, ask the user to adjust it before starting. Do not silently discard planned work.

```text
Default latest finish = original plan start + 1.5 × requested duration
Effective latest finish (planned availability option) = earlier of default latest finish and optional availability limit
Expected finish = current time + remaining scheduled time
                  (when ready to continue; excluding future unplanned delays)
```

If the existing planner leaves a small amount of requested time unused, calculate the expected finish from the actual session blocks; still base the maximum-window allowance on the original requested duration. Keep those two values distinct.

| Requested plan, including breaks | Starts | Optional availability limit | Initial expected finish* | Latest finish |
| --- | --- | --- | --- | --- |
| 4 hours | 10:00 AM | Not supplied | 2:00 PM | 4:00 PM |
| 4 hours | 10:00 AM | 3:00 PM | 2:00 PM | 3:00 PM |
| 2 hours | 10:00 AM | Not supplied | Noon | 1:00 PM |

*Examples assume the session blocks fill the requested duration. The row with an optional availability limit describes planned behaviour; that input is not implemented yet.

### Reschedule using actual elapsed time

Current code handles active running time, pause/wait delays in the expected finish, and a fixed persisted ceiling. The sleep/lock rules and separate interruption timing below remain design requirements.

- Measure extra waiting after scheduled breaks and explicit pauses using real elapsed time, including intervals with the laptop locked or the app unavailable where applicable.
- Move unfinished sessions forward to reflect actual delays while preserving their lengths whenever the remaining work still fits.
- Update the expected finish as waiting grows; the original maximum finish does not move with it.
- Count all extra time against the overall window, including time below the hidden review-buffer threshold. The buffer controls prompting only; it does not provide free time outside the window.
- Planned breaks are already part of the session plan. Add only extra break time and other non-overlapping delays; do not count the same sleep interval twice as both a planned break and an interruption.
- Sleep reconciliation still permits only the active focus and its following planned break to elapse before the next focus waits. Do not consume the rest of the plan automatically while the user is away.
- Paused or waiting time must not be reported as confirmed focused work.

Example: a four-hour plan starting at 10:00 AM normally finishes at 2:00 PM and has a 4:00 PM ceiling. Thirty minutes of extra break time moves the expected finish to 2:30 PM. Two hours of total extra delay moves it to 4:00 PM. Further delay means the unchanged remaining plan no longer fits; the clock must ask for a decision.

### Enforce the ceiling and preserve user control

Start/resume checks, proposal confirmation, snapshot validation, and deadline persistence are implemented. Proactive review independent of the break buffer, sleep-aware cutoff, optional earlier deadlines, and durable deferral remain pending requirements in this section.

- Check remaining work against the fixed ceiling before continuing and whenever actual delays change the projected finish.
- If it no longer fits, ask the user to shorten remaining work, defer some work, stop, or explicitly create a replacement plan. Do not silently compress focus sessions or remove breaks.
- Keep the optional **fit the original expected finish** action separate from the default **preserve session lengths within the maximum window** behaviour.
- At or beyond the ceiling, do not start further sessions in the old plan. Preserve unfinished work for review instead of marking it completed. If the app only resumes after the ceiling, reconcile against that deadline and explain what remains unfinished.
- Persist the original start and ceiling. Pause, resume, Keep waiting, another interruption, or reopening the app must not reset or extend them. A stopped/reopened app still consumes the overall real-world window, even though it does not accumulate active focus time.
- Deadline constraints take precedence over the hidden break buffer: if a plan no longer fits or the ceiling is reached before that buffer expires, request a planning decision without waiting for the ordinary interruption threshold.
- The plan ceiling may be shown to the user as a **latest finish**; the hidden per-break buffer remains internal.
- Updating known availability or replacing a plan is an explicit user action. The app must not automatically enlarge the ceiling to avoid handling unfinished work.

### Later Family Planner support

The future integration can use known appointments, household tasks, priorities, and activity history to suggest an appropriate plan duration or an earlier availability limit. It should reduce the user's scheduling calculations while leaving the suggested plan reviewable. This remains future integration work and does not expand the locked Family Planner V1 scope.

## Roadmap status and earlier effort estimates

**Estimate baseline: 16 October 2026.** The original table is retained for scope continuity, but its hours and totals are historical, not a current remaining-work estimate. Settings, draft persistence, and basic timer recovery have since been implemented; the new interruption design adds work. A fresh estimate is needed after that design is broken into tested steps. Development time includes reading, explanations, implementation, and debugging; a recent recovery change took over an hour despite a 30-minute target.

Current progress against that baseline:

- **Settings:** core duration and display preferences implemented; exact window positioning remains a minor limitation.
- **Unfinished notes:** draft/queue persistence and autosave implemented; further failure/reconciliation checks remain.
- **Timer recovery:** normal-exit and revised-plan pause/close/reopen recovery confirmed; periodic snapshots exist. Unexpected-close accuracy remains an open bug, alongside sleep/lock handling and richer timing records.
- **Interruption review:** manual focus start, waiting-time persistence, buffer checks, optional reasons, Continue/Wait/New plan decisions, interruption history, and bounded revised-plan Apply/resume are implemented. Dedicated long-pause review, alarm improvements, and durable deferral remain.
- **Time-range scheduling:** requested-duration planning, a fixed 1.5× maximum window, expected/latest finish display, and deadline-aware revision are implemented. Optional availability limits and original-expected-finish targeting remain planned.
- **Other sections:** retained below as planned work. The interruption and maximum-window rules belong to timer recovery, time-range scheduling, and reliability; do not count them as completed or add overlapping estimates twice.

| Section | Original scope (see progress above) | Original hours |
| --- | --- | ---: |
| Remember settings | Restore durations, available time, and display preferences | 1–2 |
| Reusable tasks | Persistent task IDs, continuation across plans, grouped progress and totals | 4–7 |
| Richer task/session details | Categories, activities, methods, effort, progress, findings, and next actions | 3–5 |
| Preserve unfinished notes | Durable drafts and queues, restoration, and access to pending notes | 3–5 |
| Timer recovery and timing records | Interrupted plans, sleep handling, start/end times, and pauses | 4–7 |
| Task demands and recovery rules | Fatigue feedback, automatic break selection, recovery checks, and pain-related pause behaviour | 6–10 |
| Adaptive work and suggestions | Focus-length adjustment, suitable task suggestions, priority handling, and return support | 4–7 |
| Time-range scheduling | Finish deadlines, expected end time, and replanning after pauses/skips; now expanded by the planned fixed 1.5× window | 4–7 |
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

Current sequence: strengthen unexpected-close recovery and complete sleep/lock and interruption handling in small checkpoints; introduce reusable tasks and richer details; add adaptive suggestions; then expand family use. Retain all original scope items. Difficulty ratings, gentle happy/grumpy companion feedback, and the previously discussed ten-minute review/form prompt remain in the richer-log and companion backlog; their exact interaction design still needs clarification. Estimates will be revised as sections are specified and tested.

## Family use and future Family Planner integration

Basic family profiles mean selectable users on a single installation. They are not, by themselves, strong privacy or access-control boundaries.

Shared data across devices, authentication, permissions, household scheduling, and automatic task assignment are outside the estimates above.

The intended integration sequence is:

1. Complete and validate the standalone clock.
2. Complete and accept the separately approved Family AI Planner V1 scope.
3. Design the integration explicitly, including identities, permissions, task ownership, and synchronization.

The proposed responsibility split is that Family Planner manages household tasks, schedules, and approved assignments, while the clock runs focus sessions and records progress. Stable user/task/session IDs and an authenticated interface would connect them. This is a future proposal, not an implemented integration or a change to the locked Family Planner V1 scope.

## Remaining work and next checkpoint

The former next checkpoint—Create a new plan, persisted fixed deadlines, and bounded revised-plan preview/Apply—is complete for the current workflow. The active-plan display fix is pushed, and normal pause/close/reopen has been confirmed.

**Suggested next checkpoint: investigate unexpected-close recovery accuracy.** Compare the last saved elapsed value with the restored value during controlled forced-stop tests, including a session transition. Keep this separate from the normal-close test that already passed. Preserve existing records and check for missing or duplicate records; do not claim a guaranteed maximum loss from the autosave interval alone.

The remaining roadmap, retaining the earlier scope:

| Area | Remaining work |
| --- | --- |
| Reliability | Unexpected-close timing, crash-safe session/notes/snapshot consistency, failed-save recovery, and broader interruption tests. |
| Sleep and lock | Wake reconciliation, lock/away handling, separation of elapsed schedule time from confirmed focus, and deadline-aware cutoff. |
| Pauses and review | Separate pause timing, long-pause threshold/reasons, and review when deadlines require action before the normal break buffer. |
| Alarms | Repeating chime, Stop alarm, volume control, and pre-focus duration/finish/phone-backup prompt. |
| Scheduling | Optional finish-by limit, original-expected-finish target, and durable deferred-work tracking. |
| Tasks | Reusable task IDs, Continue/Switch/Complete choices, and totals across sessions and days. |
| Richer notes | Category, activity, methods, mental/physical effort, difficulty, optional completion percentage, findings, pending work, and next action. |
| Adaptation | Focus/break suggestions, recovery feedback, larger-break rules, minimum-break policy, and priority-aware task suggestions. |
| History and Excel | Browse beyond 20 records, date/task filters, edit notes, task totals, Excel export, and validated import. |
| Companion | Gentle happy/grumpy feedback and the ten-minute review/form prompt; final interaction rules remain to be defined. |
| Family profiles | Separate users, tasks, history, and preferences on one installation; future integration remains separate. |
| Usability and maintenance | Actual-clock display alongside countdown, launcher/setup, pinned dependencies, incremental code organization, and documentation maintenance. |

The actual-clock display is retained from the earlier user request. This progress update does not add a new major feature or change the locked Family Planner scope. Historical estimates above remain unchanged and are not current remaining-hour estimates.

Keep the unexpected-close recovery timing discrepancy on the known-bug list. Do not change laptop power settings or add wake-up scheduling. Work in short sessions with one concrete outcome and a small verification checklist.
