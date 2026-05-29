"""Aggregation of Intempus work_report stream entries into a per-project report.

Each raw entry from /web/v1/work_report/create_stream/ looks like:
  {
    "case__name":      "Backend API",
    "case__number":    "P-001",
    "amount":          "7.50",
    "unit":            "Timer",
    "work_type__name": "Produktiv, fakturerbar",
    "start_date":      "2026-05-14"
  }

Entries are grouped by case__name and amounts summed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import BonusConfig


@dataclass
class ProjectEntry:
    name: str
    hours: float
    bonus: bool = False  # True if this project counts towards bonus


@dataclass
class Report:
    year: int
    month: int
    entries: list[ProjectEntry] = field(default_factory=list)
    bonus_cfg: BonusConfig | None = None

    @property
    def total_hours(self) -> float:
        return sum(e.hours for e in self.entries)

    @property
    def bonus_hours(self) -> float | None:
        if self.bonus_cfg is None:
            return None
        return sum(e.hours for e in self.entries if e.bonus)

    @property
    def bonus_eligible_hours(self) -> float | None:
        """Hours above the threshold that actually earn a bonus."""
        if self.bonus_cfg is None or self.bonus_hours is None:
            return None
        return max(0.0, self.bonus_hours - self.bonus_cfg.min_hours)

    @property
    def bonus_amount(self) -> float | None:
        if self.bonus_cfg is None or self.bonus_eligible_hours is None:
            return None
        return self.bonus_eligible_hours * (self.bonus_cfg.hourly_rate / 2)


def build_report(
    year: int,
    month: int,
    raw_entries: list[dict[str, Any]],
    *,
    bonus_cfg: BonusConfig | None = None,
    include_zero: bool = False,
) -> Report:
    """Aggregate raw stream entries into a Report grouped by case (project)."""
    totals: dict[str, float] = {}

    for item in raw_entries:
        name = str(item.get("case__name") or item.get("case__number") or "No project")
        amount = _to_float(item.get("amount", 0.0))
        totals[name] = totals.get(name, 0.0) + amount

    bonus_projects = set(bonus_cfg.projects) if bonus_cfg else set()

    entries = [
        ProjectEntry(name=name, hours=hours, bonus=name in bonus_projects)
        for name, hours in sorted(totals.items())
        if hours > 0 or include_zero
    ]
    return Report(year=year, month=month, entries=entries, bonus_cfg=bonus_cfg)


def _to_float(val: Any) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

