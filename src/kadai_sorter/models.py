from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PlanStatus(StrEnum):
    READY = "ready"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    COPIED = "copied"
    ERROR = "error"


@dataclass(frozen=True)
class CourseRule:
    name: str
    aliases: tuple[str, ...]
    extensions: tuple[str, ...]


@dataclass(frozen=True)
class AppConfig:
    student_id: str
    courses: tuple[CourseRule, ...]


@dataclass(frozen=True)
class PlanItem:
    source: Path
    destination: Path | None
    course: str | None
    assignment: str | None
    status: PlanStatus
    reason: str
