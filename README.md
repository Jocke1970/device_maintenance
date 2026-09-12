# Device Maintenance

A Home Assistant custom integration for self-learning device maintenance, runtime tracking, battery cycles, and service intervals.

> **Status:** early development. The `dev` branch is the active work branch and is not yet intended for production use.

## Branch model

Development follows a strict three-branch flow:

- `dev` — active development
- `beta` — testable pre-release builds
- `main` — stable releases only

Changes move in one direction: `dev` → `beta` → `main`.

## Architecture

Device Maintenance is being rebuilt as a Home Assistant helper integration instead of a collection of YAML helpers and template sensors.

Each tracked item is its own Home Assistant config entry. Static configuration lives in the config entry, while changing runtime state such as baselines, learned intervals, history, and last actions is stored in Home Assistant storage.

The backend is strategy based. The first development milestone contains:

- `session_runtime` — accumulates positive deltas from a per-session runtime sensor, designed first for devices such as the Braun Oral-B toothbrush.
- `elapsed` — tracks wall-clock time between maintenance actions.

Planned strategies include cumulative runtime from monotonically increasing counters and adapters for more specialized sources.

## Design goals

- Add and edit trackers from the Home Assistant UI.
- Keep runtime state out of YAML and out of Git backups.
- Learn expected service/charge intervals from recent real cycles.
- Reuse one generic backend for different device types.
- Link helper entities to the source device instead of creating duplicate physical devices.
- Preserve enough compatibility metadata for the existing Device Maintenance Lovelace card during migration.

## Current development version

`0.1.0-dev.1`

This first scaffold provides config flows, persistent runtime storage, a strategy layer, a maintenance sensor, and a native action button. Migration from the existing YAML implementation has not started yet.
