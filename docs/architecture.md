# Architecture

## Core model

Device Maintenance is a Home Assistant **helper integration**. One tracked maintenance item maps to one Home Assistant config entry.

Configuration that defines the tracker lives in the config entry. Mutable runtime data lives in `.storage/device_maintenance.runtime` and is keyed by config entry ID.

This deliberately replaces the previous pattern of one or more `input_number`, `input_text`, `input_boolean`, `input_datetime`, template sensors, scripts, and automations per tracked item.

## Branch flow

Only `dev` receives active development commits.

Promotion is strictly:

`dev` → `beta` → `main`

- `dev`: active development; may change storage/config schemas.
- `beta`: migration and real Home Assistant testing.
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

## Strategies

The manager owns one strategy instance per config entry. Strategies expose a common calculated snapshot:

```text
elapsed_seconds
expected_interval_seconds
remaining_seconds
progress_percent
sample_count
confidence
source_available
```

### `session_runtime`

For a source sensor that reports duration of the current session.

Rules:

- numeric → larger numeric: add the positive delta;
- numeric → smaller numeric: treat as a session reset and add the new value;
- unknown/unavailable → numeric: source restore only, add nothing;
- implausibly large deltas are ignored.

This is the first migration target and is designed around the Braun Oral-B duration sensor.

### `elapsed`

Tracks ordinary wall-clock time since the previous maintenance action. It replaces the legacy `input_datetime` + history helper + template sensor pattern.

### Planned `cumulative_runtime`

Uses a monotonically increasing source counter and stores a baseline at each maintenance action. This will replace the current activity-runtime YAML for Edge/Varia/Bontrager/Stages where a cumulative source is available.

### Planned adapters

Special sources that do not fit a simple scalar entity can be isolated behind adapters rather than adding device-specific logic to the manager. Garmin Gear and Index Sleep are expected to use this layer.

## Home Assistant device model

Device Maintenance must not claim ownership of a physical device created by another integration.

When a source or battery entity belongs to an existing device, Device Maintenance helper entities link directly to that source device. This follows the current Home Assistant helper-integration model introduced for the 2026.8 device-registry changes.

A maintenance tracker with no source device may remain unlinked rather than creating a duplicate representation of a physical device.

## Native entities

Each config entry currently creates:

- one sensor exposing maintenance state and learning metadata;
- one button that registers the configured maintenance action.

The sensor keeps compatibility-oriented attributes needed by the existing Device Maintenance Lovelace card during migration.

## Frontend direction

The existing custom card remains usable during migration. Later it will become a UI client for the integration rather than the owner of maintenance logic.

Planned frontend responsibilities:

- list and group trackers;
- add a tracker by launching the integration config flow;
- edit tracker options;
- register the maintenance action;
- upload/select an optional picture;
- display learned interval, runtime/age, remaining estimate, and battery state.

The frontend must not maintain baselines or learning history itself.
