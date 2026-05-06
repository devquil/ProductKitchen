import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, timedelta
from models.task import TaskStatus
from lib import store
from lib import analytics


SIGNAL_CONFIG = {
    "on_track":       {"emoji": "✅", "color": "#22c55e", "bg": "#f0fdf4"},
    "building":       {"emoji": "🔨", "color": "#3b82f6", "bg": "#eff6ff"},
    "coasting":       {"emoji": "⏸", "color": "#f59e0b", "bg": "#fffbeb"},
    "busy_idling":    {"emoji": "⚠️", "color": "#ef4444", "bg": "#fef2f2"},
    "suspicious":      {"emoji": "🤨", "color": "#f59e0b", "bg": "#fffbeb"},
    "off_track":      {"emoji": "🔴", "color": "#ef4444", "bg": "#fef2f2"},
    "no_tasks":       {"emoji": "📝", "color": "#f59e0b", "bg": "#fffbeb"},
    "no_habits":      {"emoji": "⏱", "color": "#f59e0b", "bg": "#fffbeb"},
    "empty":          {"emoji": "🚫", "color": "#6b7280", "bg": "#f9fafb"},
}


def _gauge_card(score: float, label: str, color: str, width: int = 200) -> str:
    pct = int(score * 100)
    bar_filled = int(score * 20)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    return f"""
    <div style="
        background: #fff;
        border: 2px solid {color}22;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        width: {width}px;
    ">
        <div style="font-size:48px;margin-bottom:8px;">{int(score*100)}%</div>
        <div style="font-size:11px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">{label}</div>
        <div style="margin-top:10px;font-size:13px;color:{color};font-family:monospace;">{bar}</div>
    </div>
    """


def render():
    st.title("📊 Combined Dashboard")
    st.markdown("**Honest output tracking** — tasks + habits together, so you can't fake one without the other.")
    st.markdown("---")

    tasks = store.get_tasks()
    habits = store.get_habits()

    # ── COMBINED SCORE ─────────────────────────────────────────────────────────
    signal = analytics.combined_score(tasks, habits)

    cfg = SIGNAL_CONFIG.get(signal.label, SIGNAL_CONFIG["empty"])
    ts = analytics.task_score(tasks)
    hs = analytics.habit_score(habits)

    sc, tc, hc = st.columns([2, 1, 1])

    with sc:
        st.markdown(f"""
        <div style="
            background: {cfg['bg']};
            border-left: 6px solid {cfg['color']};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 8px;
        ">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:36px;">{cfg['emoji']}</span>
                <div>
                    <div style="font-size:28px;font-weight:700;color:{cfg['color']};">
                        {signal.score:.0%}
                    </div>
                    <div style="font-size:14px;color:#374151;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">
                        {signal.label.replace('_', ' ')}
                    </div>
                </div>
            </div>
            <div style="margin-top:10px;font-size:14px;color:#4b5563;">{signal.message}</div>
        </div>
        """, unsafe_allow_html=True)

    with tc:
        st.markdown("**Task Score**")
        st.markdown(_gauge_card(ts, "tasks", "#3b82f6"), unsafe_allow_html=True)
        done = [t for t in tasks if t.status == TaskStatus.DONE]
        st.caption(f"{len(done)}/{len(tasks)} tasks done")

    with hc:
        st.markdown("**Habit Score**")
        st.markdown(_gauge_card(hs, "habits", "#22c55e"), unsafe_allow_html=True)
        st.caption(f"{len(habits)} habits tracked")

    st.markdown("---")

    # ── WEEKLY SUMMARY ─────────────────────────────────────────────────────────
    summary = analytics.weekly_summary(tasks, habits)

    st.subheader(f"📆 Week of {summary['week_start']} → {summary['week_end']}")
    m1, m2 = st.columns(2)
    m1.metric("Tasks Completed", summary["tasks_completed"])
    m2.metric("Hours Logged", f"{summary['total_hours']:.1f}h")

    # Day-by-day bar chart
    days = list(summary["by_day"].items())
    day_labels = [d[0][-5:] for d in days]   # MM-DD
    day_hours = [d[1]["hours"] for d in days]
    day_tasks = [d[1]["tasks_done"] for d in days]

    ch1, ch2 = st.columns(2)
    with ch1:
        st.bar_chart(day_hours, color="#4ade80")
        st.caption("Hours logged per day")
    with ch2:
        st.bar_chart(day_tasks, color="#3b82f6")
        st.caption("Tasks completed per day")

    st.markdown("---")

    # ── SIGNAL LEGEND ──────────────────────────────────────────────────────────
    with st.expander("📖 What do the signals mean?"):
        st.markdown("""
        | Signal | What it means |
        |---|---|
        | **✅ On Track** | Tasks done AND hours consistent — you're really producing. |
        | **🔨 Building** | Building momentum — keep going. |
        | **⏸ Coasting** | Tasks done but skipping habits — don't coast. |
        | **⚠️ Busy Idling** | Hours logged but few tasks — are you actually producing? |
        | **🤨 Suspicious** | Very few hours but lots of tasks — verify actual effort. |
        | **🔴 Off Track** | Low on both — focus on one thing at a time. |
        """)
