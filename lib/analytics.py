from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from models.task import Task, TaskStatus, Priority, TASK_TAGS
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
    Task efficiency: completions weighted by tag importance.
    Business tasks count 3x more than hobby tasks.
    """
    if not tasks:
        return 0.0

    completed = [t for t in tasks if t.status == TaskStatus.DONE]
    if not completed:
        # All pending/in-progress — measure effort vs deadline
        effort = sum(t.actual_hours * t.tag_weight() for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        total_est = sum(t.estimated_hours * t.tag_weight() for t in tasks)
        if total_est == 0:
            return 0.0
        effort_ratio = min(effort / total_est, 1.0)
        return effort_ratio * 0.7  # can't get full score without completing

    # Weighted completion: each completed task's weight = tag_weight
    total_weight = sum(t.tag_weight() for t in completed)
    max_possible_weight = sum(t.tag_weight() for t in tasks)
    completion_rate = total_weight / max_possible_weight if max_possible_weight > 0 else 0.0

    # Average efficiency across completed tasks (also weighted)
    total_eff_weight = sum(t.efficiency * t.tag_weight() for t in completed)
    avg_eff = total_eff_weight / total_weight if total_weight > 0 else 0.0

    # Blend: 60% completion (tag-weighted), 40% speed
    score = completion_rate * 0.6 + min(avg_eff, 1.0) * 0.4

    # Penalise overdue high-priority tasks still open
    overdue_penalty = sum(
        0.05 * t.priority.value * t.tag_weight()
        for t in tasks
        if t.is_overdue and t.status != TaskStatus.DONE
    )
    return max(0.0, min(score - overdue_penalty, 1.0))


def habit_score(habits: List[Habit]) -> float:
    """
    Habit score: block hours logged today vs goal across all habits.
    Only counts hours from work blocks linked to tasks — no loose entries.
    """
    if not habits:
        return 0.0

    today = date.today()
    scores = []
    for habit in habits:
        blocks = store.get_habit_blocks(habit_id=habit.id)
        today_hours = sum(b.duration_hours for b in blocks if b.date == today and b.duration_hours > 0)
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

    # Hours this week — from blocks only (linked to tasks)
    all_blocks = []
    for h in habits:
        all_blocks.extend(store.get_habit_blocks(habit_id=h.id))
    week_blocks = [b for b in all_blocks if week_start <= b.date <= week_end]
    total_hours = sum(b.duration_hours for b in week_blocks)

    # By-day breakdown
    days = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_blocks = [b for b in week_blocks if b.date == d]
        days[d.isoformat()] = {
            "hours": sum(b.duration_hours for b in day_blocks),
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


def tag_scores(tasks: List[Task]) -> dict:
    """
    Returns per-tag progress breakdown.
    Each tag shows: completed_weight / total_weight, hours logged, task counts.
    """
    result = {}
    for tag_key, tag_info in TASK_TAGS.items():
        tag_tasks = [t for t in tasks if t.tag == tag_key]
        if not tag_tasks:
            result[tag_key] = {
                "label": tag_info["label"],
                "color": tag_info["color"],
                "weight": tag_info["weight"],
                "description": tag_info["description"],
                "score": 0.0,
                "total": 0,
                "done": 0,
                "hours": 0.0,
            }
            continue

        completed = [t for t in tag_tasks if t.status == TaskStatus.DONE]
        total_weight = sum(t.tag_weight() for t in tag_tasks)
        done_weight = sum(t.tag_weight() for t in completed)
        total_hours = sum(t.actual_hours for t in tag_tasks)

        # Score: completion rate × efficiency blend (same formula as task_score but per tag)
        completion_rate = done_weight / total_weight if total_weight > 0 else 0.0
        avg_eff = (sum(t.efficiency for t in completed) / len(completed)) if completed else 0.0
        score = completion_rate * 0.6 + min(avg_eff, 1.0) * 0.4

        result[tag_key] = {
            "label": tag_info["label"],
            "color": tag_info["color"],
            "weight": tag_info["weight"],
            "description": tag_info["description"],
            "score": score,
            "total": len(tag_tasks),
            "done": len(completed),
            "hours": total_hours,
        }
    return result


def current_streak(habits):
    """
    Returns the number of consecutive days (ending today) where the combined
    habit block hours met or exceeded the combined daily goal.
    """
    if not habits:
        return 0

    today = date.today()
    total_goal = sum(h.goal_hours for h in habits)

    from collections import defaultdict
    day_hours = defaultdict(float)
    for h in habits:
        blocks = store.get_habit_blocks(habit_id=h.id)
        for b in blocks:
            day_hours[b.date] += b.duration_hours

    streak = 0
    check_date = today
    while True:
        hrs = day_hours.get(check_date, 0.0)
        if hrs >= total_goal:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak
