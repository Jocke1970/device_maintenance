"""Legacy migration helpers for Device Maintenance."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LEGACY_ENTITY,
    CONF_NAME,
    DEFAULT_ACTION_LABEL,
    DEFAULT_ELAPSED_FALLBACK_SECONDS,
    DEFAULT_HISTORY_SIZE,
    DOMAIN,
)
from .models import RuntimeState

LEGACY_SENSOR_PREFIX = "sensor.device_maintenance_"


@dataclass(frozen=True, slots=True)
class LegacyElapsedCandidate:
    """One legacy elapsed-time tracker that can be imported safely."""

    entity_id: str
    name: str
    datetime_entity: str
    history_entity: str
    battery_entity: str | None
    action_label: str
    fallback_interval_seconds: float
    runtime_state: RuntimeState
    warnings: tuple[str, ...] = ()

    @property
    def history_size(self) -> int:
        """Return a suitable history size for the imported tracker."""
        return min(20, max(DEFAULT_HISTORY_SIZE, len(self.runtime_state.history_seconds)))

    @property
    def warning_text(self) -> str:
        """Return warnings formatted for config-flow preview."""
        return "; ".join(self.warnings) if self.warnings else "None"


def discover_legacy_elapsed_candidates(
    hass: HomeAssistant,
) -> list[LegacyElapsedCandidate]:
    """Discover legacy elapsed-time Device Maintenance template sensors."""
    configured_names = {
        str(entry.data.get(CONF_NAME, entry.title)).casefold()
        for entry in hass.config_entries.async_entries(DOMAIN)
    }
    configured_legacy_entities = {
        str(entry.data[CONF_LEGACY_ENTITY])
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.data.get(CONF_LEGACY_ENTITY)
    }

    candidates: list[LegacyElapsedCandidate] = []
    for state in hass.states.async_all():
        if not state.entity_id.startswith(LEGACY_SENSOR_PREFIX):
            continue
        if state.attributes.get("backend") == DOMAIN:
            continue

        datetime_entity = _string_attr(state, "datetime_entity")
        history_entity = _string_attr(state, "history_entity")
        if not datetime_entity or not history_entity:
            continue

        name = _display_name(state)
        if name.casefold() in configured_names:
            continue
        if state.entity_id in configured_legacy_entities:
            continue

        warnings: list[str] = []
        last_action = _last_action(hass, datetime_entity, warnings)
        history_seconds = _history_seconds(hass, history_entity, warnings)
        fallback_seconds = _fallback_seconds(state, warnings)

        battery_entity = _string_attr(state, "battery_entity")
        action_label = _string_attr(state, "action_label") or DEFAULT_ACTION_LABEL

        candidates.append(
            LegacyElapsedCandidate(
                entity_id=state.entity_id,
                name=name,
                datetime_entity=datetime_entity,
                history_entity=history_entity,
                battery_entity=battery_entity,
                action_label=action_label,
                fallback_interval_seconds=fallback_seconds,
                runtime_state=RuntimeState(
                    last_action=last_action,
                    history_seconds=history_seconds,
                ),
                warnings=tuple(warnings),
            )
        )

    return sorted(candidates, key=lambda item: item.name.casefold())


def _display_name(state: State) -> str:
    """Return a clean tracker display name."""
    configured = _string_attr(state, "display_name")
    if configured:
        return configured
    name = state.name
    for prefix in ("Underhåll - ", "Maintenance - "):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return name


def _string_attr(state: State, key: str) -> str | None:
    """Return a non-empty string attribute."""
    value = state.attributes.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _last_action(
    hass: HomeAssistant,
    entity_id: str,
    warnings: list[str],
) -> str | None:
    """Read and normalize a legacy input_datetime value."""
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        warnings.append(f"No valid last-action value in {entity_id}")
        return None

    timestamp = state.attributes.get("timestamp")
    if _is_number(timestamp):
        return dt_util.utc_from_timestamp(float(timestamp)).isoformat()

    parsed = dt_util.parse_datetime(state.state)
    if parsed is None:
        warnings.append(f"Could not parse last-action value from {entity_id}")
        return None

    if parsed.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone)
        if timezone is not None:
            parsed = parsed.replace(tzinfo=timezone)
    if parsed.tzinfo is None:
        warnings.append(f"Could not determine timezone for {entity_id}")
        return parsed.isoformat()
    return dt_util.as_utc(parsed).isoformat()


def _history_seconds(
    hass: HomeAssistant,
    entity_id: str,
    warnings: list[str],
) -> list[float]:
    """Read legacy elapsed history, stored as days, and convert to seconds."""
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return []

    try:
        raw: Any = json.loads(state.state)
    except (TypeError, ValueError, json.JSONDecodeError):
        warnings.append(f"Could not parse history from {entity_id}")
        return []

    if not isinstance(raw, list):
        warnings.append(f"History in {entity_id} is not a list")
        return []

    history: list[float] = []
    invalid_values = 0
    for value in raw:
        if not _is_number(value):
            invalid_values += 1
            continue
        days = float(value)
        if days <= 0:
            invalid_values += 1
            continue
        history.append(days * 86400.0)

    if invalid_values:
        warnings.append(f"Ignored {invalid_values} invalid history value(s)")
    return history


def _fallback_seconds(state: State, warnings: list[str]) -> float:
    """Read legacy fallback interval in days."""
    value = state.attributes.get("fallback_interval_days")
    if not _is_number(value):
        warnings.append("Missing fallback interval; using 7 days")
        return float(DEFAULT_ELAPSED_FALLBACK_SECONDS)
    days = float(value)
    if days <= 0:
        warnings.append("Invalid fallback interval; using 7 days")
        return float(DEFAULT_ELAPSED_FALLBACK_SECONDS)
    return days * 86400.0


def _is_number(value: Any) -> bool:
    """Return whether a value can be converted to float."""
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
