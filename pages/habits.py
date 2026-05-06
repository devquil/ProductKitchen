import streamlit as st
from datetime import date, timedelta
import uuid
from models.habit import Habit, HabitEntry
from lib import store


ICON_OPTIONS = ["⏱", "📖", "🏃", "💪", "🎯", "🧘", "✍️", "💻", "🎨", "🎵"]
COLOR_OPTIONS = ["#4ade80", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4", "#f97316"]


def progress_ring(pct: float, color: str, size: int = 80) -> str:
    """Return an HTML SVG circular progress ring."""
    r = (size - 10) // 2
    cx, cy = size // 2, size // 2
    circumference = 2 * 3.14159 * r
    filled = circumference * min(pct, 1.0)
    remaining = circumference - filled
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="8"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="8"
        stroke-dasharray="{filled:.2f} {remaining:.2f}"
        stroke-linecap="round"
        transform="rotate(-90 {cx} {cy})"/>
      <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central"
        font-size="14" font-weight="bold" fill="{color}">{int(min(pct,1)*100)}%</text>
    </svg>
    """


def render():
    st.title("⏱ Habits Tracker")
    st.markdown("Log hours daily. Build consistency. Don't fake it.")

    habits = store.get_habits()

    # ── ADD HABIT ──────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Habit", expanded=False):
        with st.form("add_habit", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Habit name")
            desc = c2.text_input("Description")
            c3, c4, c5 = st.columns(3)
            goal_hrs = c3.number_input("Daily goal (hours)", 0.5, 24.0, 4.0, 0.5)
            icon = c4.selectbox("Icon", ICON_OPTIONS, index=0)
            color = c5.selectbox("Color", COLOR_OPTIONS, index=0)
            submitted = st.form_submit_button("Add Habit")
            if submitted and name:
                habit = Habit.create(
                    name=name,
                    description=desc,
                    goal_hours=goal_hrs,
                    icon=icon,
                    color=color,
                )
                store.save_habit(habit)
                st.rerun()

    if not habits:
        st.info("No habits yet. Add one above to start tracking.")
        return

    # ── TODAY'S LOG ────────────────────────────────────────────────────────────
    st.subheader(f"📅 Today — {date.today().strftime('%A, %b %d')}")

    for habit in habits:
        today_hours = store.get_today_hours(habit.id)
        pct = min(today_hours / habit.goal_hours, 1.0) if habit.goal_hours > 0 else 0

        c1, c2, c3, c4 = st.columns([1, 3, 2, 1])

        ring_html = progress_ring(pct, habit.color)
        c1.markdown(ring_html, unsafe_allow_html=True)

        c2.markdown(f"**{habit.icon} {habit.name}**")
        if habit.description:
            c2.caption(habit.description)
        c2.markdown(f"`{today_hours:.1f}h / {habit.goal_hours:.1f}h` today")

        # Log hours
        with c3:
            log_hrs = st.number_input(
                "Hours", 0.0, 24.0, 0.5, 0.25,
                key=f"hrs_{habit.id}",
                label_visibility="collapsed",
            )
        if c4.button("Log", key=f"logbtn_{habit.id}"):
            entry = HabitEntry(
                id=str(uuid.uuid4()),
                habit_id=habit.id,
                date=date.today(),
                hours_worked=log_hrs,
            )
            store.save_habit_entry(entry)
            st.rerun()

        st.markdown("---")

    # ── WEEKLY OVERVIEW ────────────────────────────────────────────────────────
    st.subheader("📆 This Week")

    week_days = []
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    for i in range(7):
        d = week_start + timedelta(days=i)
        day_label = d.strftime("%a")
        is_today = d == today

        day_entries = []
        for habit in habits:
            day_entries.extend(store.get_habit_entries(habit_id=habit.id))
        day_entries = [e for e in day_entries if e.date == d]
        total_hrs = sum(e.hours_worked for e in day_entries)

        total_goal = sum(h.goal_hours for h in habits)
        pct = min(total_hrs / total_goal, 1.0) if total_goal > 0 else 0

        bar = "█" * int(pct * 10) + "░" * (10 - int(pct * 10))
        color = "#22c55e" if is_today else "#6b7280"
        label = f"**Today**" if is_today else day_label
        st.markdown(f"{label}  |  {bar}  `{total_hrs:.1f}h`")

    # ── ALL HABITS OVERVIEW ─────────────────────────────────────────────────────
    st.subheader("🏆 All Habits — Overall Progress")

    cols = st.columns(len(habits))
    for i, habit in enumerate(habits):
        all_entries = store.get_habit_entries(habit_id=habit.id)
        total_hrs = sum(e.hours_worked for e in all_entries)
        # Show days tracked
        days_tracked = len(set(e.date for e in all_entries))
        avg_hrs = total_hrs / days_tracked if days_tracked > 0 else 0

        with cols[i]:
            st.markdown(f"**{habit.icon} {habit.name}**")
            st.caption(f"{days_tracked} days tracked")
            st.metric("Total hours", f"{total_hrs:.1f}h")
            st.metric("Avg/day", f"{avg_hrs:.1f}h")
            st.progress(min(avg_hrs / habit.goal_hours, 1.0),
                       color=habit.color)

    # ── DELETE HABIT ───────────────────────────────────────────────────────────
    with st.expander("🗑 Delete a habit"):
        del_name = st.selectbox("Select habit to delete:", habits,
                                format_func=lambda h: h.name)
        if st.button(f"Delete '{del_name.name}'", type="primary"):
            store.delete_habit(del_name.id)
            st.rerun()
