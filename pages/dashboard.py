import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from models.task import TaskStatus, TASK_TAGS
from lib import store, analytics
from lib.levels import (
    get_output_level, get_streak_level,
    level_progress, streak_progress,
    OUTPUT_LEVELS, STREAK_LEVELS,
    get_tag_level, get_peak_rank, tag_points,
    _TAG_LEVELS,
)


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


def level_badge_html(level: dict, progress: float, progress_label: str,
                     bar_color: str, rank_label: str, rank_max: str) -> str:
    return f"""
    <div style="
        background:{level['badge_bg']};
        border: 2px solid {level['border']};
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        margin-bottom: 10px;
    ">
        <!-- Header row -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:32px;">{level['emoji']}</span>
            <div>
                <div style="font-size:16px;font-weight:700;color:{level['color']};">
                    {level['name']}
                </div>
                <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;">
                    {rank_label}
                </div>
            </div>
            <div style="margin-left:auto;text-align:right;">
                <div style="font-size:20px;font-weight:800;color:{level['color']};">
                    {rank_max}
                </div>
                <div style="font-size:10px;color:#9ca3af;">{rank_label}</div>
            </div>
        </div>
        <!-- Progress bar -->
        <div style="background:#e5e7eb;border-radius:999px;height:8px;overflow:hidden;margin-bottom:6px;">
            <div style="
                background:{bar_color};width:{int(progress*100)}%;height:100%;
                border-radius:999px;transition:width 0.4s ease;
            "></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;">
            <span>{progress_label}</span>
            <span>{int(progress*100)}% to next</span>
        </div>
        <!-- Description -->
        <div style="margin-top:8px;font-size:11px;color:#6b7280;font-style:italic;">
            {level['description']}
        </div>
    </div>
    """


def render():
    st.title("📊 Combined Dashboard")
    st.markdown("**Honest output tracking** — tasks + habits together, so you can't fake one without the other.")
    st.markdown("---")

    tasks = store.get_tasks()
    habits = store.get_habits()

    signal    = analytics.combined_score(tasks, habits)
    ts        = analytics.task_score(tasks)
    hs        = analytics.habit_score(habits)
    streak    = analytics.current_streak(habits)
    done      = len([t for t in tasks if t.status == TaskStatus.DONE])

    # ── Levels ──────────────────────────────────────────────────────────────────
    out_level = get_output_level(signal.score)
    str_level = get_streak_level(streak)
    out_prog  = level_progress(signal.score, out_level)
    str_prog  = streak_progress(streak, str_level)

    # Find next level labels for "X to next" display
    out_next = None
    str_next = None
    try:
        out_idx = OUTPUT_LEVELS.index(out_level)
        if out_idx < len(OUTPUT_LEVELS) - 1:
            out_next = OUTPUT_LEVELS[out_idx + 1]
    except ValueError:
        pass
    try:
        str_idx = STREAK_LEVELS.index(str_level)
        if str_idx < len(STREAK_LEVELS) - 1:
            str_next = STREAK_LEVELS[str_idx + 1]
    except ValueError:
        pass

    out_next_label = f"{out_next['emoji']} {out_next['name']}" if out_next else "MAX"
    str_next_label = f"{str_next['emoji']} {str_next['name']}" if str_next else "MAX"

    # ── Top row: Signal card + Output Level + Streak Level ────────────────────
    emoji, color, label = SIGNAL_CONFIG.get(signal.label, SIGNAL_CONFIG["empty"])

    sig_col, lvl_col = st.columns([2, 2])

    with sig_col:
        st.html(f"""
        <div style="
            border-left: 6px solid {color};
            background: #ffffff;
            border-radius: 8px;
            padding: 18px 22px;
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

    with lvl_col:
        # Two level badges stacked
        out_badge = level_badge_html(
            level=out_level,
            progress=out_prog,
            progress_label=f"Score {signal.score:.0%} → {out_next_label}",
            bar_color=out_level["color"],
            rank_label="Output Rank",
            rank_max=f"{signal.score:.0%}",
        )
        str_badge = level_badge_html(
            level=str_level,
            progress=str_prog,
            progress_label=f"{streak} day streak → {str_next_label}",
            bar_color=str_level["color"],
            rank_label="Streak Rank",
            rank_max=f"🔥 {streak}d",
        )
        st.html(f"<div style='display:flex;flex-direction:column;gap:4px;'>{out_badge}{str_badge}</div>")

    # ── Per-tag rank cards ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏷 Tag Ranks")

    peak = get_peak_rank(tasks)
    all_tag_html = ""
    tag_card_cols = st.columns([1, 1, 1, 1])

    for i, tag in enumerate(["business", "fitness", "personal", "hobby"]):
        lvl, prog = get_tag_level(tasks, tag)
        pts = tag_points(tasks, tag)
        levels = _TAG_LEVELS[tag]
        max_lvl = levels[-1]
        is_peak = lvl["name"] == peak["name"] and pts > 0
        tag_info = TASK_TAGS.get(tag, {})

        # Progress bar within current level
        lvl_idx = levels.index(lvl)
        next_pts = levels[lvl_idx + 1]["min_pts"] if lvl_idx < len(levels) - 1 else lvl["min_pts"]
        range_pts = next_pts - lvl["min_pts"]
        within_prog = (pts - lvl["min_pts"]) / range_pts if range_pts > 0 else 1.0
        bar_w = int(within_prog * 100)

        with tag_card_cols[i]:
            st.html(f"""
            <div style="
                background:{lvl['badge_bg']};
                border: 2px solid {lvl['border'] if is_peak else '#e5e7eb'};
                border-radius: 12px; padding: 14px;
                {'box-shadow:0 0 0 2px '+lvl['color'] if is_peak else ''}
            ">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="font-size:26px;">{lvl['emoji']}</span>
                    <div>
                        <div style="font-size:13px;font-weight:700;color:{lvl['color']};">
                            {lvl['name']}
                        </div>
                        <div style="font-size:11px;color:#9ca3af;">{tag_info.get('label', tag)} · ×{tag_info.get('weight',1)}</div>
                    </div>
                    {'<span style="margin-left:auto;font-size:10px;font-weight:700;color:#22c55e;">⭐ PEAK</span>' if is_peak else ''}
                </div>
                <div style="background:#e5e7eb;border-radius:999px;height:7px;overflow:hidden;margin-bottom:6px;">
                    <div style="background:{lvl['color']};width:{bar_w}%;height:100%;border-radius:999px;transition:width 0.4s;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:10px;color:#6b7280;">
                    <span>{pts:.0f} pts</span>
                    <span>{int(within_prog*100)}% to {levels[lvl_idx+1]['name'] if lvl_idx < len(levels)-1 else 'MAX'}</span>
                </div>
                <div style="margin-top:6px;font-size:10px;color:#9ca3af;font-style:italic;">
                    {lvl['description']}
                </div>
            </div>
            """)

    # ── Score columns ──────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("Task Score", f"{int(ts*100)}%")
    m1.progress(ts)
    m1.caption(f"{done}/{len(tasks)} tasks done")

    m2.metric("Habit Score", f"{int(hs*100)}%")
    m2.progress(hs)
    m2.caption(f"{len(habits)} habits tracked")

    m3.metric("Current Streak", f"🔥 {streak} days")
    # Visual streak bar
    streak_max = 7  # visual reference
    streak_bar = min(streak / streak_max, 1.0)
    m3.progress(streak_bar)
    m3.caption(f"{streak} consecutive days met")

    # ── Tag-specific progress rings ────────────────────────────────────────────
    tag_data = analytics.tag_scores(tasks)
    st.markdown("---")
    st.subheader("🏷 Tag Progress")

    tag_ring_html = ""
    for tag_key, info in tag_data.items():
        pct = int(info["score"] * 100)
        bar_w = int(info["score"] * 100)
        badge = "✅ Done" if info["done"] == info["total"] and info["total"] > 0 else \
                f"{info['done']}/{info['total']} tasks"
        tag_ring_html += f"""
        <div style="
            display:flex; align-items:center; gap:14px;
            background:#ffffff;
            border-radius:10px; padding:10px 16px;
            border-left:5px solid {info['color']};
            box-shadow:0 1px 3px rgba(0,0,0,0.07);
            margin-bottom:8px;
        ">
            <div style="width:60px;text-align:center;flex-shrink:0;">
                <div style="font-size:22px;font-weight:800;color:{info['color']};">{pct}%</div>
                <div style="font-size:10px;color:#9ca3af;">score</div>
            </div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="font-size:14px;font-weight:700;color:{info['color']};">
                        {info['label']}
                    </span>
                    <span style="
                        background:{info['color']}22; color:{info['color']};
                        font-size:10px;font-weight:700;padding:1px 6px;border-radius:999px;
                    ">×{info['weight']}</span>
                    <span style="font-size:11px;color:#9ca3af;margin-left:auto;">{badge}</span>
                </div>
                <div style="background:#e5e7eb;border-radius:999px;height:8px;overflow:hidden;">
                    <div style="
                        background:{info['color']};width:{bar_w}%;height:100%;
                        border-radius:999px;transition:width 0.4s;
                    "></div>
                </div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px;">
                    {info['description']} &nbsp;·&nbsp; {info['hours']:.1f}h logged
                </div>
            </div>
        </div>
        """
    st.html(tag_ring_html)

    st.markdown("---")

    # ── Level Roadmap ─────────────────────────────────────────────────────────
    st.subheader("🏅 Level Roadmap")

    tab_output, tab_streak = st.tabs(["📈 Output Levels", "🔥 Streak Levels"])

    with tab_output:
        for lvl in OUTPUT_LEVELS:
            is_active = (lvl["name"] == out_level["name"])
            bg = lvl["badge_bg"] if is_active else "#f9fafb"
            border = lvl["border"] if is_active else "#e5e7eb"
            prefix = "👉 " if is_active else "   "
            st.html(f"""
            <div style="
                background:{bg};
                border-left: 4px solid {border};
                border-radius: 6px;
                padding: 8px 14px;
                margin-bottom: 4px;
                display:flex;
                align-items:center;
                gap:10px;
            ">
                <span style="font-size:20px;">{lvl['emoji']}</span>
                <div>
                    <div style="font-weight:700;font-size:13px;color:{lvl['color']};">
                        {prefix}{lvl['name']} <span style="font-weight:400;font-size:11px;color:#9ca3af;">
                            from {int(lvl['min_score']*100)}%
                        </span>
                    </div>
                    <div style="font-size:11px;color:#6b7280;">{lvl['description']}</div>
                </div>
                {'<span style="margin-left:auto;font-size:11px;font-weight:700;color:#22c55e;">✓ YOU ARE HERE</span>' if is_active else ''}
            </div>
            """)

    with tab_streak:
        for lvl in STREAK_LEVELS:
            is_active = (lvl["name"] == str_level["name"])
            bg = lvl["badge_bg"] if is_active else "#f9fafb"
            border = lvl["border"] if is_active else "#e5e7eb"
            prefix = "👉 " if is_active else "   "
            st.html(f"""
            <div style="
                background:{bg};
                border-left: 4px solid {border};
                border-radius: 6px;
                padding: 8px 14px;
                margin-bottom: 4px;
                display:flex;
                align-items:center;
                gap:10px;
            ">
                <span style="font-size:20px;">{lvl['emoji']}</span>
                <div>
                    <div style="font-weight:700;font-size:13px;color:{lvl['color']};">
                        {prefix}{lvl['name']} <span style="font-weight:400;font-size:11px;color:#9ca3af;">
                            from {lvl['min_days']} days
                        </span>
                    </div>
                    <div style="font-size:11px;color:#6b7280;">{lvl['description']}</div>
                </div>
                {'<span style="margin-left:auto;font-size:11px;font-weight:700;color:#22c55e;">✓ YOU ARE HERE</span>' if is_active else ''}
            </div>
            """)

    st.markdown("---")

    # ── Weekly summary ─────────────────────────────────────────────────────────
    summary = analytics.weekly_summary(tasks, habits)

    st.subheader(f"📆 {summary['week_start']} → {summary['week_end']}")
    w1, w2 = st.columns(2)
    w1.metric("Tasks Completed", summary["tasks_completed"])
    w2.metric("Hours Logged", f"{summary['total_hours']:.1f}h")

    days_data = list(summary["by_day"].items())
    ch1, ch2 = st.columns(2)
    with ch1:
        st.bar_chart({d[0]: d[1]["hours"] for d in days_data}, color="#4ade80")
        st.caption("Hours per day")

    # Per-tag task completion for the week
    tag_week_data = {}
    for tag_key, tag_info in TASK_TAGS.items():
        tag_tasks_done = len([
            t for t in tasks
            if t.tag == tag_key
            and t.status == TaskStatus.DONE
            and t.completed_at
            and date.fromisoformat(t.completed_at.isoformat()[:10]) >= date.fromisoformat(summary["week_start"])
        ])
        tag_week_data[tag_info["label"]] = tag_tasks_done

    with ch2:
        if any(v > 0 for v in tag_week_data.values()):
            st.bar_chart(tag_week_data, color="#3b82f6")
        else:
            st.bar_chart({d[0]: d[1]["tasks_done"] for d in days_data}, color="#3b82f6")
        st.caption("Tasks done this week (by tag)")

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
