"""Persistent state storage for Device Maintenance."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_SAVE_DELAY, STORAGE_VERSION
from .models import RuntimeState


class DeviceMaintenanceStore:
    """Shared Store wrapper for all Device Maintenance entries."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the store."""
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load persistent state."""
        self._data = await self._store.async_load() or {}

    def state_for(self, entry_id: str) -> RuntimeState:
        """Return the state for one config entry."""
        return RuntimeState.from_dict(self._data.get(entry_id))

    @callback
    def async_schedule_save(self, entry_id: str, state: RuntimeState) -> None:
        """Update one entry and coalesce disk writes."""
        self._data[entry_id] = state.as_dict()
        self._store.async_delay_save(lambda: self._data, STORAGE_SAVE_DELAY)

    async def async_remove_entry(self, entry_id: str) -> None:
        """Remove persistent state for one config entry."""
        if self._data.pop(entry_id, None) is not None:
            await self._store.async_save(self._data)

    async def async_flush(self) -> None:
        """Flush the current in-memory state to disk."""
        await self._store.async_save(self._data)
