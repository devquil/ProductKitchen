from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
import uuid


@dataclass
class HabitEntry:
    id: str
    habit_id: str
    date: date
    hours_worked: float
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "date": self.date.isoformat(),
            "hours_worked": self.hours_worked,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HabitEntry":
        return cls(
            id=d["id"],
            habit_id=d["habit_id"],
            date=date.fromisoformat(d["date"]),
            hours_worked=d["hours_worked"],
            notes=d.get("notes", ""),
        )


@dataclass
class HabitBlock:
    """
    A focused work session linking a habit (work block type) to one or more tasks.
    This is the ONLY way to log hours — no loose entries without a task.
    """
    id: str
    habit_id: str
    task_ids: List[str]          # one or more tasks worked on in this block
    date: date
    started_at: datetime
    duration_hours: float = 0.0  # 0 while open
    break_seconds: int = 0        # accumulated break seconds in this block
    notes: str = ""

    @staticmethod
    def create(habit_id: str, task_ids: List[str], date: date,
               started_at: datetime) -> "HabitBlock":
        return HabitBlock(
            id=str(uuid.uuid4()),
            habit_id=habit_id,
            task_ids=task_ids,
            date=date,
            started_at=started_at,
            duration_hours=0.0,
            break_seconds=0,
            notes="",
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "task_ids": self.task_ids,
            "date": self.date.isoformat(),
            "started_at": self.started_at.isoformat(),
            "duration_hours": self.duration_hours,
            "break_seconds": self.break_seconds,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HabitBlock":
        # Handle migration from old single task_id field
        task_ids = d.get("task_ids")
        if task_ids is None:
            old_id = d.get("task_id", "")
            task_ids = [old_id] if old_id else []
        return cls(
            id=d["id"],
            habit_id=d["habit_id"],
            task_ids=task_ids,
            date=date.fromisoformat(d["date"]),
            started_at=datetime.fromisoformat(d["started_at"]),
            duration_hours=d.get("duration_hours", 0.0),
            break_seconds=d.get("break_seconds", 0),
            notes=d.get("notes", ""),
        )


@dataclass
class SleepEntry:
    """A sleep log entry — tracks bedtime, wake time, cycles, and quality."""
    id: str
    date: date           # date of the sleep (night of)
    bedtime: datetime    # when you went to bed
    wake_time: Optional[datetime] = None
    cycles: int = 0      # number of complete 90-min sleep cycles
    quality: int = 0    # 1-5 rating
    notes: str = ""

    @staticmethod
    def create(date: date, bedtime: datetime) -> "SleepEntry":
        return SleepEntry(
            id=str(uuid.uuid4()),
            date=date,
            bedtime=bedtime,
        )

    @property
    def duration_hours(self) -> float:
        if not self.wake_time:
            return 0.0
        return (self.wake_time - self.bedtime).total_seconds() / 3600

    @property
    def cycle_label(self) -> str:
        labels = {0: "—", 1: "1 cycle", 2: "2 cycles", 3: "3 cycles",
                  4: "4 cycles", 5: "5 cycles", 6: "6 cycles", 7: "7+ cycles"}
        return labels.get(self.cycles, f"{self.cycles} cycles")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "bedtime": self.bedtime.isoformat(),
            "wake_time": self.wake_time.isoformat() if self.wake_time else None,
            "cycles": self.cycles,
            "quality": self.quality,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SleepEntry":
        wake = None
        if d.get("wake_time"):
            try:
                wake = datetime.fromisoformat(d["wake_time"])
            except (ValueError, TypeError):
                wake = None
        bedtime = None
        if d.get("bedtime"):
            try:
                bedtime = datetime.fromisoformat(d["bedtime"])
            except (ValueError, TypeError):
                bedtime = None
        return cls(
            id=d["id"],
            date=date.fromisoformat(d["date"]),
            bedtime=bedtime or datetime.now(),
            wake_time=wake,
            cycles=d.get("cycles", 0),
            quality=d.get("quality", 0),
            notes=d.get("notes", ""),
        )


@dataclass
class Habit:
    id: str
    name: str
    description: str = ""
    goal_hours: float = 8.0
    created_at: datetime = field(default_factory=datetime.now)
    color: str = "#4ade80"
    icon: str = "⏱"
    # Open block — one block per habit at a time
    open_block_id: Optional[str] = None
    open_block_task_ids: List[str] = field(default_factory=list)
    open_block_started_at: Optional[datetime] = None

    @staticmethod
    def create(name: str, description: str = "", goal_hours: float = 8.0,
              color: str = "#4ade80", icon: str = "⏱") -> "Habit":
        return Habit(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            goal_hours=goal_hours,
            color=color,
            icon=icon,
        )

    def start_block(self, block_id: str, task_ids: List[str]):
        self.open_block_id = block_id
        self.open_block_task_ids = task_ids
        self.open_block_started_at = datetime.now()

    def end_block(self):
        self.open_block_id = None
        self.open_block_task_ids = []
        self.open_block_started_at = None

    def progress(self, hours_worked: float) -> float:
        return min(hours_worked / self.goal_hours, 1.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal_hours": self.goal_hours,
            "created_at": self.created_at.isoformat(),
            "color": self.color,
            "icon": self.icon,
            "open_block_id": self.open_block_id,
            "open_block_task_ids": self.open_block_task_ids,
            "open_block_started_at":
                self.open_block_started_at.isoformat() if self.open_block_started_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Habit":
        started_at = None
        if d.get("open_block_started_at"):
            try:
                started_at = datetime.fromisoformat(d["open_block_started_at"])
            except (ValueError, TypeError):
                started_at = None
        # Handle migration from old single task_id field
        task_ids = d.get("open_block_task_ids")
        if task_ids is None:
            old_id = d.get("open_block_task_id", "")
            task_ids = [old_id] if old_id else []
        return cls(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            goal_hours=d.get("goal_hours", 8.0),
            created_at=datetime.fromisoformat(d.get("created_at", datetime.now().isoformat())),
            color=d.get("color", "#4ade80"),
            icon=d.get("icon", "⏱"),
            open_block_id=d.get("open_block_id"),
            open_block_task_ids=task_ids,
            open_block_started_at=started_at,
        )
