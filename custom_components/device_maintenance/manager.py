"""Runtime manager for Device Maintenance."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ACTION_LABEL,
    CONF_BATTERY_ENTITY,
    CONF_NAME,
    CONF_PICTURE_KEY,
    DEFAULT_ACTION_LABEL,
)
from .models import MaintenanceSnapshot, RuntimeState
from .store import DeviceMaintenanceStore
from .strategies import create_strategy


class DeviceMaintenanceManager:
    """Own one configured maintenance tracker."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        store: DeviceMaintenanceStore,
    ) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self.store = store
        self.state: RuntimeState = store.state_for(entry.entry_id)
        self._listeners: set[Callable[[], None]] = set()
        self._remove_battery_listener = None
        self.strategy = create_strategy(
            hass,
            entry,
            self.state,
            self._async_state_changed,
        )

    @property
    def name(self) -> str:
        """Return configured display name."""
        return str(self.entry.data.get(CONF_NAME, self.entry.title))

    @property
    def action_label(self) -> str:
        """Return configured action label."""
        return str(self.entry.options.get(CONF_ACTION_LABEL, DEFAULT_ACTION_LABEL))

    @property
    def picture_key(self) -> str:
        """Return optional frontend picture key."""
        return str(self.entry.options.get(CONF_PICTURE_KEY, ""))

    @property
    def battery_entity_id(self) -> str | None:
        """Return optional battery entity."""
        return self.entry.options.get(CONF_BATTERY_ENTITY)

    @property
    def source_entity_id(self) -> str | None:
        """Return strategy source entity."""
        return self.strategy.source_entity_id

    @property
    def linked_entity_id(self) -> str | None:
        """Return entity whose device helper entities should link to."""
        return self.source_entity_id or self.battery_entity_id

    @property
    def battery_percent(self) -> float | None:
        """Return current battery percent when available."""
        entity_id = self.battery_entity_id
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable"}:
            return None
        try:
            return max(0.0, min(100.0, float(state.state)))
        except (TypeError, ValueError):
            return None

    @property
    def snapshot(self) -> MaintenanceSnapshot:
        """Return the current calculated maintenance state."""
        return self.strategy.snapshot()

    async def async_start(self) -> None:
        """Start strategy and auxiliary listeners."""
        await self.strategy.async_start()
        if self.battery_entity_id:
            self._remove_battery_listener = async_track_state_change_event(
                self.hass,
                [self.battery_entity_id],
                self._async_auxiliary_state_changed,
            )

    async def async_stop(self) -> None:
        """Stop all listeners."""
        await self.strategy.async_stop()
        if self._remove_battery_listener is not None:
            self._remove_battery_listener()
            self._remove_battery_listener = None

    async def async_register_action(self) -> None:
        """Register the configured maintenance action."""
        await self.strategy.async_register_action()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.add(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    async def _async_state_changed(self, persist: bool = True) -> None:
        """Persist state when needed and notify entities."""
        if persist:
            self.store.async_schedule_save(self.entry.entry_id, self.state)
        for listener in tuple(self._listeners):
            listener()

    @callback
    def _async_auxiliary_state_changed(self, _event) -> None:
        """Notify entities after battery/source metadata changes."""
        for listener in tuple(self._listeners):
            listener()
