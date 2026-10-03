"""Number platform for Device Maintenance."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .const import BATTERY_MODE_MANUAL
from .manager import DeviceMaintenanceManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up optional mutable Device Maintenance numbers."""
    manager: DeviceMaintenanceManager = entry.runtime_data
    entities: list[NumberEntity] = []
    if manager.battery_mode == BATTERY_MODE_MANUAL:
        entities.append(DeviceMaintenanceManualBatteryNumber(hass, manager))
    if manager.usage_enabled:
        entities.append(DeviceMaintenanceUsageCountNumber(hass, manager))
    async_add_entities(entities)


class _DeviceMaintenanceNumber(NumberEntity):
    """Shared number entity plumbing."""

    _attr_has_entity_name = False
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        self.manager = manager
        linked_entity = manager.linked_entity_id
        if linked_entity:
            self.device_entry = async_entity_id_to_device(hass, linked_entity)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self._async_manager_updated))

    @callback
    def _async_manager_updated(self) -> None:
        self.async_write_ha_state()


class DeviceMaintenanceManualBatteryNumber(_DeviceMaintenanceNumber):
    """Manually entered battery percentage."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:battery-edit"

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        super().__init__(hass, manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_manual_battery_percent"
        self._attr_name = f"{manager.name} - Manuell batterinivå"
        self._attr_suggested_object_id = (
            f"device_maintenance_{slugify(manager.name)}_manual_battery"
        )

    @property
    def native_value(self) -> float | None:
        return self.manager.state.manual_battery_percent

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "backend": "device_maintenance_auxiliary",
            "entry_id": self.manager.entry.entry_id,
            "number_role": "manual_battery_percent",
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.manager.async_set_manual_battery_percent(value)


class DeviceMaintenanceUsageCountNumber(_DeviceMaintenanceNumber):
    """Editable current-cycle usage count."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100000
    _attr_native_step = 1
    _attr_icon = "mdi:counter"

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        super().__init__(hass, manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_usage_count"
        self._attr_name = f"{manager.name} - Antal användningar"
        self._attr_suggested_object_id = (
            f"device_maintenance_{slugify(manager.name)}_usage_count"
        )

    @property
    def native_value(self) -> float:
        return float(self.manager.state.usage_count)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "backend": "device_maintenance_auxiliary",
            "entry_id": self.manager.entry.entry_id,
            "number_role": "usage_count",
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.manager.async_set_usage_count(value)
