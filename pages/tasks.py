import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime, date
from models.task import Task, Priority, TaskStatus, TASK_TAGS
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
    st.markdown("Tag your tasks — weights drive your output score.")

    st.session_state.setdefault("task_title", "")
    st.session_state.setdefault("task_desc", "")
    st.session_state.setdefault("task_est", 1.0)
    st.session_state.setdefault("task_due", None)
    st.session_state.setdefault("task_tag", "personal")
    st.session_state.setdefault("task_habit_id", None)

    tasks = store.get_tasks()

    # ── TAG LEGEND ────────────────────────────────────────────────────────────
    st.markdown("**🏷 Tag weights** &nbsp;*(higher weight = more impact on your score)*")
    tag_cols = st.columns(len(TASK_TAGS))
    for i, (tag_key, tag_info) in enumerate(TASK_TAGS.items()):
        with tag_cols[i]:
            st.markdown(
                f"<span style='color:{tag_info['color']};font-weight:bold;'>"
                f"{tag_info['label']}</span> "
                f"<code style='background:#f3f4f6;padding:1px 4px;border-radius:3px;'>"
                f"×{tag_info['weight']}</code>",
                unsafe_allow_html=True)
            st.caption(tag_info["description"])

    st.markdown("---")

    habits = store.get_habits()

    # ── ADD TASK FORM ──────────────────────────────────────────────────────────
    with st.form("add_task_form", clear_on_submit=True):
        st.markdown("**Add New Task**")
        c1, c2 = st.columns([3, 2])
        c1.text_input("Task title", key="task_title")
        c2.selectbox("Tag", list(TASK_TAGS.keys()),
                     index=list(TASK_TAGS.keys()).index(st.session_state.task_tag),
                     key="task_tag",
                     format_func=lambda t: TASK_TAGS[t]["label"])
        c3, c4 = st.columns(2)
        c3.text_input("Description", key="task_desc")
        c5, c6 = st.columns([1, 1])
        c5.number_input("Est. hours", 0.25, 24.0, 1.0, 0.25, key="task_est")
        c6.date_input("Due date", key="task_due")
        # Optional habit link
        habit_options = ["— None —"] + [h.id for h in habits]
        habit_labels = {h.id: f"{h.icon} {h.name}" for h in habits}
        habit_labels["__none__"] = "— None —"
        selected_habit_idx = 0
        if habits:
            habit_options = ["__none__"] + [h.id for h in habits]
            if st.session_state.task_habit_id and st.session_state.task_habit_id in habit_labels:
                selected_habit_idx = habit_options.index(st.session_state.task_habit_id)
        selected_habit = st.selectbox(
            "Link to habit (optional)",
            habit_options,
            index=selected_habit_idx,
            key="task_habit_id",
            format_func=lambda hid: habit_labels.get(hid, "— None —"))
        if st.form_submit_button("Add Task", use_container_width=True):
            if st.session_state.task_title.strip():
                due = st.session_state.task_due
                linked_habit = None
                if selected_habit != "__none__":
                    linked_habit = selected_habit
                task = Task.create(
                    title=st.session_state.task_title.strip(),
                    description=st.session_state.task_desc,
                    due_date=datetime.combine(due, datetime.min.time()) if due else None,
                    estimated_hours=st.session_state.task_est,
                    tag=st.session_state.task_tag,
                    habit_id=linked_habit,
                )
                store.save_task(task)
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

    # Tag filter
    filter_col, _ = st.columns([2, 4])
    with filter_col:
        tag_options = ["All"] + list(TASK_TAGS.keys())
        selected_filter = st.selectbox("Filter by tag:", tag_options,
                                       format_func=lambda t: "All tags" if t == "All" else TASK_TAGS[t]["label"])

    filtered = tasks if selected_filter == "All" else [t for t in tasks if t.tag == selected_filter]
    if not filtered:
        st.info(f"No {selected_filter} tasks found.")
        return

    for task in sorted(filtered, key=lambda t: (t.priority.value, t.due_date or date.max)):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 2])

        c1.markdown(f"**{task.title}**")
        if task.description:
            c1.caption(task.description[:70])

        # Tag badge
        tag_info = TASK_TAGS.get(task.tag, TASK_TAGS["personal"])
        c2.markdown(
            f"<span style='color:{tag_info['color']};font-weight:bold;font-size:12px;'>"
            f"{tag_info['label'].split()[0]} {task.tag}</span>",
            unsafe_allow_html=True)

        c3.markdown(
            f"<span style='color:{PRIO_COLOR[task.priority]};font-weight:bold'>{task.priority.value.upper()}</span>",
            unsafe_allow_html=True)
        c4.markdown(
            f"<span style='color:{STATUS_COLOR[task.status]}'>{task.status.value.replace('_',' ')}</span>",
            unsafe_allow_html=True)

        due_str = task.due_date.strftime("%b %d") if task.due_date else "—"
        if task.is_overdue:
            due_str = f"🔴 {due_str}"
        c5.markdown(f"`{due_str}`")
        c6.metric("Actual", f"{task.actual_hours:.1f}h")

        action = c7.segmented_control(
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
