from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
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
class Habit:
    id: str
    name: str
    description: str = ""
    goal_hours: float = 8.0
    created_at: datetime = field(default_factory=datetime.now)
    color: str = "#4ade80"
    icon: str = "⏱"

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
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Habit":
        return cls(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            goal_hours=d.get("goal_hours", 8.0),
            created_at=datetime.fromisoformat(d.get("created_at", datetime.now().isoformat())),
            color=d.get("color", "#4ade80"),
            icon=d.get("icon", "⏱"),
        )
