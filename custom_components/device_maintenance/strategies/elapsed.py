"""Elapsed-time strategy for Device Maintenance."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from ..models import MaintenanceSnapshot, RuntimeState
from .base import MaintenanceStrategy, StateChangedCallback


class ElapsedStrategy(MaintenanceStrategy):
    """Track wall-clock time since the last maintenance action."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        state: RuntimeState,
        async_state_changed: StateChangedCallback,
    ) -> None:
        """Initialize the strategy."""
        super().__init__(hass, entry, state, async_state_changed)
        self._remove_timer = None

    async def async_start(self) -> None:
        """Start minute ticks and seed first action time if needed."""
        if self.state.last_action is None:
            self.state.last_action = dt_util.utcnow().isoformat()
            await self._async_state_changed()
        self._remove_timer = async_track_time_interval(
            self.hass,
            self._async_tick,
            timedelta(minutes=1),
        )

    async def async_stop(self) -> None:
        """Stop minute ticks."""
        if self._remove_timer is not None:
            self._remove_timer()
            self._remove_timer = None

    @callback
    def _async_tick(self, _now) -> None:
        """Notify entities that elapsed time changed."""
        self.hass.async_create_task(self._async_state_changed(persist=False))

    async def async_register_action(self) -> None:
        """Register a maintenance action."""
        elapsed = self._elapsed_seconds()
        self._append_sample(elapsed)
        self.state.last_action = dt_util.utcnow().isoformat()
        await self._async_state_changed()

    def snapshot(self) -> MaintenanceSnapshot:
        """Return current elapsed-time state."""
        elapsed = self._elapsed_seconds()
        expected = self.expected_interval_seconds
        remaining = expected - elapsed
        progress = (elapsed / expected) * 100 if expected > 0 else 0.0
        return MaintenanceSnapshot(
            elapsed_seconds=elapsed,
            expected_interval_seconds=expected,
            remaining_seconds=remaining,
            progress_percent=progress,
            sample_count=self.sample_count,
            confidence=self.confidence,
            source_available=True,
        )

    def _elapsed_seconds(self) -> float:
        """Return elapsed seconds since the last registered action."""
        if not self.state.last_action:
            return 0.0
        try:
            last_action = dt_util.parse_datetime(self.state.last_action)
        except (TypeError, ValueError):
            return 0.0
        if last_action is None:
            return 0.0
        now = dt_util.utcnow()
        if last_action.tzinfo is None:
            last_action = last_action.replace(tzinfo=now.tzinfo)
        return max(0.0, (now - last_action).total_seconds())
