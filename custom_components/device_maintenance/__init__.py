"""Device Maintenance integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_MIGRATION_SEED, DATA_STORE, DOMAIN, PLATFORMS
from .manager import DeviceMaintenanceManager
from .models import RuntimeState
from .store import DeviceMaintenanceStore

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up Device Maintenance."""
    store = DeviceMaintenanceStore(hass)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[DATA_STORE] = store
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Device Maintenance config entry."""
    store: DeviceMaintenanceStore = hass.data[DOMAIN][DATA_STORE]

    migration_seed = entry.data.get(CONF_MIGRATION_SEED)
    if migration_seed is not None:
        if not store.has_state(entry.entry_id):
            await store.async_import_state(
                entry.entry_id,
                RuntimeState.from_dict(migration_seed),
            )
        updated_data = dict(entry.data)
        updated_data.pop(CONF_MIGRATION_SEED, None)
        hass.config_entries.async_update_entry(entry, data=updated_data)

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
