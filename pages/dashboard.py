import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from models.task import TaskStatus
from lib import store, analytics


SIGNAL_CONFIG = {
    "on_track":     ("✅", "#22c55e", "On Track"),
    "building":     ("🔨", "#3b82f6", "Building Momentum"),
    "coasting":     ("⏸",  "#f59e0b", "Coasting"),
    "busy_idling":  ("⚠️", "#ef4444", "Busy Idling"),
    "suspicious":   ("🤨", "#f59e0b", "Suspicious"),
    "off_track":    ("🔴", "#ef4444", "Off Track"),
    "no_tasks":     ("📝", "#f59e0b", "No Tasks Yet"),
    "no_habits":    ("⏱",  "#f59e0b", "No Habits Yet"),
    "empty":        ("🚫", "#6b7280", "Nothing Tracked Yet"),
}


def render():
    st.title("📊 Combined Dashboard")
    st.markdown("**Honest output tracking** — tasks + habits together, so you can't fake one without the other.")
    st.markdown("---")

    tasks = store.get_tasks()
    habits = store.get_habits()

    signal = analytics.combined_score(tasks, habits)
    ts = analytics.task_score(tasks)
    hs = analytics.habit_score(habits)
    done = len([t for t in tasks if t.status == TaskStatus.DONE])

    emoji, color, label = SIGNAL_CONFIG.get(signal.label, SIGNAL_CONFIG["empty"])

    sig_col, task_col, habit_col = st.columns([2, 1, 1])

    # Signal card using st.html (cleaner rendering than unsafe_allow_html)
    with sig_col:
        st.html(f"""
        <div style="
            border-left: 6px solid {color};
            background: #ffffff;
            border-radius: 8px;
            padding: 18px 22px;
            margin-bottom: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:6px;">
                <span style="font-size:38px;">{emoji}</span>
                <div>
                    <div style="font-size:30px;font-weight:700;color:{color};">
                        {signal.score:.0%}
                    </div>
                    <div style="font-size:13px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;">
                        {label}
                    </div>
                </div>
            </div>
            <div style="font-size:13px;color:#4b5563;">{signal.message}</div>
        </div>
        """)

    with task_col:
        st.metric("Task Score", f"{int(ts*100)}%")
        st.progress(ts)
        st.caption(f"{done}/{len(tasks)} tasks done")

    with habit_col:
        st.metric("Habit Score", f"{int(hs*100)}%")
        st.progress(hs)
        st.caption(f"{len(habits)} habits tracked")

    st.markdown("---")

    # Weekly summary
    summary = analytics.weekly_summary(tasks, habits)

    st.subheader(f"📆 {summary['week_start']} → {summary['week_end']}")
    m1, m2 = st.columns(2)
    m1.metric("Tasks Completed", summary["tasks_completed"])
    m2.metric("Hours Logged", f"{summary['total_hours']:.1f}h")

    days_data = list(summary["by_day"].items())
    ch1, ch2 = st.columns(2)
    with ch1:
        st.bar_chart({d[0]: d[1]["hours"] for d in days_data}, color="#4ade80")
        st.caption("Hours per day")
    with ch2:
        st.bar_chart({d[0]: d[1]["tasks_done"] for d in days_data}, color="#3b82f6")
        st.caption("Tasks per day")

    st.markdown("---")

    with st.expander("📖 What do the signals mean?"):
        st.markdown("""
| Signal | Meaning |
|---|---|
| **On Track** | Tasks done AND hours consistent — you're really producing. |
| **Building Momentum** | Building momentum — keep going. |
| **Coasting** | Tasks done but skipping habits — don't coast. |
| **Busy Idling** | Hours logged but few tasks — are you actually producing? |
| **Suspicious** | Very few hours but lots of tasks — verify actual effort. |
| **Off Track** | Low on both — focus on one thing at a time. |
""")
