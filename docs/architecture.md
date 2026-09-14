# Architecture

## Core model

Device Maintenance is a Home Assistant **helper integration**. One tracked maintenance item maps to one Home Assistant config entry.

Stable configuration lives in the config entry. Mutable runtime data lives in Home Assistant storage and is keyed by config entry ID.

This deliberately replaces the previous pattern of one or more `input_number`, `input_text`, `input_boolean`, `input_datetime`, template sensors, scripts, and automations per tracked item.

## Repository layout

```text
custom_components/device_maintenance/
├── __init__.py
├── manifest.json
├── const.py
├── models.py
├── store.py
├── manager.py
├── config_flow.py
├── migration.py
├── sensor.py
├── button.py
├── brand/
│   ├── icon.png
│   └── icon@2x.png
├── translations/
│   ├── en.json
│   └── sv.json
└── strategies/
    ├── __init__.py
    ├── base.py
    ├── elapsed.py
    └── session_runtime.py
```

The integration layer is intentionally small. Device-specific behavior belongs in strategies or adapters rather than in the manager.

## Branch flow

Only `dev` receives active development commits.

Promotion is strictly:

```text
dev → beta → main
```

- `dev`: active development; config and storage schemas may still change;
- `beta`: real Home Assistant testing, migration validation, and release hardening;
- `main`: stable releases only.

No feature work goes directly to `beta` or `main`.

## Config entry vs runtime state

A config entry contains the stable definition of a tracker, for example:

```text
name
strategy
source_entity
battery_entity
linked_entity
ui_group
action_label
maintenance_item_type
maintenance_item_quantity
maintenance_item_specification
fallback_interval
history_size
strategy-specific settings
```

`ui_group` is presentation metadata only. Two trackers that share a `ui_group` remain separate config entries with separate runtime/history and action buttons.

Runtime state contains values that change while Home Assistant runs:

```text
total_runtime_seconds
baseline_runtime_seconds
last_action
history_seconds
```

Runtime state is intentionally kept out of Git-backed YAML.

The current storage key is:

```text
device_maintenance.runtime
```

and uses Home Assistant's `Store` helper. Writes are coalesced with a short delay so frequent runtime updates do not result in unnecessary disk writes.

Deleting a config entry also removes the persistent state associated with that entry.

## Runtime lifecycle

For each config entry:

1. Home Assistant creates a `DeviceMaintenanceManager`;
2. the manager loads the entry's persisted `RuntimeState`;
3. the manager creates the configured strategy;
4. the strategy registers source listeners if needed;
5. sensor and button entities subscribe to manager updates;
6. strategy changes are persisted through the shared store;
7. unloading the entry stops listeners and flushes state.

The manager owns integration-wide behavior such as battery metadata, presentation metadata, and entity notifications. The strategy owns the meaning of runtime and maintenance actions.

## Strategy contract

All strategies derive from a common base and expose the same calculated snapshot:

```text
elapsed_seconds
expected_interval_seconds
remaining_seconds
progress_percent
sample_count
confidence
source_available
```

The common learning model is also implemented in the base class.

A valid completed interval is appended to history, trimmed to the configured history size, and ignored if shorter than the minimum sample duration.

The expected interval is:

- the configured fallback while fewer than two valid samples exist;
- the arithmetic mean of stored history once at least two samples exist.

Confidence labels are:

```text
0–1 samples  → Startintervall
2–3 samples  → Preliminärt snitt
4+ samples   → Inlärt snitt
```

## Strategies

### `session_runtime`

For a source sensor that reports duration of the current session in seconds.

Rules:

- numeric → larger numeric: add the positive delta;
- numeric → smaller numeric: treat as a session reset and add the new value;
- unknown/unavailable → numeric: source restore only, add nothing;
- invalid, negative, or out-of-range source states are ignored;
- implausibly large transition deltas are rejected by the configurable max-session guard.

The strategy maintains a cumulative internal total and a maintenance baseline. Runtime for the current cycle is:

```text
total_runtime_seconds - baseline_runtime_seconds
```

Registering the maintenance action stores that cycle as history when valid, moves the baseline to the current total, and records the action timestamp.

This is the first migration target and is designed around the Braun Oral-B duration sensor.

### `elapsed`

Tracks ordinary wall-clock time since the previous maintenance action. It replaces the legacy `input_datetime` + history helper + template sensor pattern.

No runtime source entity is required.

### Planned `cumulative_runtime`

Uses a monotonically increasing source counter and stores a baseline at each maintenance action.

This will replace the current activity-runtime YAML for devices such as:

- Garmin Edge 1040;
- Garmin Varia 511;
- Bontrager Ion 200 RT Flare;
- Stages Power L Shimano Ultegra R8100.

The generic strategy should know only how to consume a cumulative number. Product-specific source resolution belongs in adapters.

### Planned adapters

Special sources that do not fit a simple scalar entity should be isolated behind adapters rather than adding device-specific logic to the manager.

Expected examples:

- Garmin Gear record lookup;
- Garmin Index Sleep runtime accounting.

Index Sleep specifically requires parity with delayed sleep booking and correction handling before migration.

## Home Assistant device model

Device Maintenance must not claim ownership of a physical device created by another integration.

When a source, battery entity, or explicitly selected linked entity belongs to an existing device, Device Maintenance helper entities link directly to that source device.

A maintenance tracker with no source device may remain unlinked rather than creating a duplicate representation of a physical device.

`linked_entity` is for physical device attachment only. It must not be used to group maintenance trackers, and it should not point to the tracker's own Device Maintenance sensor or to another Device Maintenance maintenance sensor. The same rule applies to `battery_entity` and, unless a future strategy explicitly defines otherwise, `source_entity`.

This keeps Device Maintenance focused on maintenance state rather than pretending to be the hardware integration.

## Native entities

Each config entry currently creates:

- one sensor exposing maintenance state and learning metadata;
- one button that registers the configured maintenance action.

The sensor exposes stable `entry_id` and `backend=device_maintenance` metadata so a frontend can discover trackers and pair them with their buttons without hard-coded entity IDs. It also exposes `ui_group` as optional presentation metadata.

The button is deliberately the mutation boundary for normal maintenance actions. The frontend calls backend actions rather than altering baselines or history itself.

## Frontend boundary

The dynamic Device Maintenance Lovelace card is now a thin client of the integration-native sensor/button contract rather than the owner of maintenance logic.

Current development-card behavior (`0.2.0-dev.8`) includes:

- dynamic discovery of Device Maintenance sensors;
- action-button pairing by `entry_id`;
- urgency sorting and show-all filtering;
- optional product pictures with fallback icons;
- maintenance category, age/runtime, remaining estimate, confidence, item metadata, and battery context;
- explicit grouping through shared `ui_group` values;
- a common product title for grouped trackers while preserving separate child rows/actions;
- desktop/mobile presentation;
- localized display labels for generic maintenance-item metadata.

Grouped presentation has been verified with OneBlade (charge + blade replacement) and Air Wick (refill + battery replacement).

The card is currently developed as a separate Lovelace resource while the integration backend remains in this repository. Release packaging for the card is still an open decision.

The frontend may:

- list and group trackers;
- display state, metadata, prognosis, and pictures;
- register a maintenance action through the native button entity;
- later launch add/edit/delete flows.

The frontend must not own:

- baselines;
- runtime accumulation;
- learning history;
- source restore logic;
- migration state.

Those remain backend responsibilities.

## Grouping model

Grouping does not change the backend object model. The relationship is:

```text
physical product
  ├── maintenance tracker A (ConfigEntry, Store state, button)
  └── maintenance tracker B (ConfigEntry, Store state, button)
            ↑
       same ui_group
```

The shared `ui_group` tells the frontend only that the trackers may be presented as one product card. It does not create a shared baseline, shared learning history, or shared action.

This distinction is important because one product may have unrelated maintenance intervals, for example charging an internal battery every few months while replacing a blade on a different schedule.

## Compatibility during migration

The integration intentionally exposes compatibility-oriented metadata required by the dynamic Device Maintenance card and by state-safe migration diagnostics.

Compatibility remains versioned. Once every legacy tracker has been migrated and the frontend/release contract is finalized, obsolete compatibility attributes can be removed only through an explicit versioned change.
