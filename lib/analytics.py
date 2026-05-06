from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from models.task import Task, TaskStatus, Priority
from models.habit import Habit
from lib import store


@dataclass
class EfficiencySignal:
    score: float           # 0.0–1.0
    label: str             # "on_track", "busy_idling", "coasting", "suspicious"
    message: str
    color: str


def task_score(tasks: List[Task]) -> float:
    """
    Task efficiency: how many done vs estimated.
    Also penalises overdue HIGH priority tasks.
    """
    if not tasks:
        return 0.0

    completed = [t for t in tasks if t.status == TaskStatus.DONE]
    if not completed:
        # All pending/in-progress — measure effort vs deadline
        effort = sum(t.actual_hours for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        total_est = sum(t.estimated_hours for t in tasks)
        if total_est == 0:
            return 0.0
        effort_ratio = min(effort / total_est, 1.0)
        return effort_ratio * 0.7  # can't get full score without completing

    # Completion rate weighted by priority
    total_weight = sum(p.value for p in [t.priority for t in completed])
    max_weight = total_weight  # simplified

    # Average efficiency across completed tasks
    avg_eff = sum(t.efficiency for t in completed) / len(completed) if completed else 0.0
    completion_rate = len(completed) / len(tasks)

    # Blend: 60% completion, 40% speed
    score = completion_rate * 0.6 + min(avg_eff, 1.0) * 0.4

    # Penalise overdue high-priority tasks still open
    overdue_penalty = sum(
        0.05 * t.priority.value
        for t in tasks
        if t.is_overdue and t.status != TaskStatus.DONE
    )
    return max(0.0, min(score - overdue_penalty, 1.0))


def habit_score(habits: List[Habit]) -> float:
    """
    Habit score: hours logged today vs goal across all habits.
    """
    if not habits:
        return 0.0

    today = date.today()
    scores = []
    for habit in habits:
        entries = store.get_habit_entries(habit_id=habit.id)
        today_entries = [e for e in entries if e.date == today]
        today_hours = sum(e.hours_worked for e in today_entries)
        progress = min(today_hours / habit.goal_hours, 1.0)
        scores.append(progress)

    return sum(scores) / len(scores)


def combined_score(task_tasks: List[Task], habits: List[Habit]) -> EfficiencySignal:
    ts = task_score(task_tasks)
    hs = habit_score(habits)

    if not task_tasks and not habits:
        return EfficiencySignal(0.0, "empty", "No data yet — start tracking!", "#6b7280")

    if not task_tasks:
        hs_scaled = hs
        return EfficiencySignal(
            score=hs_scaled,
            label="no_tasks",
            message="No tasks yet — add tasks to measure true output.",
            color="#f59e0b",
        )

    if not habits:
        ts_scaled = ts
        return EfficiencySignal(
            score=ts_scaled,
            label="no_habits",
            message="No habits tracked — add habits to measure consistency.",
            color="#f59e0b",
        )

    combined = (ts * 0.5) + (hs * 0.5)

    # Determine signal
    total_task_hours = sum(t.actual_hours for t in task_tasks if t.status == TaskStatus.DONE)
    completed = [t for t in task_tasks if t.status == TaskStatus.DONE]
    total_est = sum(t.estimated_hours for t in completed) if completed else 0

    hours_per_task = total_task_hours / len(completed) if completed else 0
    avg_est = total_est / len(completed) if completed else 1

    # Signal logic
    if combined >= 0.75 and ts >= 0.6 and hs >= 0.6:
        label, message, color = "on_track", "On track — tasks done and hours consistent.", "#22c55e"
    elif hs >= 0.6 and ts < 0.3 and total_task_hours > avg_est * 2:
        label, message, color = (
            "busy_idling",
            "Hours logged but few tasks done — are you actually producing?",
            "#ef4444",
        )
    elif ts >= 0.6 and hs < 0.3:
        label, message, color = (
            "coasting",
            "Tasks done but not maintaining habit hours — don't coast yet.",
            "#f59e0b",
        )
    elif ts >= 0.8 and total_task_hours < avg_est * 0.5 and len(completed) > 2:
        label, message, color = (
            "suspicious",
            "Very few hours but tasks done fast — verify actual effort.",
            "#f59e0b",
        )
    elif combined < 0.3:
        label, message, color = "off_track", "Off track — focus on one thing at a time.", "#ef4444"
    else:
        label, message, color = "building", "Building momentum — keep going.", "#3b82f6"

    return EfficiencySignal(score=combined, label=label, message=message, color=color)


def weekly_summary(tasks: List[Task], habits: List[Habit]) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Tasks this week
    week_tasks = [
        t for t in tasks
        if t.completed_at and date.fromisoformat(t.completed_at.isoformat()[:10]) >= week_start
    ]

    # Hours this week
    habit_ids = [h.id for h in habits]
    all_entries = []
    for hid in habit_ids:
        all_entries.extend(store.get_habit_entries(habit_id=hid))
    week_entries = [
        e for e in all_entries
        if week_start <= e.date <= week_end
    ]
    total_hours = sum(e.hours_worked for e in week_entries)

    # By-day breakdown
    days = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_entries = [e for e in week_entries if e.date == d]
        days[d.isoformat()] = {
            "hours": sum(e.hours_worked for e in day_entries),
            "tasks_done": len([
                t for t in week_tasks
                if t.completed_at and date.fromisoformat(t.completed_at.isoformat()[:10]) == d
            ]),
        }

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "tasks_completed": len(week_tasks),
        "total_hours": total_hours,
        "by_day": days,
    }
