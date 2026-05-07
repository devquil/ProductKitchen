import json
import os
from pathlib import Path
from datetime import date
from typing import List, Optional

from models.task import Task
from models.habit import Habit, HabitEntry, HabitBlock, SleepEntry


DATA_DIR = Path.home() / ".productkitchen"
DATA_FILE = DATA_DIR / "data.json"


def _load_data() -> dict:
    if not DATA_FILE.exists():
        return {"tasks": [], "habits": [], "habit_entries": [], "habit_blocks": [], "sleep_entries": []}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    # Migrate old data that might not have habit_blocks key
    if "habit_blocks" not in raw:
        raw["habit_blocks"] = []
    if "sleep_entries" not in raw:
        raw["sleep_entries"] = []
    return raw


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
    data["habit_blocks"] = [b for b in data.get("habit_blocks", []) if b["habit_id"] != habit_id]
    _save_data(data)


# ─── HABIT BLOCKS ─────────────────────────────────────────────────────────────

def get_habit_blocks(habit_id: Optional[str] = None,
                     task_id: Optional[str] = None,
                     block_date: Optional[date] = None) -> List[HabitBlock]:
    blocks = [HabitBlock.from_dict(b) for b in _load_data().get("habit_blocks", [])]
    if habit_id:
        blocks = [b for b in blocks if b.habit_id == habit_id]
    if task_id:
        blocks = [b for b in blocks if task_id in b.task_ids]
    if block_date:
        blocks = [b for b in blocks if b.date == block_date]
    return blocks


def save_habit_block(block: HabitBlock):
    data = _load_data()
    blocks = data.get("habit_blocks", [])
    idx = next((i for i, b in enumerate(blocks) if b["id"] == block.id), None)
    if idx is not None:
        blocks[idx] = block.to_dict()
    else:
        blocks.append(block.to_dict())
    data["habit_blocks"] = blocks
    _save_data(data)


def delete_habit_block(block_id: str):
    data = _load_data()
    data["habit_blocks"] = [b for b in data.get("habit_blocks", []) if b["id"] != block_id]
    _save_data(data)


# ─── HABIT ENTRIES ─────────────────────────────────────────────────────────────

def get_habit_entries(habit_id: Optional[str] = None,
                      entry_date: Optional[date] = None) -> List[HabitEntry]:
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
    """Returns total hours from blocks for this habit today."""
    blocks = get_habit_blocks(habit_id=habit_id)
    today = date.today()
    return sum(b.duration_hours for b in blocks if b.date == today and b.duration_hours > 0)


def get_hours_this_week(habit_id: str) -> float:
    """Returns total block hours for this habit this week."""
    from datetime import timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    blocks = get_habit_blocks(habit_id=habit_id)
    return sum(b.duration_hours for b in blocks
               if week_start <= b.date <= today and b.duration_hours > 0)


# ─── SLEEP ──────────────────────────────────────────────────────────────────────

def get_sleep_entries(days: int = 7) -> List[SleepEntry]:
    """Returns sleep entries for the last N days (including today)."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days - 1)
    all_entries = [SleepEntry.from_dict(e) for e in _load_data().get("sleep_entries", [])]
    return sorted([e for e in all_entries if e.date >= cutoff], key=lambda e: e.date)


def get_sleep_entry(date: date) -> Optional[SleepEntry]:
    """Returns sleep entry for a specific date, if any."""
    for e in _load_data().get("sleep_entries", []):
        if e.get("date") == date.isoformat():
            return SleepEntry.from_dict(e)
    return None


def save_sleep_entry(entry: SleepEntry):
    data = _load_data()
    entries = data.get("sleep_entries", [])
    idx = next((i for i, e in enumerate(entries) if e["id"] == entry.id), None)
    if idx is not None:
        entries[idx] = entry.to_dict()
    else:
        entries.append(entry.to_dict())
    data["sleep_entries"] = entries
    _save_data(data)


def delete_sleep_entry(entry_id: str):
    data = _load_data()
    data["sleep_entries"] = [e for e in data.get("sleep_entries", []) if e["id"] != entry_id]
    _save_data(data)
