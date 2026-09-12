"""Device Maintenance integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DATA_STORE, DOMAIN, PLATFORMS
from .manager import DeviceMaintenanceManager
from .store import DeviceMaintenanceStore


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up Device Maintenance."""
    store = DeviceMaintenanceStore(hass)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[DATA_STORE] = store
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Device Maintenance config entry."""
    store: DeviceMaintenanceStore = hass.data[DOMAIN][DATA_STORE]
    manager = DeviceMaintenanceManager(hass, entry, store)
    entry.runtime_data = manager

    await manager.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one Device Maintenance config entry."""
    manager: DeviceMaintenanceManager = entry.runtime_data
    await manager.async_stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        store: DeviceMaintenanceStore = hass.data[DOMAIN][DATA_STORE]
        await store.async_flush()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove persistent state when a tracker is deleted."""
    store: DeviceMaintenanceStore = hass.data[DOMAIN][DATA_STORE]
    await store.async_remove_entry(entry.entry_id)
