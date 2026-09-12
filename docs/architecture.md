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
├── sensor.py
├── button.py
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
action_label
fallback_interval
history_size
strategy-specific settings
```

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

The manager owns integration-wide behavior such as battery metadata and entity notifications. The strategy owns the meaning of runtime and maintenance actions.

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

When a source or battery entity belongs to an existing device, Device Maintenance helper entities link directly to that source device.

A maintenance tracker with no source device may remain unlinked rather than creating a duplicate representation of a physical device.

This keeps Device Maintenance focused on maintenance state rather than pretending to be the hardware integration.

## Native entities

Each config entry currently creates:

- one sensor exposing maintenance state and learning metadata;
- one button that registers the configured maintenance action.

The sensor keeps compatibility-oriented attributes needed by the existing Device Maintenance Lovelace card during migration.

The button is deliberately the mutation boundary for normal maintenance actions. The frontend should call backend actions rather than alter baselines or history itself.

## Frontend boundary

The existing custom card remains usable during migration. Later it should become a UI client for the integration rather than the owner of maintenance logic.

Planned frontend responsibilities:

- list and group trackers;
- launch add/edit flows;
- register a maintenance action;
- upload or select an optional picture;
- display learned interval, runtime/age, remaining estimate, and battery state.

The frontend must not own:

- baselines;
- runtime accumulation;
- learning history;
- source restore logic;
- migration state.

Those remain backend responsibilities.

## Compatibility during migration

The integration intentionally exposes metadata that resembles the existing YAML sensor contract so the current card can be adapted incrementally.

Compatibility is temporary. Once every legacy tracker has been migrated and the card consumes integration-native state directly, obsolete compatibility attributes can be removed in a versioned change.
