"""Tracking strategies for Device Maintenance."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..const import CONF_STRATEGY, STRATEGY_ELAPSED, STRATEGY_SESSION_RUNTIME
from ..models import RuntimeState
from .base import MaintenanceStrategy, StateChangedCallback
from .elapsed import ElapsedStrategy
from .session_runtime import SessionRuntimeStrategy


def create_strategy(
    hass: HomeAssistant,
    entry: ConfigEntry,
    state: RuntimeState,
    async_state_changed: StateChangedCallback,
) -> MaintenanceStrategy:
    """Create the configured tracking strategy."""
    strategy = entry.data.get(CONF_STRATEGY)
    if strategy == STRATEGY_ELAPSED:
        return ElapsedStrategy(hass, entry, state, async_state_changed)
    if strategy == STRATEGY_SESSION_RUNTIME:
        return SessionRuntimeStrategy(hass, entry, state, async_state_changed)
    raise ValueError(f"Unsupported Device Maintenance strategy: {strategy}")
