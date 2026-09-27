"""Runtime manager for Device Maintenance."""

from __future__ import annotations

from collections.abc import Callable
from statistics import fmean

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ACTION_ICON_BY_ITEM_TYPE,
    BATTERY_MODE_ENTITY,
    BATTERY_MODE_MANUAL,
    BATTERY_MODE_NONE,
    CONF_ACTION_LABEL,
    CONF_BATTERY_ENTITY,
    CONF_BATTERY_MODE,
    CONF_HISTORY_SIZE,
    CONF_LINKED_ENTITY,
    CONF_MAINTENANCE_ITEM_QUANTITY,
    CONF_MAINTENANCE_ITEM_SPECIFICATION,
    CONF_MAINTENANCE_ITEM_TYPE,
    CONF_NAME,
    CONF_PICTURE_KEY,
    CONF_UI_GROUP,
    CONF_USAGE_MODE,
    DEFAULT_ACTION_LABEL,
    DEFAULT_BATTERY_MODE,
    DEFAULT_HISTORY_SIZE,
    DEFAULT_MAINTENANCE_ITEM_QUANTITY,
    DEFAULT_MAINTENANCE_ITEM_TYPE,
    DEFAULT_USAGE_MODE,
    ITEM_TYPE_BLADE,
    ITEM_TYPE_BUILT_IN_BATTERY,
    ITEM_TYPE_CARTRIDGE,
    ITEM_TYPE_CO2_CYLINDER,
    ITEM_TYPE_FILTER,
    ITEM_TYPE_REPLACEABLE_BATTERY,
    USAGE_MODE_NONE,
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
    def action_icon(self) -> str:
        """Return an icon matching the configured maintenance item."""
        return ACTION_ICON_BY_ITEM_TYPE.get(
            self.maintenance_item_type,
            ACTION_ICON_BY_ITEM_TYPE[DEFAULT_MAINTENANCE_ITEM_TYPE],
        )

    @property
    def picture_key(self) -> str:
        """Return optional frontend picture key."""
        return str(self.entry.options.get(CONF_PICTURE_KEY, ""))

    @property
    def ui_group(self) -> str:
        """Return optional explicit frontend group key."""
        return str(self.entry.options.get(CONF_UI_GROUP, "") or "").strip()

    @property
    def battery_mode(self) -> str:
        """Return configured battery source mode with legacy inference."""
        configured = self.entry.options.get(CONF_BATTERY_MODE)
        if configured in {BATTERY_MODE_NONE, BATTERY_MODE_ENTITY, BATTERY_MODE_MANUAL}:
            return str(configured)
        if self.entry.options.get(CONF_BATTERY_ENTITY):
            return BATTERY_MODE_ENTITY
        return DEFAULT_BATTERY_MODE

    @property
    def usage_mode(self) -> str:
        """Return configured usage counter mode."""
        return str(self.entry.options.get(CONF_USAGE_MODE, DEFAULT_USAGE_MODE))

    @property
    def usage_enabled(self) -> bool:
        """Return whether usage counting is enabled."""
        return self.usage_mode != USAGE_MODE_NONE

    @property
    def battery_entity_id(self) -> str | None:
        """Return battery percentage entity when entity mode is active."""
        if self.battery_mode != BATTERY_MODE_ENTITY:
            return None
        return self.entry.options.get(CONF_BATTERY_ENTITY)

    @property
    def explicit_linked_entity_id(self) -> str | None:
        """Return optional entity explicitly selected for device linking."""
        return self.entry.options.get(CONF_LINKED_ENTITY)

    @property
    def maintenance_item_type(self) -> str:
        """Return the configured maintenance or replacement item type."""
        configured = self.entry.options.get(CONF_MAINTENANCE_ITEM_TYPE)
        if configured:
            return str(configured)
        return _infer_item_type_from_action(self.action_label)

    @property
    def maintenance_item_quantity(self) -> int:
        """Return the configured replacement-item quantity."""
        if self.maintenance_item_type == ITEM_TYPE_BUILT_IN_BATTERY:
            return 1
        try:
            return max(
                1,
                int(
                    self.entry.options.get(
                        CONF_MAINTENANCE_ITEM_QUANTITY,
                        DEFAULT_MAINTENANCE_ITEM_QUANTITY,
                    )
                ),
            )
        except (TypeError, ValueError):
            return DEFAULT_MAINTENANCE_ITEM_QUANTITY

    @property
    def maintenance_item_specification(self) -> str:
        """Return optional battery type, model, or item specification."""
        if self.maintenance_item_type == ITEM_TYPE_BUILT_IN_BATTERY:
            return ""
        return str(
            self.entry.options.get(CONF_MAINTENANCE_ITEM_SPECIFICATION, "") or ""
        ).strip()

    @property
    def maintenance_item_summary(self) -> str:
        """Return a compact language-neutral maintenance-item summary."""
        item_type = self.maintenance_item_type
        if item_type == ITEM_TYPE_BUILT_IN_BATTERY:
            return item_type

        specification = self.maintenance_item_specification
        quantity = self.maintenance_item_quantity
        if specification:
            return f"{quantity} × {specification}"
        return f"{quantity} × {item_type}"

    @property
    def legacy_battery_type(self) -> str | None:
        """Return old card-compatible battery_type metadata when relevant."""
        if self.maintenance_item_type != ITEM_TYPE_REPLACEABLE_BATTERY:
            return None
        specification = self.maintenance_item_specification
        if not specification:
            return None
        return f"{self.maintenance_item_quantity} × {specification}"

    @property
    def source_entity_id(self) -> str | None:
        """Return strategy source entity."""
        return self.strategy.source_entity_id

    @property
    def linked_entity_id(self) -> str | None:
        """Return entity whose device helper entities should link to."""
        return (
            self.explicit_linked_entity_id
            or self.source_entity_id
            or self.battery_entity_id
        )

    @property
    def battery_percent(self) -> float | None:
        """Return current battery percent from the configured source."""
        if self.battery_mode == BATTERY_MODE_MANUAL:
            return self.state.manual_battery_percent
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
    def usage_sample_count(self) -> int:
        """Return number of completed usage-count cycles."""
        return len(self.state.usage_history)

    @property
    def expected_usage_count(self) -> float | None:
        """Return learned usages per maintenance cycle once enough samples exist."""
        if self.usage_sample_count < 2:
            return None
        return float(fmean(self.state.usage_history))

    @property
    def usages_remaining(self) -> float | None:
        """Return learned remaining usages in the current cycle."""
        expected = self.expected_usage_count
        if expected is None:
            return None
        return expected - self.state.usage_count

    @property
    def usage_confidence(self) -> str:
        """Return confidence label for usage-count learning."""
        count = self.usage_sample_count
        if count < 2:
            return "Samlar historik"
        if count < 4:
            return "Preliminärt snitt"
        return "Inlärt snitt"

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
        """Register maintenance action and close the current usage cycle."""
        old_count = self.state.usage_count
        old_history = list(self.state.usage_history)
        if self.usage_enabled:
            self._archive_usage_cycle()
        try:
            await self.strategy.async_register_action()
        except Exception:
            self.state.usage_count = old_count
            self.state.usage_history = old_history
            raise

    async def async_increment_usage(self) -> None:
        """Register one usage."""
        if not self.usage_enabled:
            return
        self.state.usage_count += 1
        await self._async_state_changed()

    async def async_set_usage_count(self, value: float) -> None:
        """Correct the current usage count."""
        if not self.usage_enabled:
            return
        self.state.usage_count = max(0, int(round(value)))
        await self._async_state_changed()

    async def async_set_manual_battery_percent(self, value: float) -> None:
        """Set manually observed battery percentage."""
        if self.battery_mode != BATTERY_MODE_MANUAL:
            return
        self.state.manual_battery_percent = max(0.0, min(100.0, float(value)))
        await self._async_state_changed()

    def _archive_usage_cycle(self) -> None:
        """Append the current non-zero usage cycle and reset its counter."""
        count = max(0, int(self.state.usage_count))
        if count > 0:
            self.state.usage_history.append(count)
            history_size = max(
                2,
                int(self.entry.options.get(CONF_HISTORY_SIZE, DEFAULT_HISTORY_SIZE)),
            )
            self.state.usage_history = self.state.usage_history[-history_size:]
        self.state.usage_count = 0

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


def _infer_item_type_from_action(action_label: str) -> str:
    """Infer metadata for entries created before maintenance-item fields existed."""
    normalized = action_label.casefold()
    if "blad" in normalized or "blade" in normalized:
        return ITEM_TYPE_BLADE
    if "kolsyre" in normalized or "co2" in normalized or "co₂" in normalized:
        return ITEM_TYPE_CO2_CYLINDER
    if "filter" in normalized:
        return ITEM_TYPE_FILTER
    if "patron" in normalized or "refill" in normalized:
        return ITEM_TYPE_CARTRIDGE
    if "batteri" in normalized or "battery" in normalized:
        return ITEM_TYPE_REPLACEABLE_BATTERY
    if "ladd" in normalized or "charg" in normalized:
        return ITEM_TYPE_BUILT_IN_BATTERY
    return DEFAULT_MAINTENANCE_ITEM_TYPE
