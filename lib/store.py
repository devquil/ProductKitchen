import json
import os
from pathlib import Path
from datetime import date
from typing import List, Optional

from models.task import Task
from models.habit import Habit, HabitEntry


DATA_DIR = Path.home() / ".productkitchen"
DATA_FILE = DATA_DIR / "data.json"


def _load_data() -> dict:
    if not DATA_FILE.exists():
        return {"tasks": [], "habits": [], "habit_entries": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─── TASKS ────────────────────────────────────────────────────────────────────

def get_tasks() -> List[Task]:
    return [Task.from_dict(t) for t in _load_data()["tasks"]]


def save_task(task: Task):
    data = _load_data()
    tasks = data["tasks"]
    idx = next((i for i, t in enumerate(tasks) if t["id"] == task.id), None)
    if idx is not None:
        tasks[idx] = task.to_dict()
    else:
        tasks.append(task.to_dict())
    data["tasks"] = tasks
    _save_data(data)


def delete_task(task_id: str):
    data = _load_data()
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    _save_data(data)


# ─── HABITS ───────────────────────────────────────────────────────────────────

def get_habits() -> List[Habit]:
    return [Habit.from_dict(h) for h in _load_data()["habits"]]


def save_habit(habit: Habit):
    data = _load_data()
    habits = data["habits"]
    idx = next((i for i, h in enumerate(habits) if h["id"] == habit.id), None)
    if idx is not None:
        habits[idx] = habit.to_dict()
    else:
        habits.append(habit.to_dict())
    data["habits"] = habits
    _save_data(data)


def delete_habit(habit_id: str):
    data = _load_data()
    data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
    data["habit_entries"] = [e for e in data.get("habit_entries", []) if e["habit_id"] != habit_id]
    _save_data(data)


# ─── HABIT ENTRIES ─────────────────────────────────────────────────────────────

def get_habit_entries(habit_id: Optional[str] = None, entry_date: Optional[date] = None) -> List[HabitEntry]:
    entries = [HabitEntry.from_dict(e) for e in _load_data().get("habit_entries", [])]
    if habit_id:
        entries = [e for e in entries if e.habit_id == habit_id]
    if entry_date:
        entries = [e for e in entries if e.date == entry_date]
    return entries


def save_habit_entry(entry: HabitEntry):
    data = _load_data()
    entries = data.get("habit_entries", [])
    idx = next(
        (i for i, e in enumerate(entries)
         if e["habit_id"] == entry.habit_id and e["date"] == entry.date.isoformat()),
        None
    )
    if idx is not None:
        entries[idx] = entry.to_dict()
    else:
        entries.append(entry.to_dict())
    data["habit_entries"] = entries
    _save_data(data)


def delete_habit_entry(entry_id: str):
    data = _load_data()
    data["habit_entries"] = [e for e in data.get("habit_entries", []) if e["id"] != entry_id]
    _save_data(data)


def get_today_hours(habit_id: str) -> float:
    today = date.today().isoformat()
    entries = _load_data().get("habit_entries", [])
    total = sum(
        e["hours_worked"]
        for e in entries
        if e["habit_id"] == habit_id and e["date"] == today
    )
    return total


def get_hours_this_week(habit_id: str) -> float:
    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    entries = _load_data().get("habit_entries", [])
    return sum(
        e["hours_worked"]
        for e in entries
        if e["habit_id"] == habit_id
        and date.fromisoformat(e["date"]) >= week_start
    )
