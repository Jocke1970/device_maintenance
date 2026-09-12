"""Data models for Device Maintenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RuntimeState:
    """Persistent runtime state for one maintenance config entry."""

    total_runtime_seconds: float = 0.0
    baseline_runtime_seconds: float = 0.0
    last_action: str | None = None
    history_seconds: list[float] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "RuntimeState":
        """Create state from storage data."""
        raw = raw or {}
        history = raw.get("history_seconds", [])
        return cls(
            total_runtime_seconds=float(raw.get("total_runtime_seconds", 0.0) or 0.0),
            baseline_runtime_seconds=float(raw.get("baseline_runtime_seconds", 0.0) or 0.0),
            last_action=raw.get("last_action"),
            history_seconds=[float(value) for value in history if _is_number(value)],
        )

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable storage data."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MaintenanceSnapshot:
    """Calculated maintenance state exposed to entities."""

    elapsed_seconds: float
    expected_interval_seconds: float
    remaining_seconds: float
    progress_percent: float
    sample_count: int
    confidence: str
    source_available: bool = True


def _is_number(value: Any) -> bool:
    """Return whether a value can safely be converted to float."""
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
