"""Constants for Device Maintenance."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "device_maintenance"
NAME = "Device Maintenance"
VERSION = "0.1.0-dev.10"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

DATA_STORE = "store"
STORAGE_KEY = f"{DOMAIN}.runtime"
STORAGE_VERSION = 1
STORAGE_SAVE_DELAY = 5.0

STRATEGY_ELAPSED = "elapsed"
STRATEGY_SESSION_RUNTIME = "session_runtime"
STRATEGIES = [STRATEGY_ELAPSED, STRATEGY_SESSION_RUNTIME]

ITEM_TYPE_BUILT_IN_BATTERY = "built_in_battery"
ITEM_TYPE_REPLACEABLE_BATTERY = "replaceable_battery"
ITEM_TYPE_FILTER = "filter"
ITEM_TYPE_CARTRIDGE = "cartridge"
ITEM_TYPE_BLADE = "blade"
ITEM_TYPE_CO2_CYLINDER = "co2_cylinder"
ITEM_TYPE_OTHER = "other"
MAINTENANCE_ITEM_TYPES = [
    ITEM_TYPE_BUILT_IN_BATTERY,
    ITEM_TYPE_REPLACEABLE_BATTERY,
    ITEM_TYPE_FILTER,
    ITEM_TYPE_CARTRIDGE,
    ITEM_TYPE_BLADE,
    ITEM_TYPE_CO2_CYLINDER,
    ITEM_TYPE_OTHER,
]

INITIAL_ACTION_NOW = "now"
INITIAL_ACTION_CUSTOM = "custom"
INITIAL_ACTION_MODES = [INITIAL_ACTION_NOW, INITIAL_ACTION_CUSTOM]

CONF_NAME = "name"
CONF_STRATEGY = "strategy"
CONF_SOURCE_ENTITY = "source_entity"
CONF_BATTERY_ENTITY = "battery_entity"
CONF_LINKED_ENTITY = "linked_entity"
CONF_UI_GROUP = "ui_group"
CONF_ACTION_LABEL = "action_label"
CONF_FALLBACK_INTERVAL_SECONDS = "fallback_interval_seconds"
CONF_HISTORY_SIZE = "history_size"
CONF_MAX_SESSION_SECONDS = "max_session_seconds"
CONF_PICTURE_KEY = "picture_key"
CONF_LEGACY_ENTITY = "legacy_entity"
CONF_MIGRATION_SEED = "migration_seed"
CONF_MAINTENANCE_ITEM_TYPE = "maintenance_item_type"
CONF_MAINTENANCE_ITEM_QUANTITY = "maintenance_item_quantity"
CONF_MAINTENANCE_ITEM_SPECIFICATION = "maintenance_item_specification"
CONF_INITIAL_ACTION_MODE = "initial_action_mode"
CONF_INITIAL_ACTION_DATETIME = "initial_action_datetime"

DEFAULT_ACTION_LABEL = "Laddad"
DEFAULT_HISTORY_SIZE = 5
DEFAULT_MAX_SESSION_SECONDS = 1200
DEFAULT_RUNTIME_FALLBACK_SECONDS = 90 * 60
DEFAULT_ELAPSED_FALLBACK_SECONDS = 7 * 24 * 60 * 60
DEFAULT_MAINTENANCE_ITEM_TYPE = ITEM_TYPE_OTHER
DEFAULT_MAINTENANCE_ITEM_QUANTITY = 1
MIN_SAMPLE_SECONDS = 60

ACTION_LABEL_BY_ITEM_TYPE = {
    ITEM_TYPE_BUILT_IN_BATTERY: "Laddad",
    ITEM_TYPE_REPLACEABLE_BATTERY: "Batteri bytt",
    ITEM_TYPE_FILTER: "Filter bytt",
    ITEM_TYPE_CARTRIDGE: "Patron bytt",
    ITEM_TYPE_BLADE: "Blad bytt",
    ITEM_TYPE_CO2_CYLINDER: "CO₂-patron bytt",
    ITEM_TYPE_OTHER: "Underhåll utfört",
}

ACTION_ICON_BY_ITEM_TYPE = {
    ITEM_TYPE_BUILT_IN_BATTERY: "mdi:battery-check",
    ITEM_TYPE_REPLACEABLE_BATTERY: "mdi:battery-sync",
    ITEM_TYPE_FILTER: "mdi:air-filter",
    ITEM_TYPE_CARTRIDGE: "mdi:swap-horizontal-bold",
    ITEM_TYPE_BLADE: "mdi:razor-double-edge",
    ITEM_TYPE_CO2_CYLINDER: "mdi:gas-cylinder",
    ITEM_TYPE_OTHER: "mdi:check-circle-outline",
}
