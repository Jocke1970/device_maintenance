"""Sensor platform for Device Maintenance."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .const import CONF_STRATEGY, STRATEGY_ELAPSED, STRATEGY_SESSION_RUNTIME
from .manager import DeviceMaintenanceManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Device Maintenance sensor."""
    manager: DeviceMaintenanceManager = entry.runtime_data
    async_add_entities([DeviceMaintenanceSensor(hass, manager)])


class DeviceMaintenanceSensor(SensorEntity):
    """Self-learning maintenance state sensor."""

    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        """Initialize the maintenance sensor."""
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_maintenance"
        self._attr_name = f"Underhåll - {manager.name}"
        self._attr_suggested_object_id = f"device_maintenance_{slugify(manager.name)}"
        linked_entity = manager.linked_entity_id
        if linked_entity:
            self.device_entry = async_entity_id_to_device(hass, linked_entity)

    async def async_added_to_hass(self) -> None:
        """Register runtime update listener."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self._async_manager_updated))

    @callback
    def _async_manager_updated(self) -> None:
        """Handle manager state changes."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return elapsed runtime in hours or elapsed age in days."""
        snapshot = self.manager.snapshot
        strategy = self.manager.entry.data.get(CONF_STRATEGY)
        if strategy == STRATEGY_SESSION_RUNTIME:
            return round(snapshot.elapsed_seconds / 3600, 3)
        return round(snapshot.elapsed_seconds / 86400, 2)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the sensor unit."""
        strategy = self.manager.entry.data.get(CONF_STRATEGY)
        return "h" if strategy == STRATEGY_SESSION_RUNTIME else "d"

    @property
    def extra_state_attributes(self) -> dict:
        """Return Device Maintenance metadata for UI consumers."""
        snapshot = self.manager.snapshot
        strategy = self.manager.entry.data.get(CONF_STRATEGY)
        battery = self.manager.battery_percent
        attrs = {
            "backend": "device_maintenance",
            "entry_id": self.manager.entry.entry_id,
            "display_name": self.manager.name,
            "strategy": strategy,
            "action_label": self.manager.action_label,
            "picture_key": self.manager.picture_key or slugify(self.manager.name),
            "battery_entity": self.manager.battery_entity_id,
            "battery_percent": round(battery) if battery is not None else None,
            "source_entity": self.manager.source_entity_id,
            "source_available": snapshot.source_available,
            "sample_count": snapshot.sample_count,
            "confidence": snapshot.confidence,
            "progress_percent": round(snapshot.progress_percent, 1),
            "last_action": self.manager.state.last_action,
        }
        if strategy == STRATEGY_SESSION_RUNTIME:
            attrs.update(
                {
                    "source_total_seconds": round(
                        self.manager.state.total_runtime_seconds,
                        1,
                    ),
                    "baseline_seconds": round(
                        self.manager.state.baseline_runtime_seconds,
                        1,
                    ),
                    "expected_interval_hours": round(
                        snapshot.expected_interval_seconds / 3600,
                        3,
                    ),
                    "hours_remaining": round(snapshot.remaining_seconds / 3600, 3),
                }
            )
        elif strategy == STRATEGY_ELAPSED:
            attrs.update(
                {
                    "expected_interval_days": round(
                        snapshot.expected_interval_seconds / 86400,
                        2,
                    ),
                    "days_remaining": round(snapshot.remaining_seconds / 86400, 2),
                }
            )
        return attrs
