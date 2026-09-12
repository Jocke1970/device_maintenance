"""Config flow for Device Maintenance."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.helpers.selector import (
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
from homeassistant.util import slugify

from .const import (
    CONF_ACTION_LABEL,
    CONF_BATTERY_ENTITY,
    CONF_FALLBACK_INTERVAL_SECONDS,
    CONF_HISTORY_SIZE,
    CONF_LEGACY_ENTITY,
    CONF_MAX_SESSION_SECONDS,
    CONF_MIGRATION_SEED,
    CONF_NAME,
    CONF_PICTURE_KEY,
    CONF_SOURCE_ENTITY,
    CONF_STRATEGY,
    DEFAULT_ACTION_LABEL,
    DEFAULT_ELAPSED_FALLBACK_SECONDS,
    DEFAULT_HISTORY_SIZE,
    DEFAULT_MAX_SESSION_SECONDS,
    DEFAULT_RUNTIME_FALLBACK_SECONDS,
    DOMAIN,
    STRATEGY_ELAPSED,
    STRATEGY_SESSION_RUNTIME,
)
from .migration import LegacyElapsedCandidate, discover_legacy_elapsed_candidates


class DeviceMaintenanceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Device Maintenance config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._base: dict[str, Any] = {}
        self._legacy_candidate: LegacyElapsedCandidate | None = None

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
            if user_input[CONF_STRATEGY] == STRATEGY_SESSION_RUNTIME:
                return await self.async_step_session_runtime()
            return await self.async_step_elapsed()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_STRATEGY, default=STRATEGY_SESSION_RUNTIME): SelectSelector(
                    SelectSelectorConfig(
                        options=[STRATEGY_SESSION_RUNTIME, STRATEGY_ELAPSED],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="strategy",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="create", data_schema=schema)

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
                CONF_ACTION_LABEL: candidate.action_label,
                CONF_FALLBACK_INTERVAL_SECONDS: candidate.fallback_interval_seconds,
                CONF_HISTORY_SIZE: candidate.history_size,
                CONF_PICTURE_KEY: slugify(candidate.name),
            }
            return self.async_create_entry(
                title=candidate.name,
                data=data,
                options=options,
            )

        last_action = candidate.runtime_state.last_action or "—"
        fallback_days = candidate.fallback_interval_seconds / 86400.0
        return self.async_show_form(
            step_id="legacy_preview",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": candidate.name,
                "entity": candidate.entity_id,
                "last_action": last_action,
                "samples": str(len(candidate.runtime_state.history_seconds)),
                "fallback_days": f"{fallback_days:.2f}",
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
                CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                CONF_ACTION_LABEL: user_input[CONF_ACTION_LABEL],
                CONF_FALLBACK_INTERVAL_SECONDS: float(user_input["fallback_minutes"]) * 60,
                CONF_HISTORY_SIZE: int(user_input[CONF_HISTORY_SIZE]),
                CONF_MAX_SESSION_SECONDS: int(user_input[CONF_MAX_SESSION_SECONDS]),
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
                vol.Required(CONF_ACTION_LABEL, default=DEFAULT_ACTION_LABEL): TextSelector(),
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
                vol.Required(CONF_HISTORY_SIZE, default=DEFAULT_HISTORY_SIZE): NumberSelector(
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
            data = {
                CONF_NAME: self._base[CONF_NAME],
                CONF_STRATEGY: STRATEGY_ELAPSED,
            }
            options = {
                CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                CONF_ACTION_LABEL: user_input[CONF_ACTION_LABEL],
                CONF_FALLBACK_INTERVAL_SECONDS: float(user_input["fallback_days"]) * 86400,
                CONF_HISTORY_SIZE: int(user_input[CONF_HISTORY_SIZE]),
                CONF_PICTURE_KEY: slugify(self._base[CONF_NAME]),
            }
            return self.async_create_entry(
                title=self._base[CONF_NAME],
                data=data,
                options=options,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_BATTERY_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_ACTION_LABEL, default=DEFAULT_ACTION_LABEL): TextSelector(),
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
                vol.Required(CONF_HISTORY_SIZE, default=DEFAULT_HISTORY_SIZE): NumberSelector(
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

        if user_input is not None:
            options = {
                **current,
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
            vol.Optional(
                CONF_BATTERY_ENTITY,
                description={"suggested_value": current.get(CONF_BATTERY_ENTITY)},
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_ACTION_LABEL,
                default=current.get(CONF_ACTION_LABEL, DEFAULT_ACTION_LABEL),
            ): TextSelector(),
            vol.Required(
                CONF_HISTORY_SIZE,
                default=current.get(CONF_HISTORY_SIZE, DEFAULT_HISTORY_SIZE),
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
