import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime, date
from models.task import Task, Priority, TaskStatus
from lib import store


PRIO_COLOR = {Priority.HIGH: "#ef4444", Priority.MEDIUM: "#f59e0b", Priority.LOW: "#6b7280"}
STATUS_COLOR = {
    TaskStatus.PENDING: "#6b7280",
    TaskStatus.IN_PROGRESS: "#3b82f6",
    TaskStatus.DONE: "#22c55e",
    TaskStatus.BLOCKED: "#a855f7",
}


def render():
    st.title("✅ Tasks Tracker")
    st.markdown("Add tasks, log hours, track efficiency.")

    # Init form session state
    st.session_state.setdefault("task_title", "")
    st.session_state.setdefault("task_desc", "")
    st.session_state.setdefault("task_est", 1.0)
    st.session_state.setdefault("task_due", None)

    tasks = store.get_tasks()

    # ── ADD TASK FORM ──────────────────────────────────────────────────────────
    with st.form("add_task_form", clear_on_submit=True):
        st.markdown("**Add New Task**")
        c1, c2 = st.columns([3, 2])
        c1.text_input("Task title", key="task_title")
        c2.text_input("Description", key="task_desc")
        c3, c4, c5 = st.columns(3)
        c3.number_input("Est. hours", 0.25, 24.0, 1.0, 0.25, key="task_est")
        c4.date_input("Due date", key="task_due")
        c5.markdown("")  # spacer
        if st.form_submit_button("Add Task", use_container_width=True):
            if st.session_state.task_title.strip():
                due = st.session_state.task_due
                task = Task.create(
                    title=st.session_state.task_title.strip(),
                    description=st.session_state.task_desc,
                    due_date=datetime.combine(due, datetime.min.time()) if due else None,
                    estimated_hours=st.session_state.task_est,
                )
                store.save_task(task)
                st.session_state.task_title = ""
                st.session_state.task_desc = ""
                st.success("Task added!")
            else:
                st.error("Task title is required.")

    st.markdown("---")

    # ── METRICS ────────────────────────────────────────────────────────────────
    if tasks:
        done = [t for t in tasks if t.status == TaskStatus.DONE]
        in_prog = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(tasks))
        m2.metric("Done", len(done))
        m3.metric("In Progress", len(in_prog))
        m4.metric("Pending", len([t for t in tasks if t.status == TaskStatus.PENDING]))

    # ── TASK LIST ─────────────────────────────────────────────────────────────
    if not tasks:
        st.info("No tasks yet. Add one above.")
        return

    for task in sorted(tasks, key=lambda t: (t.priority.value, t.due_date or date.max)):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 1, 1, 1, 2])

        c1.markdown(f"**{task.title}**")
        if task.description:
            c1.caption(task.description[:70])

        c2.markdown(
            f"<span style='color:{PRIO_COLOR[task.priority]};font-weight:bold'>{task.priority.value.upper()}</span>",
            unsafe_allow_html=True)
        c3.markdown(
            f"<span style='color:{STATUS_COLOR[task.status]}'>{task.status.value.replace('_',' ')}</span>",
            unsafe_allow_html=True)

        due_str = task.due_date.strftime("%b %d") if task.due_date else "—"
        if task.is_overdue:
            due_str = f"🔴 {due_str}"
        c4.markdown(f"`{due_str}`")
        c5.metric("Actual", f"{task.actual_hours:.1f}h")

        action = c6.segmented_control(
            "Action", ["Start", "Done", "Del"],
            default=None, label_visibility="collapsed", key=f"seg_{task.id}")

        if action == "Start" and task.status == TaskStatus.PENDING:
            task.start()
            store.save_task(task)
            st.rerun()
        elif action == "Done":
            store.save_task(task)
            st.rerun()
        elif action == "Del":
            store.delete_task(task.id)
            st.rerun()

        st.markdown("---")

    # ── LOG HOURS ──────────────────────────────────────────────────────────────
    st.subheader("⏱ Log Hours")
    in_prog = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    if not in_prog:
        st.caption("Start a task to log hours.")
        return

    sel_idx = st.selectbox(
        "Task:", range(len(in_prog)),
        format_func=lambda i: f"{in_prog[i].title} ({in_prog[i].actual_hours:.1f}h)",
        key="log_task_idx")
    sel = in_prog[sel_idx]
    log_hrs = st.number_input("Hours to add", 0.25, 12.0, 0.5, 0.25, key="log_hrs")
    if st.button(f"Log {log_hrs}h", key="log_hrs_btn", use_container_width=True):
        sel.actual_hours += log_hrs
        if sel.actual_hours > 0:
            sel.efficiency = min(sel.estimated_hours / sel.actual_hours, 2.0)
        store.save_task(sel)
        st.rerun()
