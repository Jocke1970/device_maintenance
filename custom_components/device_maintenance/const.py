"""Constants for Device Maintenance."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "device_maintenance"
NAME = "Device Maintenance"
VERSION = "0.1.0-dev.1"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

DATA_STORE = "store"
STORAGE_KEY = f"{DOMAIN}.runtime"
STORAGE_VERSION = 1
STORAGE_SAVE_DELAY = 5.0

STRATEGY_ELAPSED = "elapsed"
STRATEGY_SESSION_RUNTIME = "session_runtime"
STRATEGIES = [STRATEGY_ELAPSED, STRATEGY_SESSION_RUNTIME]

CONF_NAME = "name"
CONF_STRATEGY = "strategy"
CONF_SOURCE_ENTITY = "source_entity"
CONF_BATTERY_ENTITY = "battery_entity"
CONF_ACTION_LABEL = "action_label"
CONF_FALLBACK_INTERVAL_SECONDS = "fallback_interval_seconds"
CONF_HISTORY_SIZE = "history_size"
CONF_MAX_SESSION_SECONDS = "max_session_seconds"
CONF_PICTURE_KEY = "picture_key"

DEFAULT_ACTION_LABEL = "Laddad"
DEFAULT_HISTORY_SIZE = 5
DEFAULT_MAX_SESSION_SECONDS = 1200
DEFAULT_RUNTIME_FALLBACK_SECONDS = 90 * 60
DEFAULT_ELAPSED_FALLBACK_SECONDS = 7 * 24 * 60 * 60
MIN_SAMPLE_SECONDS = 60
