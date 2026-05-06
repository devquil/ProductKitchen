import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime, date
from models.task import Task, Priority, TaskStatus
from lib import store


PRIORITY_COLOR = {
    Priority.HIGH: "#ef4444",
    Priority.MEDIUM: "#f59e0b",
    Priority.LOW: "#6b7280",
}

STATUS_COLOR = {
    TaskStatus.PENDING: "#6b7280",
    TaskStatus.IN_PROGRESS: "#3b82f6",
    TaskStatus.DONE: "#22c55e",
    TaskStatus.BLOCKED: "#a855f7",
}


def render():
    st.title("✅ Tasks Tracker")
    st.markdown("Add tasks, log hours, track efficiency.")

    tasks = store.get_tasks()
    col_config = {
        "title": "Task",
        "priority": st.column_config.TextColumn("Priority"),
        "status": st.column_config.TextColumn("Status"),
        "due_date": st.column_config.DateColumn("Due"),
        "estimated_hours": st.column_config.NumberColumn("Est. Hrs"),
        "actual_hours": st.column_config.NumberColumn("Actual Hrs"),
        "efficiency": st.column_config.ProgressColumn(
            "Efficiency", format="%.0f%%", min_value=0, max_value=100
        ),
    }

    # ── ADD TASK ────────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            c1, c2 = st.columns(2)
            title = c1.text_input("Task title")
            desc = c2.text_input("Description")
            c3, c4, c5 = st.columns(3)
            priority = c3.selectbox("Priority", [Priority.HIGH, Priority.MEDIUM, Priority.LOW],
                                    format_func=lambda p: p.value.upper())
            est_hrs = c4.number_input("Est. hours", 0.25, 24.0, 1.0, 0.25)
            due = c5.date_input("Due date", value=None)
            submitted = st.form_submit_button("Add Task")
            if submitted and title:
                task = Task.create(
                    title=title,
                    description=desc,
                    priority=priority,
                    due_date=datetime.combine(due, datetime.min.time()) if due else None,
                    estimated_hours=est_hrs,
                )
                store.save_task(task)
                st.rerun()

    # ── TASK TABLE ──────────────────────────────────────────────────────────────
    if not tasks:
        st.info("No tasks yet. Add one above.")
        return

    done = [t for t in tasks if t.status == TaskStatus.DONE]
    in_prog = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    blocked = [t for t in tasks if t.status == TaskStatus.BLOCKED]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(tasks))
    m2.metric("Done ✅", len(done))
    m3.metric("In Progress 🔵", len(in_prog))
    m4.metric("Pending", len(pending))
    st.markdown("---")

    # Display each task as a card
    for task in sorted(tasks, key=lambda t: (t.priority.value, t.due_date or date.max)):
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 1, 1, 1, 2])

            prio_color = PRIORITY_COLOR[task.priority]
            status_color = STATUS_COLOR[task.status]
            eff = int(task.efficiency * 100) if task.efficiency else 0

            c1.markdown(f"**{task.title}**")
            if task.description:
                c1.caption(task.description[:60])

            c2.markdown(
                f"<span style='color:{prio_color};font-weight:bold'>{task.priority.value.upper()}</span>",
                unsafe_allow_html=True,
            )
            c3.markdown(
                f"<span style='color:{status_color}'>{task.status.value.replace('_',' ')}</span>",
                unsafe_allow_html=True,
            )

            due_str = task.due_date.strftime("%b %d") if task.due_date else "—"
            if task.is_overdue:
                due_str = f"🔴 {due_str}"
            c4.markdown(f"`{due_str}`")

            c5.metric("Actual", f"{task.actual_hours:.1f}h")

            actions = c6
            action = actions.segmented_control(
                "Action", ["Start", "Done", "Del"],
                default=None, label_visibility="collapsed"
            )

            if action == "Start" and task.status == TaskStatus.PENDING:
                task.start()
                store.save_task(task)
                st.rerun()
            elif action == "Done":
                hrs = task.actual_hours
                if hrs == 0:
                    hrs = st.number_input(
                        f"Actual hours for '{task.title}'",
                        0.25, 24.0, task.estimated_hours, 0.25,
                        key=f"hrs_{task.id}",
                    )
                task.complete(hrs)
                store.save_task(task)
                st.rerun()
            elif action == "Del":
                store.delete_task(task.id)
                st.rerun()

            st.markdown("---")

    # ── LOG HOURS ──────────────────────────────────────────────────────────────
    st.subheader("⏱ Log Hours")
    in_prog_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    if in_prog_tasks:
        sel = st.selectbox("Select active task to log hours:", in_prog_tasks,
                           format_func=lambda t: f"{t.title} ({t.actual_hours:.1f}h logged)")
        hrs = st.number_input("Hours to add", 0.25, 12.0, 0.5, 0.25, key="log_hrs")
        if st.button(f"Log {hrs}h to '{sel.title}'"):
            sel.actual_hours += hrs
            sel.efficiency = min(sel.estimated_hours / sel.actual_hours, 2.0) if sel.actual_hours > 0 else 0.0
            store.save_task(sel)
            st.rerun()
    else:
        st.caption("Start a task first to log hours.")
