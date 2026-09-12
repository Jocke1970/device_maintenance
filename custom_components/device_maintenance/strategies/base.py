"""Base strategy for Device Maintenance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from statistics import fmean

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_FALLBACK_INTERVAL_SECONDS,
    CONF_HISTORY_SIZE,
    DEFAULT_HISTORY_SIZE,
    MIN_SAMPLE_SECONDS,
)
from ..models import MaintenanceSnapshot, RuntimeState

StateChangedCallback = Callable[..., Awaitable[None]]


class MaintenanceStrategy(ABC):
    """Base class for maintenance tracking strategies."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        state: RuntimeState,
        async_state_changed: StateChangedCallback,
    ) -> None:
        """Initialize the strategy."""
        self.hass = hass
        self.entry = entry
        self.state = state
        self._async_state_changed = async_state_changed

    @property
    def options(self) -> dict:
        """Return effective options."""
        return dict(self.entry.options)

    @property
    def fallback_interval_seconds(self) -> float:
        """Return configured fallback interval."""
        return max(
            1.0,
            float(self.options.get(CONF_FALLBACK_INTERVAL_SECONDS, 1.0) or 1.0),
        )

    @property
    def history_size(self) -> int:
        """Return maximum learned interval history length."""
        return max(
            1,
            int(self.options.get(CONF_HISTORY_SIZE, DEFAULT_HISTORY_SIZE) or DEFAULT_HISTORY_SIZE),
        )

    @property
    def sample_count(self) -> int:
        """Return number of learned interval samples."""
        return len(self.state.history_seconds)

    @property
    def expected_interval_seconds(self) -> float:
        """Return learned interval or configured fallback."""
        if self.sample_count >= 2:
            return max(1.0, fmean(self.state.history_seconds))
        return self.fallback_interval_seconds

    @property
    def confidence(self) -> str:
        """Return human-readable learning confidence."""
        count = self.sample_count
        if count < 2:
            return "Startintervall"
        if count < 4:
            return "Preliminärt snitt"
        return "Inlärt snitt"

    def _append_sample(self, seconds: float) -> bool:
        """Append a valid maintenance interval sample."""
        if seconds < MIN_SAMPLE_SECONDS:
            return False
        self.state.history_seconds = [
            *self.state.history_seconds,
            float(seconds),
        ][-self.history_size :]
        return True

    @abstractmethod
    async def async_start(self) -> None:
        """Start tracking."""

    @abstractmethod
    async def async_stop(self) -> None:
        """Stop tracking."""

    @abstractmethod
    async def async_register_action(self) -> None:
        """Register a maintenance action."""

    @abstractmethod
    def snapshot(self) -> MaintenanceSnapshot:
        """Return current calculated state."""

    @property
    def source_entity_id(self) -> str | None:
        """Return the primary source entity, if any."""
        return None
