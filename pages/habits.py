import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, timedelta, datetime
import uuid
from models.habit import Habit, HabitEntry, HabitBlock, SleepEntry
from models.task import TaskStatus
from lib import store


ICON_OPTIONS  = ["⏱", "📖", "🏃", "💪", "🎯", "🧘", "✍️", "💻", "🎨", "🎵"]
COLOR_OPTIONS = ["#4ade80", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4", "#f97316"]


# ── SVG helpers ─────────────────────────────────────────────────────────────────

def progress_ring(pct: float, color: str, size: int = 80) -> str:
    r = (size - 10) // 2
    cx, cy = size // 2, size // 2
    circ = 2 * 3.14159 * r
    filled = circ * min(pct, 1.0)
    remaining = circ - filled
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#e5e7eb' stroke-width='8'/>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{color}' stroke-width='8' "
        f"stroke-dasharray='{filled:.1f} {remaining:.1f}' stroke-linecap='round' "
        f"transform='rotate(-90 {cx} {cy})'/>"
        f"<text x='{cx}' y='{cy}' text-anchor='middle' dominant-baseline='central' "
        f"font-size='13' font-weight='bold' fill='{color}'>{int(min(pct,1)*100)}%</text>"
        f"</svg>"
    )


def mini_ring(pct: float, color: str, size: int = 36) -> str:
    r = (size - 6) // 2
    cx, cy = size // 2, size // 2
    circ = 2 * 3.14159 * r
    filled = circ * min(pct, 1.0)
    remaining = circ - filled
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#e5e7eb' stroke-width='5'/>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{color}' stroke-width='5' "
        f"stroke-dasharray='{filled:.1f} {remaining:.1f}' stroke-linecap='round' "
        f"transform='rotate(-90 {cx} {cy})'/>"
        f"</svg>"
    )


# ── Sleep tracker helpers ─────────────────────────────────────────────────────

CYCLE_MINUTES = 90


def _fmt_time(dt: datetime) -> str:
    """Cross-platform time formatter: 12-hour with AM/PM."""
    hour = dt.hour % 12 or 12
    ampm = "PM" if dt.hour >= 12 else "AM"
    return f"{hour}:{dt.minute:02d} {ampm}"


def optimal_wake_times(bedtime: datetime) -> dict:
    """Returns wake times for 3-6 complete cycles + recommended badge."""
    results = {}
    for cycles in [3, 4, 5, 6]:
        mins = cycles * CYCLE_MINUTES
        wake = bedtime + timedelta(minutes=mins)
        results[cycles] = {
            "wake": wake,
            "hours": mins / 60,
            "label": _fmt_time(wake),
        }
    return results


def quality_stars(quality: int) -> str:
    return "⭐" * quality + "☆" * (5 - quality)


def sleep_card_html(entry, tag_color: str = "#6366f1") -> str:
    bedtime_str = _fmt_time(entry.bedtime) if entry.bedtime else "—"
    wake_str = _fmt_time(entry.wake_time) if entry.wake_time else "—"
    dur = entry.duration_hours
    return f"""
    <div style="
        background:#ffffff;border-radius:8px;padding:10px 12px;
        border-left:4px solid {tag_color};margin-bottom:6px;
        box-shadow:0 1px 3px rgba(0,0,0,0.07);
    ">
        <div style="display:flex;align-items:center;gap:10px;">
            <div>
                <div style="font-size:12px;font-weight:700;color:#374151;">{entry.date.strftime('%a %b %d')}</div>
                <div style="font-size:11px;color:#9ca3af;">{bedtime_str} → {wake_str}</div>
            </div>
            <div style="margin-left:auto;text-align:right;">
                <div style="font-size:15px;font-weight:800;color:{tag_color};">{dur:.1f}h</div>
                <div style="font-size:11px;color:#9ca3af;">{quality_stars(entry.quality)}</div>
            </div>
        </div>
    </div>
    """


# ── Render ─────────────────────────────────────────────────────────────────────

def render():
    st.title("⏱ Habits Tracker")
    st.markdown("Work blocks linked to tasks — hours you log are hours your tasks get credited.")
    st.markdown("---")

    st.session_state.setdefault("habit_view_date", date.today())
    st.session_state.setdefault("habit_name", "")
    st.session_state.setdefault("habit_desc", "")
    st.session_state.setdefault("habit_goal", 4.0)
    st.session_state.setdefault("habit_icon", "⏱")
    st.session_state.setdefault("habit_color", "#4ade80")
    st.session_state.setdefault("start_block_mode", None)  # habit_id if choosing task
    st.session_state.setdefault("selected_task_idx", 0)

    habits = store.get_habits()
    tasks  = store.get_tasks()
    # Only tasks that are pending or in-progress can be worked on
    work_tasks = [t for t in tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
    view_date = st.session_state.habit_view_date
    today = date.today()

    # ── ADD HABIT ──────────────────────────────────────────────────────────────
    with st.expander("**＋ Add New Habit**", expanded=not habits):
        with st.form("add_habit_form", clear_on_submit=True):
            c1, c2 = st.columns([3, 2])
            c1.text_input("Habit name", key="habit_name")
            c2.text_input("Description", key="habit_desc")
            c3, c4, c5, c6 = st.columns([2, 1, 1, 2])
            c3.number_input("Daily goal (hours)", 0.5, 24.0, 4.0, 0.5, key="habit_goal")
            c4.selectbox("Icon", ICON_OPTIONS, key="habit_icon")
            c5.selectbox("Color", COLOR_OPTIONS, key="habit_color")
            c6.markdown("")
            if st.form_submit_button("Add Habit", use_container_width=True):
                if st.session_state.habit_name.strip():
                    habit = Habit.create(
                        name=st.session_state.habit_name.strip(),
                        description=st.session_state.habit_desc,
                        goal_hours=st.session_state.habit_goal,
                        icon=st.session_state.habit_icon,
                        color=st.session_state.habit_color,
                    )
                    store.save_habit(habit)
                    st.success(f"'{habit.name}' added!")
                else:
                    st.error("Habit name is required.")

    if not habits:
        st.info("No habits yet. Add one above to start tracking.")
        return

    # ── DATE NAVIGATION ────────────────────────────────────────────────────────
    col_prev, col_date, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("←", key="habit_prev_day", use_container_width=True):
            st.session_state.habit_view_date = view_date - timedelta(days=1)
            st.rerun()
    with col_date:
        day_of_week = view_date.weekday()
        week_start = view_date - timedelta(days=day_of_week)
        week_end = week_start + timedelta(days=6)
        if week_start.month == week_end.month:
            date_label = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}"
        else:
            date_label = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}"
        st.markdown(
            f"<p style='text-align:center; font-size:15px; font-weight:700; "
            f"margin:4px 0; color:#1f2937;'>{date_label}</p>",
            unsafe_allow_html=True)
        picked = st.date_input(
            "Pick a date to view",
            value=view_date,
            key="habit_date_picker",
            label_visibility="collapsed")
        if picked != view_date:
            st.session_state.habit_view_date = picked
            st.rerun()
    with col_next:
        if st.button("→", key="habit_next_day", use_container_width=True):
            st.session_state.habit_view_date = view_date + timedelta(days=1)
            st.rerun()

    st.markdown("---")

    # ── HABIT ROWS ────────────────────────────────────────────────────────────
    for habit in habits:
        blocks = store.get_habit_blocks(habit_id=habit.id)
        day_blocks = [b for b in blocks if b.date == view_date]
        today_blocks = [b for b in blocks if b.date == today]

        hours_worked = sum(b.duration_hours for b in day_blocks if b.duration_hours > 0)
        today_hours  = sum(b.duration_hours for b in today_blocks if b.duration_hours > 0)
        pct = min(hours_worked / habit.goal_hours, 1.0) if habit.goal_hours > 0 else 0.0
        is_done = hours_worked >= habit.goal_hours
        is_today_view = view_date == today

        # Check if this habit has an open block (from any day)
        open_block = None
        if habit.open_block_id:
            open_blocks = [b for b in blocks if b.id == habit.open_block_id]
            if open_blocks:
                open_block = open_blocks[0]

        # Overall stats
        total_hrs = sum(b.duration_hours for b in blocks)
        days_tracked = len(set(b.date for b in blocks if b.duration_hours > 0))
        avg_hrs = total_hrs / days_tracked if days_tracked > 0 else 0.0
        eff_pct = int(min(avg_hrs / habit.goal_hours, 1.0) * 100) if habit.goal_hours > 0 else 0

        # Streak
        streak = 0
        check_d = today
        from collections import defaultdict
        day_totals = defaultdict(float)
        for b in blocks:
            day_totals[b.date] += b.duration_hours
        total_goal_day = sum(h.goal_hours for h in habits)
        while True:
            hrs = day_totals.get(check_d, 0.0)
            if hrs >= total_goal_day:
                streak += 1
                check_d -= timedelta(days=1)
            else:
                break

        # Card styling
        done_bg = "#f0fdf4" if is_done else "#ffffff"
        done_border = habit.color if is_done else "#e5e7eb"
        st.markdown(
            f"<div style='background:{done_bg}; border-left:5px solid {done_border}; "
            f"border-radius:10px; padding:14px 16px; margin-bottom:12px; "
            f"box-shadow:0 1px 3px rgba(0,0,0,0.08);'>",
            unsafe_allow_html=True)

        r1, r2, r3, r4 = st.columns([1, 3, 2, 1])

        with r1:
            st.markdown(progress_ring(pct, habit.color), unsafe_allow_html=True)

        with r2:
            st.markdown(f"**{habit.icon} {habit.name}**")
            if habit.description:
                st.caption(habit.description)
            st.markdown(
                f"<span style='font-size:13px; color:#6b7280;'>{hours_worked:.1f}h / "
                f"{habit.goal_hours:.1f}h &nbsp;|&nbsp; {days_tracked} days &nbsp;|&nbsp; "
                f"Eff: {eff_pct}% &nbsp;|&nbsp; 🔥 {streak}d streak</span>",
                unsafe_allow_html=True)

        # ── Block controls ────────────────────────────────────────────────────
        with r3:
            if open_block:
                # ── BLOCK IS OPEN ──────────────────────────────────────────────
                linked_tasks = [t for t in tasks if t.id in open_block.task_ids]

                # Calculate elapsed work time (total elapsed minus breaks)
                now = datetime.now()
                total_elapsed_s = 0.0
                work_elapsed_s = 0.0
                if open_block.started_at:
                    total_elapsed_s = (now - open_block.started_at).total_seconds()
                    work_elapsed_s = total_elapsed_s - open_block.break_seconds
                elapsed_h = work_elapsed_s / 3600

                st.caption(f"🔵 Working on:")
                for t in linked_tasks:
                    short = (t.title[:22] + "…") if len(t.title) > 22 else t.title
                    st.caption(f"&nbsp;&nbsp;• {short}")
                if open_block.break_seconds > 0:
                    break_mins = open_block.break_seconds / 60
                    st.caption(f"&nbsp;&nbsp;⏸ Break: {break_mins:.0f}m")
                st.caption(f"⏱ {elapsed_h:.1f}h net work")

                # ── Take / End Break ──────────────────────────────────────────────
                break_mode_key = f"break_mode_{habit.id}_{open_block.id}"
                st.session_state.setdefault(break_mode_key, False)

                if not st.session_state[break_mode_key]:
                    # Working — show Take Break button
                    if st.button("⏸ Take Break", key=f"take_break_{habit.id}",
                                 use_container_width=True):
                        st.session_state[break_mode_key] = True
                        st.rerun()
                else:
                    # On break — show End Break button
                    if st.button("▶ End Break", key=f"end_break_{habit.id}",
                                 use_container_width=True, type="primary"):
                        # Accumulate break time since we entered break mode
                        # We don't have exact break-start time in session state,
                        # so use a simple approach: add 1 minute per rerun cycle
                        open_block.break_seconds += 60
                        store.save_habit_block(open_block)
                        st.session_state[break_mode_key] = False
                        st.rerun()

                # ── Edit Tasks (mid-block) ───────────────────────────────────────
                with st.expander("✏ Edit Tasks"):
                    edit_key = f"edit_tasks_{habit.id}"
                    all_work_ids = [t.id for t in work_tasks]
                    current_ids  = [tid for tid in open_block.task_ids if tid in all_work_ids]
                    default_idxs = [all_work_ids.index(tid) for tid in current_ids if tid in all_work_ids]

                    if not work_tasks:
                        st.caption("No pending/in-progress tasks available.")
                    else:
                        selected_idxs = st.multiselect(
                            "Tasks in block",
                            all_work_ids,
                            default=default_idxs,
                            key=edit_key,
                            format_func=lambda tid: next((t.title for t in work_tasks if t.id == tid), tid),
                            label_visibility="collapsed")
                        if st.button("Save Tasks", key=f"save_tasks_{habit.id}", use_container_width=True):
                            open_block.task_ids = selected_idxs
                            store.save_habit_block(open_block)
                            habit.open_block_task_ids = selected_idxs
                            store.save_habit(habit)
                            st.rerun()

                # ── End Block ─────────────────────────────────────────────────────
                # Default duration input to the net work elapsed (rounded to nearest 0.25)
                net_h = max(round(elapsed_h * 4) / 4, 0.25)
                end_hrs = st.number_input(
                    "Duration (h)", 0.25, 24.0, net_h, 0.25,
                    key=f"end_hrs_{habit.id}", label_visibility="collapsed")
                if st.button("End Block", key=f"end_block_{habit.id}",
                             use_container_width=True, type="primary"):
                    if end_hrs > 0:
                        # Finalize break: one more minute if currently on break
                        if st.session_state.get(break_mode_key, False):
                            open_block.break_seconds += 60
                        open_block.duration_hours = end_hrs
                        store.save_habit_block(open_block)

                        # Credit ALL linked tasks
                        for lt in linked_tasks:
                            lt.actual_hours += end_hrs
                            if lt.actual_hours > 0 and lt.estimated_hours > 0:
                                lt.efficiency = min(
                                    lt.estimated_hours / lt.actual_hours, 2.0)
                            store.save_task(lt)

                        habit.end_block()
                        store.save_habit(habit)
                        st.session_state.pop(break_mode_key, None)
                        st.rerun()

            elif st.session_state.start_block_mode == habit.id:
                # ── TASK SELECTOR (about to start block) ─────────────────────────
                st.caption("Select tasks for this block:")
                if not work_tasks:
                    st.warning("No pending/in-progress tasks. Add a task first.")
                    if st.button("Cancel", key=f"cancel_block_{habit.id}"):
                        st.session_state.start_block_mode = None
                        st.rerun()
                else:
                    all_ids = [t.id for t in work_tasks]
                    selected_ids = st.multiselect(
                        "Tasks",
                        all_ids,
                        default=all_ids,
                        key=f"sel_tasks_{habit.id}",
                        format_func=lambda tid: next((t.title for t in work_tasks if t.id == tid), tid),
                        label_visibility="collapsed")
                    c_start, c_cancel = st.columns(2)
                    if c_start.button("Begin Block", key=f"begin_{habit.id}", use_container_width=True):
                        if not selected_ids:
                            st.error("Select at least one task.")
                        else:
                            sel_tasks = [t for t in work_tasks if t.id in selected_ids]
                            for t in sel_tasks:
                                if t.status == TaskStatus.PENDING:
                                    t.start()
                                    store.save_task(t)
                            block = HabitBlock.create(
                                habit_id=habit.id,
                                task_ids=[t.id for t in sel_tasks],
                                date=view_date,
                                started_at=datetime.now(),
                            )
                            store.save_habit_block(block)
                            habit.start_block(block.id, [t.id for t in sel_tasks])
                            store.save_habit(habit)
                            st.session_state.start_block_mode = None
                            st.rerun()
                    if c_cancel.button("Cancel", key=f"cancel_block_{habit.id}", use_container_width=True):
                        st.session_state.start_block_mode = None
                        st.rerun()

            else:
                # ── NO BLOCK OPEN ────────────────────────────────────────────────
                if is_today_view:
                    if st.button(
                            f"▶ Start Block",
                            key=f"start_block_{habit.id}",
                            use_container_width=True):
                        st.session_state.start_block_mode = habit.id
                        st.rerun()
                else:
                    st.caption("⏱ Can only start blocks for today")

        with r4:
            if open_block:
                # Determine if on break (session state flag)
                break_mode_key = f"break_mode_{habit.id}_{open_block.id}"
                on_break = st.session_state.get(break_mode_key, False)

                linked_r4 = [t for t in tasks if t.id in open_block.task_ids]
                if linked_r4:
                    labels = [((t.title[:16]+"…") if len(t.title)>16 else t.title) for t in linked_r4]
                    joined = ", ".join(labels)
                    if len(joined) > 30:
                        joined = joined[:30] + "…"
                else:
                    joined = "(deleted)"

                badge = "⏸" if on_break else "🔵"
                color = "#f59e0b" if on_break else "#3b82f6"
                st.markdown(
                    f"<span style='font-size:11px;color:{color};font-weight:600;'>"
                    f"{badge} {joined}</span>",
                    unsafe_allow_html=True)
                if on_break:
                    st.caption(f"<span style='color:#f59e0b;font-size:10px;'>On break</span>",
                               unsafe_allow_html=True)
            else:
                st.markdown("&nbsp;")

        st.markdown("</div>", unsafe_allow_html=True)  # close card

    # ── WEEKLY PROGRESS CHART ─────────────────────────────────────────────────
    view_weekday = view_date.weekday()
    week_start = view_date - timedelta(days=view_weekday)

    week_data = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_hours = {}
        for h in habits:
            h_blocks = store.get_habit_blocks(habit_id=h.id)
            day_hours[h.name] = sum(b.duration_hours for b in h_blocks
                                    if b.date == d and b.duration_hours > 0)
        week_data[d] = day_hours

    if habits:
        import pandas as pd
        chart_df = {h.name: [week_data[d].get(h.name, 0.0)
                              for d in [week_start + timedelta(days=i) for i in range(7)]]
                    for h in habits}
        day_labels = [(week_start + timedelta(days=i)).strftime("%a")
                      for i in range(7)]
        df_chart = pd.DataFrame(chart_df, index=day_labels)

        total_goal = sum(h.goal_hours for h in habits)

        st.markdown("---")
        g1, g2 = st.columns([3, 1])
        with g1:
            st.markdown("**📊 Weekly Breakdown**")
            st.bar_chart(df_chart, horizontal=False)
        with g2:
            st.markdown("**Goal**")
            for h in habits:
                st.markdown(
                    f"<span style='color:{h.color}; font-size:13px;'>● {h.icon} {h.name} "
                    f"<code style='background:#f3f4f6;padding:1px 4px;border-radius:4px;'>"
                    f"{h.goal_hours:.0f}h/day</code></span>",
                    unsafe_allow_html=True)
            st.markdown(f"**Total goal:** `{total_goal:.0f}h/day`")

    # ── MINI WEEKLY GRID ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📆 This Week**")

    wgrid = st.columns(7)
    for i in range(7):
        d = week_start + timedelta(days=i)
        is_view = d == view_date
        is_today_d = d == today
        is_future = d > today

        total_h = sum(week_data[d].values())
        total_g = sum(h.goal_hours for h in habits)
        day_pct = min(total_h / total_g, 1.0) if total_g > 0 else 0

        ring_color = "#22c55e" if is_view else ("#9ca3af" if is_future else "#6b7280")
        ring_svg = mini_ring(day_pct, ring_color, 36)
        tick = "✅" if day_pct >= 1.0 else ("⏳" if total_h > 0 and day_pct < 1.0 else ("—" if is_future else "○"))

        with wgrid[i]:
            bg = "#f3f4f6" if is_view else "#ffffff"
            border = "#3b82f6" if is_view else ("#22c55e" if is_today_d else "transparent")
            st.markdown(
                f"<div style='text-align:center; background:{bg}; "
                f"border:2px solid {border}; border-radius:8px; padding:6px 2px;'>"
                f"<div style='font-size:11px;font-weight:600;color:#6b7280;'>{d.strftime('%a')}</div>"
                f"<div style='font-size:10px;color:#9ca3af;'>{d.strftime('%d')}</div>"
                f"{ring_svg}"
                f"<div style='font-size:12px;margin-top:2px;'>{tick}</div>"
                f"<div style='font-size:10px;color:#9ca3af;'>{total_h:.1f}h</div>"
                f"</div>",
                unsafe_allow_html=True)

    # ── ALL HABITS OVERALL PROGRESS ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🏆 All Habits — Overall Progress**")

    cols = st.columns(len(habits)) if habits else []
    for i, habit in enumerate(habits):
        all_blocks = store.get_habit_blocks(habit_id=habit.id)
        total_hrs = sum(b.duration_hours for b in all_blocks)
        days_tracked = len(set(b.date for b in all_blocks if b.duration_hours > 0))
        avg_hrs = total_hrs / days_tracked if days_tracked > 0 else 0.0
        overall_pct = min(avg_hrs / habit.goal_hours, 1.0) if habit.goal_hours > 0 else 0.0

        with cols[i]:
            st.markdown(f"**{habit.icon} {habit.name}**")
            st.caption(f"{days_tracked} days tracked")
            st.metric("Total hours", f"{total_hrs:.1f}h")
            st.metric("Avg/day", f"{avg_hrs:.1f}h")
            st.progress(overall_pct)

    # ── SLEEP TRACKER ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌙 Sleep Tracker")

    st.session_state.setdefault("sleep_bedtime", datetime.now().replace(hour=23, minute=0, second=0, microsecond=0))
    st.session_state.setdefault("sleep_quality", 3)

    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("**Bedtime → Wake-up calculator**")
        bedtime_input = st.time_input(
            "Bedtime",
            value=st.session_state.sleep_bedtime,
            key="sleep_bedtime_input",
        )
        bedtime_dt = datetime.combine(date.today(), bedtime_input)

        wakes = optimal_wake_times(bedtime_dt)
        st.markdown("**Wake up after:**")
        wake_cols = st.columns(4)
        recommended = 5
        for i, (cycles, info) in enumerate(wakes.items()):
            with wake_cols[i]:
                is_rec = cycles == recommended
                badge = " ✅ Best" if is_rec else ""
                st.markdown(
                    f"<div style='text-align:center;padding:8px 4px;"
                    f"background:{'#f0fdf4' if is_rec else '#f9fafb'};"
                    f"border-radius:8px;border:{'2px solid #22c55e' if is_rec else '1px solid #e5e7eb'};'>"
                    f"<div style='font-size:18px;font-weight:800;color:#6366f1;'>{info['label']}</div>"
                    f"<div style='font-size:11px;color:#9ca3af;'>{cycles} cycles · {info['hours']:.1f}h{badge}</div>"
                    f"</div>",
                    unsafe_allow_html=True)
        st.caption(f"Each sleep cycle ≈ {CYCLE_MINUTES} min. 5 cycles (7.5h) is the sweet spot — most REM rich.")

    with c_right:
        st.markdown("**Log last night's sleep**")
        sleep_entries = store.get_sleep_entries(days=7)
        last_entry = sleep_entries[-1] if sleep_entries else None
        default_date = last_entry.date if last_entry else date.today()

        with st.form("sleep_log_form", clear_on_submit=True):
            log_date = st.date_input("Sleep date", value=default_date, key="sleep_log_date")
            log_bedtime = st.time_input("Bedtime", value=st.session_state.sleep_bedtime, key="sleep_bedtime_log")
            log_waketime = st.time_input("Wake time (optional)",
                                         value=datetime.now().replace(hour=7, minute=0),
                                         key="sleep_waketime")
            quality = st.slider("Sleep quality", 1, 5, st.session_state.sleep_quality, key="sleep_quality")

            if st.form_submit_button("Log Sleep", use_container_width=True):
                bedtime_combined = datetime.combine(log_date, log_bedtime)
                wake_combined = datetime.combine(log_date, log_waketime)
                if wake_combined <= bedtime_combined:
                    wake_combined += timedelta(days=1)
                dur_h = (wake_combined - bedtime_combined).total_seconds() / 3600
                cycles = max(0, min(round(dur_h * 60 / CYCLE_MINUTES), 12))
                entry = SleepEntry.create(date=log_date, bedtime=bedtime_combined)
                entry.wake_time = wake_combined
                entry.cycles = cycles
                entry.quality = quality
                store.save_sleep_entry(entry)
                st.success(f"Logged {dur_h:.1f}h, {cycles} cycles, {quality_stars(quality)}")
                st.rerun()

        if sleep_entries:
            st.markdown("**Last 7 nights:**")
            cards = "".join(sleep_card_html(e) for e in reversed(sleep_entries))
            st.html(cards)

    # ── DELETE ────────────────────────────────────────────────────────────────
    with st.expander("🗑 Delete a habit"):
        if habits:
            del_idx = st.selectbox(
                "Select habit to delete:",
                range(len(habits)),
                format_func=lambda i: habits[i].name,
                key="del_habit_idx")
            if st.button(f"Delete '{habits[del_idx].name}'", type="primary", key="del_habit_btn"):
                store.delete_habit(habits[del_idx].id)
                st.rerun()
