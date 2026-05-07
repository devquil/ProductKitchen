from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


# Tag system with weights — business is highest priority
TASK_TAGS = {
    "business":   {"label": "💼 Business",  "weight": 3.0, "color": "#ef4444", "description": "Revenue-generating work — highest priority"},
    "fitness":    {"label": "💪 Fitness",   "weight": 1.5, "color": "#22c55e", "description": "Health & physical training"},
    "hobby":      {"label": "🎨 Hobby",    "weight": 1.0, "color": "#8b5cf6", "description": "Creative / leisure activities"},
    "personal":   {"label": "🏠 Personal", "weight": 1.2, "color": "#06b6d4", "description": "Life admin & personal projects"},
}


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    efficiency: float = 0.0
    tag: str = "personal"   # one of: business, fitness, hobby, personal
    habit_id: Optional[str] = None  # optional link to a habit tracker habit

    @staticmethod
    def create(title: str, description: str = "", priority: Priority = Priority.MEDIUM,
               due_date: Optional[datetime] = None, estimated_hours: float = 1.0,
               tag: str = "personal", habit_id: Optional[str] = None) -> "Task":
        return Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            estimated_hours=estimated_hours,
            tag=tag,
            habit_id=habit_id,
        )

    def tag_weight(self) -> float:
        return TASK_TAGS.get(self.tag, TASK_TAGS["personal"])["weight"]

    def start(self):
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, actual_hours: float):
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.actual_hours = actual_hours
        if actual_hours > 0:
            self.efficiency = min(self.estimated_hours / actual_hours, 2.0)
        else:
            self.efficiency = 0.0

    def hours_logged(self, hours: float):
        self.actual_hours = hours
        if self.status == TaskStatus.DONE and hours > 0:
            self.efficiency = min(self.estimated_hours / hours, 2.0)

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status != TaskStatus.DONE:
            return datetime.now() > self.due_date
        return False

    @property
    def days_until_due(self) -> Optional[int]:
        if self.due_date:
            delta = self.due_date - datetime.now()
            return delta.days
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "efficiency": self.efficiency,
            "tag": self.tag,
            "habit_id": self.habit_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d["id"],
            title=d["title"],
            description=d.get("description", ""),
            priority=Priority(d.get("priority", "medium")),
            status=TaskStatus(d.get("status", "pending")),
            due_date=datetime.fromisoformat(d["due_date"]) if d.get("due_date") else None,
            created_at=datetime.fromisoformat(d.get("created_at", datetime.now().isoformat())),
            started_at=datetime.fromisoformat(d["started_at"]) if d.get("started_at") else None,
            completed_at=datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None,
            estimated_hours=d.get("estimated_hours", 1.0),
            actual_hours=d.get("actual_hours", 0.0),
            efficiency=d.get("efficiency", 0.0),
            tag=d.get("tag", "personal"),
            habit_id=d.get("habit_id"),
        )
