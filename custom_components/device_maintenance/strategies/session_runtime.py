"""Session-runtime strategy for Device Maintenance."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_MAX_SESSION_SECONDS,
    CONF_SOURCE_ENTITY,
    DEFAULT_MAX_SESSION_SECONDS,
)
from ..models import MaintenanceSnapshot, RuntimeState
from .base import MaintenanceStrategy, StateChangedCallback


class SessionRuntimeStrategy(MaintenanceStrategy):
    """Accumulate positive deltas from a per-session runtime sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        state: RuntimeState,
        async_state_changed: StateChangedCallback,
    ) -> None:
        """Initialize the strategy."""
        super().__init__(hass, entry, state, async_state_changed)
        self._remove_listener = None

    @property
    def source_entity_id(self) -> str | None:
        """Return the session timer source entity."""
        return self.entry.data.get(CONF_SOURCE_ENTITY)

    @property
    def max_session_seconds(self) -> float:
        """Return maximum accepted delta for one state transition."""
        return max(
            1.0,
            float(
                self.options.get(CONF_MAX_SESSION_SECONDS, DEFAULT_MAX_SESSION_SECONDS)
                or DEFAULT_MAX_SESSION_SECONDS
            ),
        )

    async def async_start(self) -> None:
        """Start listening for session timer changes."""
        source = self.source_entity_id
        if source:
            self._remove_listener = async_track_state_change_event(
                self.hass,
                [source],
                self._async_source_changed,
            )

    async def async_stop(self) -> None:
        """Stop listening for session timer changes."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source state changes without counting startup restores."""
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        old_value = _state_seconds(old_state)
        new_value = _state_seconds(new_state)

        # A transition from unknown/unavailable to a numeric value is only a
        # source restore. It must never be booked as new runtime.
        if new_value is None or old_value is None:
            self.hass.async_create_task(self._async_state_changed())
            return

        delta = new_value - old_value if new_value >= old_value else new_value
        if 0 < delta <= self.max_session_seconds:
            self.state.total_runtime_seconds += delta

        self.hass.async_create_task(self._async_state_changed())

    async def async_register_action(self) -> None:
        """Register a charge/service action and reset the runtime baseline."""
        elapsed = max(
            0.0,
            self.state.total_runtime_seconds - self.state.baseline_runtime_seconds,
        )
        self._append_sample(elapsed)
        self.state.baseline_runtime_seconds = self.state.total_runtime_seconds
        self.state.last_action = dt_util.utcnow().isoformat()
        await self._async_state_changed()

    def snapshot(self) -> MaintenanceSnapshot:
        """Return current runtime state."""
        elapsed = max(
            0.0,
            self.state.total_runtime_seconds - self.state.baseline_runtime_seconds,
        )
        expected = self.expected_interval_seconds
        remaining = expected - elapsed
        progress = (elapsed / expected) * 100 if expected > 0 else 0.0
        source = self.source_entity_id
        source_state = self.hass.states.get(source) if source else None
        source_available = bool(
            source_state
            and source_state.state not in {"unknown", "unavailable"}
        )
        return MaintenanceSnapshot(
            elapsed_seconds=elapsed,
            expected_interval_seconds=expected,
            remaining_seconds=remaining,
            progress_percent=progress,
            sample_count=self.sample_count,
            confidence=self.confidence,
            source_available=source_available,
        )


def _state_seconds(state) -> float | None:
    """Return a valid numeric source state in seconds."""
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    if value < 0 or value > 3600:
        return None
    return value
