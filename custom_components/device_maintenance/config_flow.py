"""Config flow for Device Maintenance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    DateTimeSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    ACTION_LABEL_BY_ITEM_TYPE,
    CONF_ACTION_LABEL,
    CONF_BATTERY_ENTITY,
    CONF_FALLBACK_INTERVAL_SECONDS,
    CONF_HISTORY_SIZE,
    CONF_INITIAL_ACTION_DATETIME,
    CONF_INITIAL_ACTION_MODE,
    CONF_LEGACY_ENTITY,
    CONF_LINKED_ENTITY,
    CONF_MAINTENANCE_ITEM_QUANTITY,
    CONF_MAINTENANCE_ITEM_SPECIFICATION,
    CONF_MAINTENANCE_ITEM_TYPE,
    CONF_MAX_SESSION_SECONDS,
    CONF_MIGRATION_SEED,
    CONF_NAME,
    CONF_PICTURE_KEY,
    CONF_SOURCE_ENTITY,
    CONF_STRATEGY,
    CONF_UI_GROUP,
    DEFAULT_ACTION_LABEL,
    DEFAULT_ELAPSED_FALLBACK_SECONDS,
    DEFAULT_HISTORY_SIZE,
    DEFAULT_MAINTENANCE_ITEM_QUANTITY,
    DEFAULT_MAINTENANCE_ITEM_TYPE,
    DEFAULT_MAX_SESSION_SECONDS,
    DEFAULT_RUNTIME_FALLBACK_SECONDS,
    DOMAIN,
    INITIAL_ACTION_CUSTOM,
    INITIAL_ACTION_MODES,
    INITIAL_ACTION_NOW,
    ITEM_TYPE_BUILT_IN_BATTERY,
    ITEM_TYPE_OTHER,
    ITEM_TYPE_REPLACEABLE_BATTERY,
    MAINTENANCE_ITEM_TYPES,
    STRATEGY_ELAPSED,
    STRATEGY_SESSION_RUNTIME,
)
from .migration import LegacyElapsedCandidate, discover_legacy_elapsed_candidates
from .models import RuntimeState


class DeviceMaintenanceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Device Maintenance config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._base: dict[str, Any] = {}
        self._legacy_candidate: LegacyElapsedCandidate | None = None
        self._pending_entry_data: dict[str, Any] = {}
        self._pending_entry_options: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose whether to create a tracker or import legacy state."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["create", "legacy_import"],
        )

    async def async_step_create(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose tracker name and strategy."""
        if user_input is not None:
            self._base = user_input
            return await self.async_step_maintenance_item()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(
                    CONF_STRATEGY,
                    default=STRATEGY_SESSION_RUNTIME,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[STRATEGY_SESSION_RUNTIME, STRATEGY_ELAPSED],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="strategy",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="create", data_schema=schema)

    async def async_step_maintenance_item(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose what is charged, replaced, or serviced."""
        if user_input is not None:
            self._base[CONF_MAINTENANCE_ITEM_TYPE] = user_input[
                CONF_MAINTENANCE_ITEM_TYPE
            ]
            self._base[CONF_LINKED_ENTITY] = user_input.get(CONF_LINKED_ENTITY)
            self._base[CONF_UI_GROUP] = _clean_optional_text(
                user_input.get(CONF_UI_GROUP)
            )
            if (
                self._base[CONF_MAINTENANCE_ITEM_TYPE]
                == ITEM_TYPE_BUILT_IN_BATTERY
            ):
                self._base[CONF_MAINTENANCE_ITEM_QUANTITY] = 1
                self._base[CONF_MAINTENANCE_ITEM_SPECIFICATION] = ""
                return await self._async_strategy_step()
            if (
                self._base[CONF_MAINTENANCE_ITEM_TYPE]
                == ITEM_TYPE_REPLACEABLE_BATTERY
            ):
                return await self.async_step_battery_details()
            return await self.async_step_item_details()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAINTENANCE_ITEM_TYPE,
                    default=ITEM_TYPE_BUILT_IN_BATTERY,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=MAINTENANCE_ITEM_TYPES,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="maintenance_item_type",
                    )
                ),
                vol.Optional(CONF_LINKED_ENTITY): EntitySelector(
                    EntitySelectorConfig()
                ),
                vol.Optional(CONF_UI_GROUP): TextSelector(),
            }
        )
        return self.async_show_form(step_id="maintenance_item", data_schema=schema)

    async def async_step_battery_details(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure a replaceable battery set."""
        if user_input is not None:
            self._base[CONF_MAINTENANCE_ITEM_QUANTITY] = int(
                user_input[CONF_MAINTENANCE_ITEM_QUANTITY]
            )
            self._base[CONF_MAINTENANCE_ITEM_SPECIFICATION] = str(
                user_input[CONF_MAINTENANCE_ITEM_SPECIFICATION]
            ).strip()
            return await self._async_strategy_step()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAINTENANCE_ITEM_QUANTITY,
                    default=DEFAULT_MAINTENANCE_ITEM_QUANTITY,
                ): _quantity_selector(),
                vol.Required(CONF_MAINTENANCE_ITEM_SPECIFICATION): TextSelector(),
            }
        )
        return self.async_show_form(step_id="battery_details", data_schema=schema)

    async def async_step_item_details(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure a replaceable filter, cartridge, blade, or other item."""
        if user_input is not None:
            self._base[CONF_MAINTENANCE_ITEM_QUANTITY] = int(
                user_input[CONF_MAINTENANCE_ITEM_QUANTITY]
            )
            self._base[CONF_MAINTENANCE_ITEM_SPECIFICATION] = str(
                user_input.get(CONF_MAINTENANCE_ITEM_SPECIFICATION, "") or ""
            ).strip()
            return await self._async_strategy_step()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAINTENANCE_ITEM_QUANTITY,
                    default=DEFAULT_MAINTENANCE_ITEM_QUANTITY,
                ): _quantity_selector(),
                vol.Optional(CONF_MAINTENANCE_ITEM_SPECIFICATION): TextSelector(),
            }
        )
        return self.async_show_form(step_id="item_details", data_schema=schema)

    async def _async_strategy_step(self) -> ConfigFlowResult:
        """Continue to the fields required by the selected tracking strategy."""
        if self._base[CONF_STRATEGY] == STRATEGY_SESSION_RUNTIME:
            return await self.async_step_session_runtime()
        return await self.async_step_elapsed()

    async def async_step_legacy_import(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose a compatible legacy elapsed-time tracker to import."""
        candidates = {
            item.entity_id: item
            for item in discover_legacy_elapsed_candidates(self.hass)
        }
        if not candidates:
            return self.async_abort(reason="no_legacy_trackers")

        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = candidates.get(str(user_input[CONF_LEGACY_ENTITY]))
            if candidate is None:
                errors["base"] = "legacy_tracker_unavailable"
            else:
                self._legacy_candidate = candidate
                return await self.async_step_legacy_preview()

        options = [
            {
                "value": candidate.entity_id,
                "label": f"{candidate.name} ({candidate.entity_id})",
            }
            for candidate in candidates.values()
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_LEGACY_ENTITY): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="legacy_import",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_legacy_preview(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Preview imported state before creating a tracker."""
        candidate = self._legacy_candidate
        if candidate is None:
            return self.async_abort(reason="legacy_tracker_unavailable")

        if user_input is not None:
            await self.async_set_unique_id(f"legacy:{candidate.entity_id}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_NAME: candidate.name,
                CONF_STRATEGY: STRATEGY_ELAPSED,
                CONF_LEGACY_ENTITY: candidate.entity_id,
                CONF_MIGRATION_SEED: candidate.runtime_state.as_dict(),
            }
            options = {
                CONF_BATTERY_ENTITY: candidate.battery_entity,
                CONF_LINKED_ENTITY: candidate.linked_entity,
                CONF_UI_GROUP: "",
                CONF_ACTION_LABEL: candidate.action_label,
                CONF_FALLBACK_INTERVAL_SECONDS: candidate.fallback_interval_seconds,
                CONF_HISTORY_SIZE: candidate.history_size,
                CONF_PICTURE_KEY: slugify(candidate.name),
                CONF_MAINTENANCE_ITEM_TYPE: candidate.maintenance_item_type,
                CONF_MAINTENANCE_ITEM_QUANTITY: candidate.maintenance_item_quantity,
                CONF_MAINTENANCE_ITEM_SPECIFICATION: (
                    candidate.maintenance_item_specification
                ),
            }
            return self.async_create_entry(
                title=candidate.name,
                data=data,
                options=options,
            )

        last_action = candidate.runtime_state.last_action or "—"
        fallback_days = candidate.fallback_interval_seconds / 86400.0
        item_summary = _item_summary(
            candidate.maintenance_item_type,
            candidate.maintenance_item_quantity,
            candidate.maintenance_item_specification,
            self.hass.config.language,
        )
        return self.async_show_form(
            step_id="legacy_preview",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": candidate.name,
                "entity": candidate.entity_id,
                "last_action": last_action,
                "samples": str(len(candidate.runtime_state.history_seconds)),
                "fallback_days": f"{fallback_days:.2f}",
                "item_summary": item_summary,
                "warnings": candidate.warning_text,
            },
        )

    async def async_step_session_runtime(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure a session-runtime tracker."""
        if user_input is not None:
            data = {
                CONF_NAME: self._base[CONF_NAME],
                CONF_STRATEGY: STRATEGY_SESSION_RUNTIME,
                CONF_SOURCE_ENTITY: user_input[CONF_SOURCE_ENTITY],
            }
            options = {
                **_item_options(self._base),
                CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                CONF_ACTION_LABEL: user_input[CONF_ACTION_LABEL],
                CONF_FALLBACK_INTERVAL_SECONDS: float(
                    user_input["fallback_minutes"]
                )
                * 60,
                CONF_HISTORY_SIZE: int(user_input[CONF_HISTORY_SIZE]),
                CONF_MAX_SESSION_SECONDS: int(
                    user_input[CONF_MAX_SESSION_SECONDS]
                ),
                CONF_PICTURE_KEY: slugify(self._base[CONF_NAME]),
            }
            return self.async_create_entry(
                title=self._base[CONF_NAME],
                data=data,
                options=options,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_BATTERY_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_ACTION_LABEL,
                    default=_action_default(self._base),
                ): TextSelector(),
                vol.Required(
                    "fallback_minutes",
                    default=DEFAULT_RUNTIME_FALLBACK_SECONDS // 60,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=100000,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
                vol.Required(
                    CONF_HISTORY_SIZE,
                    default=DEFAULT_HISTORY_SIZE,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=2,
                        max=20,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_MAX_SESSION_SECONDS,
                    default=DEFAULT_MAX_SESSION_SECONDS,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=3600,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="session_runtime", data_schema=schema)

    async def async_step_elapsed(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure a wall-clock tracker."""
        if user_input is not None:
            self._pending_entry_data = {
                CONF_NAME: self._base[CONF_NAME],
                CONF_STRATEGY: STRATEGY_ELAPSED,
            }
            self._pending_entry_options = {
                **_item_options(self._base),
                CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                CONF_ACTION_LABEL: user_input[CONF_ACTION_LABEL],
                CONF_FALLBACK_INTERVAL_SECONDS: float(
                    user_input["fallback_days"]
                )
                * 86400,
                CONF_HISTORY_SIZE: int(user_input[CONF_HISTORY_SIZE]),
                CONF_PICTURE_KEY: slugify(self._base[CONF_NAME]),
            }
            return await self.async_step_initial_action()

        schema = vol.Schema(
            {
                vol.Optional(CONF_BATTERY_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_ACTION_LABEL,
                    default=_action_default(self._base),
                ): TextSelector(),
                vol.Required(
                    "fallback_days",
                    default=DEFAULT_ELAPSED_FALLBACK_SECONDS // 86400,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.01,
                        max=3650,
                        step=0.01,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="d",
                    )
                ),
                vol.Required(
                    CONF_HISTORY_SIZE,
                    default=DEFAULT_HISTORY_SIZE,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=2,
                        max=20,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="elapsed", data_schema=schema)

    async def async_step_initial_action(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose when the current elapsed maintenance cycle started."""
        if user_input is not None:
            mode = str(user_input[CONF_INITIAL_ACTION_MODE])
            if mode == INITIAL_ACTION_CUSTOM:
                return await self.async_step_initial_action_datetime()
            return self._create_pending_elapsed_entry()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_INITIAL_ACTION_MODE,
                    default=INITIAL_ACTION_NOW,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=INITIAL_ACTION_MODES,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="initial_action_mode",
                    )
                )
            }
        )
        return self.async_show_form(step_id="initial_action", data_schema=schema)

    async def async_step_initial_action_datetime(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Seed an elapsed tracker with a known previous action time."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized = _normalize_initial_action_datetime(
                self.hass,
                user_input[CONF_INITIAL_ACTION_DATETIME],
            )
            if normalized is None:
                errors[CONF_INITIAL_ACTION_DATETIME] = "invalid_initial_action"
            else:
                parsed = dt_util.parse_datetime(normalized)
                if parsed is None:
                    errors[CONF_INITIAL_ACTION_DATETIME] = (
                        "invalid_initial_action"
                    )
                elif parsed > dt_util.utcnow():
                    errors[CONF_INITIAL_ACTION_DATETIME] = (
                        "future_initial_action"
                    )
                else:
                    self._pending_entry_data[CONF_MIGRATION_SEED] = RuntimeState(
                        last_action=normalized
                    ).as_dict()
                    return self._create_pending_elapsed_entry()

        schema = vol.Schema(
            {
                vol.Required(CONF_INITIAL_ACTION_DATETIME): DateTimeSelector(),
            }
        )
        return self.async_show_form(
            step_id="initial_action_datetime",
            data_schema=schema,
            errors=errors,
        )

    def _create_pending_elapsed_entry(self) -> ConfigFlowResult:
        """Create the elapsed config entry assembled by the previous steps."""
        return self.async_create_entry(
            title=str(self._pending_entry_data[CONF_NAME]),
            data=self._pending_entry_data,
            options=self._pending_entry_options,
        )

    @staticmethod
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> "DeviceMaintenanceOptionsFlow":
        """Return the options flow."""
        return DeviceMaintenanceOptionsFlow()


class DeviceMaintenanceOptionsFlow(OptionsFlowWithReload):
    """Manage mutable Device Maintenance settings."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Edit mutable tracker options."""
        strategy = self.config_entry.data[CONF_STRATEGY]
        current = dict(self.config_entry.options)
        current_item_type = str(
            current.get(
                CONF_MAINTENANCE_ITEM_TYPE,
                _infer_item_type_from_action(current.get(CONF_ACTION_LABEL)),
            )
        )

        if user_input is not None:
            item_type = str(user_input[CONF_MAINTENANCE_ITEM_TYPE])
            item_quantity = (
                1
                if item_type == ITEM_TYPE_BUILT_IN_BATTERY
                else int(user_input[CONF_MAINTENANCE_ITEM_QUANTITY])
            )
            item_specification = (
                ""
                if item_type == ITEM_TYPE_BUILT_IN_BATTERY
                else str(
                    user_input.get(
                        CONF_MAINTENANCE_ITEM_SPECIFICATION,
                        "",
                    )
                    or ""
                ).strip()
            )
            options = {
                **current,
                CONF_MAINTENANCE_ITEM_TYPE: item_type,
                CONF_MAINTENANCE_ITEM_QUANTITY: item_quantity,
                CONF_MAINTENANCE_ITEM_SPECIFICATION: item_specification,
                CONF_LINKED_ENTITY: user_input.get(CONF_LINKED_ENTITY),
                CONF_UI_GROUP: _clean_optional_text(
                    user_input.get(CONF_UI_GROUP)
                ),
                CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                CONF_ACTION_LABEL: user_input[CONF_ACTION_LABEL],
                CONF_HISTORY_SIZE: int(user_input[CONF_HISTORY_SIZE]),
            }
            if strategy == STRATEGY_SESSION_RUNTIME:
                options[CONF_FALLBACK_INTERVAL_SECONDS] = (
                    float(user_input["fallback_minutes"]) * 60
                )
                options[CONF_MAX_SESSION_SECONDS] = int(
                    user_input[CONF_MAX_SESSION_SECONDS]
                )
            else:
                options[CONF_FALLBACK_INTERVAL_SECONDS] = (
                    float(user_input["fallback_days"]) * 86400
                )
            return self.async_create_entry(data=options)

        common = {
            vol.Required(
                CONF_MAINTENANCE_ITEM_TYPE,
                default=current_item_type,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=MAINTENANCE_ITEM_TYPES,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="maintenance_item_type",
                )
            ),
            vol.Required(
                CONF_MAINTENANCE_ITEM_QUANTITY,
                default=current.get(
                    CONF_MAINTENANCE_ITEM_QUANTITY,
                    DEFAULT_MAINTENANCE_ITEM_QUANTITY,
                ),
            ): _quantity_selector(),
            vol.Optional(
                CONF_MAINTENANCE_ITEM_SPECIFICATION,
                description={
                    "suggested_value": current.get(
                        CONF_MAINTENANCE_ITEM_SPECIFICATION,
                        "",
                    )
                },
            ): TextSelector(),
            vol.Optional(
                CONF_LINKED_ENTITY,
                description={
                    "suggested_value": current.get(CONF_LINKED_ENTITY)
                },
            ): EntitySelector(EntitySelectorConfig()),
            vol.Optional(
                CONF_UI_GROUP,
                description={
                    "suggested_value": current.get(CONF_UI_GROUP, "")
                },
            ): TextSelector(),
            vol.Optional(
                CONF_BATTERY_ENTITY,
                description={
                    "suggested_value": current.get(CONF_BATTERY_ENTITY)
                },
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_ACTION_LABEL,
                default=current.get(
                    CONF_ACTION_LABEL,
                    ACTION_LABEL_BY_ITEM_TYPE.get(
                        current_item_type,
                        DEFAULT_ACTION_LABEL,
                    ),
                ),
            ): TextSelector(),
            vol.Required(
                CONF_HISTORY_SIZE,
                default=current.get(
                    CONF_HISTORY_SIZE,
                    DEFAULT_HISTORY_SIZE,
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=2,
                    max=20,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }

        if strategy == STRATEGY_SESSION_RUNTIME:
            schema = vol.Schema(
                {
                    **common,
                    vol.Required(
                        "fallback_minutes",
                        default=float(
                            current.get(
                                CONF_FALLBACK_INTERVAL_SECONDS,
                                DEFAULT_RUNTIME_FALLBACK_SECONDS,
                            )
                        )
                        / 60,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=100000,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                    vol.Required(
                        CONF_MAX_SESSION_SECONDS,
                        default=current.get(
                            CONF_MAX_SESSION_SECONDS,
                            DEFAULT_MAX_SESSION_SECONDS,
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=3600,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                }
            )
        else:
            schema = vol.Schema(
                {
                    **common,
                    vol.Required(
                        "fallback_days",
                        default=float(
                            current.get(
                                CONF_FALLBACK_INTERVAL_SECONDS,
                                DEFAULT_ELAPSED_FALLBACK_SECONDS,
                            )
                        )
                        / 86400,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0.01,
                            max=3650,
                            step=0.01,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="d",
                        )
                    ),
                }
            )

        return self.async_show_form(step_id="init", data_schema=schema)


def _quantity_selector() -> NumberSelector:
    """Return the selector used for replacement-item quantities."""
    return NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=100,
            step=1,
            mode=NumberSelectorMode.BOX,
        )
    )


def _item_options(base: dict[str, Any]) -> dict[str, Any]:
    """Return common maintenance-item options from the creation flow."""
    return {
        CONF_MAINTENANCE_ITEM_TYPE: base.get(
            CONF_MAINTENANCE_ITEM_TYPE,
            DEFAULT_MAINTENANCE_ITEM_TYPE,
        ),
        CONF_MAINTENANCE_ITEM_QUANTITY: int(
            base.get(
                CONF_MAINTENANCE_ITEM_QUANTITY,
                DEFAULT_MAINTENANCE_ITEM_QUANTITY,
            )
        ),
        CONF_MAINTENANCE_ITEM_SPECIFICATION: str(
            base.get(CONF_MAINTENANCE_ITEM_SPECIFICATION, "") or ""
        ).strip(),
        CONF_LINKED_ENTITY: base.get(CONF_LINKED_ENTITY),
        CONF_UI_GROUP: _clean_optional_text(base.get(CONF_UI_GROUP)),
    }


def _action_default(base: dict[str, Any]) -> str:
    """Return an action label matching the selected maintenance item."""
    item_type = str(
        base.get(
            CONF_MAINTENANCE_ITEM_TYPE,
            DEFAULT_MAINTENANCE_ITEM_TYPE,
        )
    )
    return ACTION_LABEL_BY_ITEM_TYPE.get(item_type, DEFAULT_ACTION_LABEL)


def _infer_item_type_from_action(action_label: Any) -> str:
    """Give old config entries a useful options-flow default."""
    normalized = str(action_label or "").casefold()
    if "blad" in normalized or "blade" in normalized:
        return "blade"
    if "kolsyre" in normalized or "co2" in normalized or "co₂" in normalized:
        return "co2_cylinder"
    if "filter" in normalized:
        return "filter"
    if "patron" in normalized or "refill" in normalized:
        return "cartridge"
    if "batteri" in normalized or "battery" in normalized:
        return "replaceable_battery"
    if "ladd" in normalized or "charg" in normalized:
        return "built_in_battery"
    return ITEM_TYPE_OTHER


def _clean_optional_text(value: Any) -> str:
    """Return a stripped optional text value."""
    return str(value or "").strip()


def _normalize_initial_action_datetime(
    hass: HomeAssistant,
    value: Any,
) -> str | None:
    """Normalize a config-flow datetime to a timezone-aware UTC ISO string."""
    parsed: datetime | None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone)
        if timezone is None:
            return None
        parsed = parsed.replace(tzinfo=timezone)
    return dt_util.as_utc(parsed).isoformat()


def _item_summary(
    item_type: str,
    quantity: int,
    specification: str,
    language: str | None,
) -> str:
    """Return a localized compact migration-preview summary."""
    labels_sv = {
        "built_in_battery": "Inbyggt batteri",
        "replaceable_battery": "Utbytbart batteri",
        "filter": "Filter",
        "cartridge": "Patron/refill",
        "blade": "Blad",
        "co2_cylinder": "CO₂-patron",
        "other": "Annat",
    }
    labels_en = {
        "built_in_battery": "Built-in battery",
        "replaceable_battery": "Replaceable battery",
        "filter": "Filter",
        "cartridge": "Cartridge/refill",
        "blade": "Blade",
        "co2_cylinder": "CO₂ cylinder",
        "other": "Other",
    }
    labels = (
        labels_sv
        if str(language or "").lower().startswith("sv")
        else labels_en
    )
    label = labels.get(item_type, item_type)
    if item_type == ITEM_TYPE_BUILT_IN_BATTERY:
        return label
    if specification:
        return f"{quantity} × {specification} · {label}"
    return f"{quantity} × {label}"
