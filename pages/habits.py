import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, timedelta
import uuid
from models.habit import Habit, HabitEntry
from lib import store


ICON_OPTIONS = ["⏱", "📖", "🏃", "💪", "🎯", "🧘", "✍️", "💻", "🎨", "🎵"]
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


# ── Render ─────────────────────────────────────────────────────────────────────

def render():
    st.title("⏱ Habits Tracker")
    st.markdown("Log hours daily. Build consistency. Don't fake it.")
    st.markdown("---")

    # Init session state for date nav
    st.session_state.setdefault("habit_view_date", date.today())
    st.session_state.setdefault("habit_name", "")
    st.session_state.setdefault("habit_desc", "")
    st.session_state.setdefault("habit_goal", 4.0)
    st.session_state.setdefault("habit_icon", "⏱")
    st.session_state.setdefault("habit_color", "#4ade80")

    habits = store.get_habits()
    view_date = st.session_state.habit_view_date

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
                    st.session_state.habit_name = ""
                    st.session_state.habit_desc = ""
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
        # Show Mon–Sun range for the week containing view_date
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
        # date picker sits below the label
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
    today = date.today()

    for habit in habits:
        entries = store.get_habit_entries(habit_id=habit.id)
        day_entries = [e for e in entries if e.date == view_date]
        hours_worked = sum(e.hours_worked for e in day_entries)
        pct = min(hours_worked / habit.goal_hours, 1.0) if habit.goal_hours > 0 else 0.0
        is_done = hours_worked >= habit.goal_hours
        is_today = view_date == today

        # Overall stats
        all_entries = entries
        days_tracked = len(set(e.date for e in all_entries))
        total_hrs = sum(e.hours_worked for e in all_entries)
        avg_hrs = total_hrs / days_tracked if days_tracked > 0 else 0.0
        eff_pct = int(min(avg_hrs / habit.goal_hours, 1.0) * 100) if habit.goal_hours > 0 else 0

        # Streak
        streak = 0
        check_date = today
        while True:
            day_h = sum(e.hours_worked for e in all_entries if e.date == check_date)
            if day_h >= habit.goal_hours:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Card
        done_bg = "#f0fdf4" if is_done else "#ffffff"
        done_border = habit.color if is_done else "#e5e7eb"
        st.markdown(
            f"<div style='background:{done_bg}; border-left:5px solid {done_border}; "
            f"border-radius:10px; padding:14px 16px; margin-bottom:12px; "
            f"box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
            f"</div>",
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
                f"Eff: {eff_pct}% &nbsp;|&nbsp; 🔥 {streak} day streak</span>",
                unsafe_allow_html=True)

        with r3:
            log_key = f"hlog_{habit.id}_{view_date}"
            if log_key not in st.session_state:
                st.session_state[log_key] = 0.5
            log_val = st.number_input(
                "Hours", 0.0, 24.0, st.session_state[log_key], 0.25,
                key=log_key, label_visibility="collapsed")

        with r4:
            st.markdown("&nbsp;")
            if st.button("Log", key=f"logbtn_{habit.id}_{view_date}", use_container_width=True):
                entry = HabitEntry(
                    id=str(uuid.uuid4()),
                    habit_id=habit.id,
                    date=view_date,
                    hours_worked=log_val,
                )
                store.save_habit_entry(entry)
                st.session_state[log_key] = log_val
                st.rerun()

            # Mark as Done checkbox
            done_key = f"hdone_{habit.id}_{view_date}"
            was_done = is_done
            checked = st.checkbox(
                "Mark as Done" if not was_done else "✓ Done",
                value=was_done,
                key=done_key)
            if checked and not was_done:
                # Auto-fill goal hours as a log entry for today
                entry = HabitEntry(
                    id=str(uuid.uuid4()),
                    habit_id=habit.id,
                    date=view_date,
                    hours_worked=habit.goal_hours,
                )
                store.save_habit_entry(entry)
                st.rerun()
            elif not checked and was_done:
                # Remove the entry that reached the goal
                for e in day_entries:
                    if e.hours_worked >= habit.goal_hours:
                        store.delete_habit_entry(e.id)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # close card div

    # ── WEEKLY PROGRESS CHART ─────────────────────────────────────────────────
    view_weekday = view_date.weekday()
    week_start = view_date - timedelta(days=view_weekday)

    # Build week data (reused by grid + chart)
    week_data = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_hours = {}
        for h in habits:
            h_entries = store.get_habit_entries(habit_id=h.id)
            day_hours[h.name] = sum(e.hours_worked for e in h_entries if e.date == d)
        week_data[d] = day_hours

    # Stacked bar chart: habits × days
    if habits:
        chart_df = {h.name: [week_data[d].get(h.name, 0.0) for d in
                              [week_start + timedelta(days=i) for i in range(7)]]
                    for h in habits}
        chart_df["_day_labels"] = [(week_start + timedelta(days=i)).strftime("%a")
                                    for i in range(7)]
        # Build DataFrame for streamlit
        import pandas as pd
        df_chart = pd.DataFrame(chart_df, index=chart_df["_day_labels"])
        df_chart = df_chart.drop(columns=["_day_labels"])

        # Goal line reference: sum of daily goals per habit
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
        is_today = d == today
        is_future = d > today

        total_h = sum(week_data[d].values())
        total_goal = sum(h.goal_hours for h in habits)
        day_pct = min(total_h / total_goal, 1.0) if total_goal > 0 else 0

        # Ring for this day
        ring_color = "#22c55e" if (is_view or is_today) else "#9ca3af"
        ring_svg = mini_ring(day_pct, ring_color, 36)

        # Tick or X
        tick = "✅" if day_pct >= 1.0 else ("⏳" if total_h > 0 and day_pct < 1.0 else ("—" if is_future else "○"))

        with wgrid[i]:
            bg = "#f3f4f6" if is_view else "#ffffff"
            border = "#3b82f6" if is_view else ("#22c55e" if is_today else "transparent")
            st.markdown(
                f"<div style='text-align:center; background:{bg}; "
                f"border:2px solid {border}; border-radius:8px; padding:6px 2px;'>"
                f"<div style='font-size:11px; font-weight:600; color:#6b7280;'>{d.strftime('%a')}</div>"
                f"<div style='font-size:10px; color:#9ca3af;'>{d.strftime('%d')}</div>"
                f"{ring_svg}"
                f"<div style='font-size:12px; margin-top:2px;'>{tick}</div>"
                f"<div style='font-size:10px; color:#9ca3af;'>{total_h:.1f}h</div>"
                f"</div>",
                unsafe_allow_html=True)

    # ── ALL HABITS OVERALL PROGRESS ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🏆 All Habits — Overall Progress**")

    cols = st.columns(len(habits)) if habits else []
    for i, habit in enumerate(habits):
        all_entries = store.get_habit_entries(habit_id=habit.id)
        total_hrs = sum(e.hours_worked for e in all_entries)
        days_tracked = len(set(e.date for e in all_entries))
        avg_hrs = total_hrs / days_tracked if days_tracked > 0 else 0.0
        overall_pct = min(avg_hrs / habit.goal_hours, 1.0) if habit.goal_hours > 0 else 0.0

        with cols[i]:
            st.markdown(f"**{habit.icon} {habit.name}**")
            st.caption(f"{days_tracked} days tracked")
            st.metric("Total hours", f"{total_hrs:.1f}h")
            st.metric("Avg/day", f"{avg_hrs:.1f}h")
            st.progress(overall_pct)

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
