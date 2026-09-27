"""Button platform for Device Maintenance."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .manager import DeviceMaintenanceManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Device Maintenance buttons."""
    manager: DeviceMaintenanceManager = entry.runtime_data
    entities: list[ButtonEntity] = [DeviceMaintenanceActionButton(hass, manager)]
    if manager.usage_enabled:
        entities.append(DeviceMaintenanceUsageButton(hass, manager))
    async_add_entities(entities)


class DeviceMaintenanceActionButton(ButtonEntity):
    """Register a maintenance action for one tracker."""

    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        """Initialize the action button."""
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_action"
        self._attr_name = f"{manager.name} - {manager.action_label}"
        self._attr_suggested_object_id = (
            f"device_maintenance_{slugify(manager.name)}_action"
        )
        self._attr_icon = manager.action_icon
        linked_entity = manager.linked_entity_id
        if linked_entity:
            self.device_entry = async_entity_id_to_device(hass, linked_entity)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose stable metadata for frontend consumers."""
        return {
            "backend": "device_maintenance",
            "entry_id": self.manager.entry.entry_id,
            "display_name": self.manager.name,
            "button_role": "maintenance_action",
            "action_label": self.manager.action_label,
            "action_icon": self.manager.action_icon,
            "maintenance_item_type": self.manager.maintenance_item_type,
            "maintenance_item_summary": self.manager.maintenance_item_summary,
        }

    async def async_press(self) -> None:
        """Register the configured action."""
        await self.manager.async_register_action()


class DeviceMaintenanceUsageButton(ButtonEntity):
    """Increment manual usage count by one."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:counter"

    def __init__(self, hass: HomeAssistant, manager: DeviceMaintenanceManager) -> None:
        """Initialize the usage button."""
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_usage_increment"
        self._attr_name = f"{manager.name} - +1 användning"
        self._attr_suggested_object_id = (
            f"device_maintenance_{slugify(manager.name)}_usage_increment"
        )
        linked_entity = manager.linked_entity_id
        if linked_entity:
            self.device_entry = async_entity_id_to_device(hass, linked_entity)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose auxiliary metadata without colliding with card action discovery."""
        return {
            "backend": "device_maintenance_auxiliary",
            "entry_id": self.manager.entry.entry_id,
            "display_name": self.manager.name,
            "button_role": "usage_increment",
            "usage_count": self.manager.state.usage_count,
        }

    async def async_press(self) -> None:
        """Register one usage."""
        await self.manager.async_increment_usage()
