# Device Maintenance

[![Validate](https://github.com/Jocke1970/device_maintenance/actions/workflows/validate.yml/badge.svg)](https://github.com/Jocke1970/device_maintenance/actions/workflows/validate.yml)

A Home Assistant custom integration for self-learning device maintenance, runtime tracking, battery cycles, and service intervals.

> **Status:** first beta released from the `beta` branch. `0.1.0-beta.1` is intended for controlled real Home Assistant testing alongside the existing legacy/YAML implementation. Active development continues on `dev` as `0.1.0-dev.4`.

Device Maintenance is being rebuilt from a collection of YAML helpers, template sensors, scripts, and automations into a proper Home Assistant helper integration with persistent runtime state and a strategy-based backend.

## What it does

Device Maintenance tracks how long a device has been used, how long it has been since a maintenance action, and how often those actions normally occur. It can then estimate when the next charge, battery replacement, service, refill, or similar action is likely to be needed.

Current goals:

- configure trackers from the Home Assistant UI;
- keep mutable runtime state out of YAML and Git backups;
- learn expected intervals from real maintenance cycles;
- expose native Home Assistant entities for status and actions;
- reuse the same backend for many different device types;
- link helper entities to the source device instead of creating duplicate physical devices;
- remain compatible with the existing Device Maintenance Lovelace card during migration.

## Current versions

- beta: `0.1.0-beta.1`
- dev: `0.1.0-dev.4`

The current backend provides:

- Home Assistant config flow and options flow;
- persistent runtime storage in Home Assistant `.storage`;
- one maintenance sensor per tracker;
- one native action button per tracker;
- battery metadata support;
- adaptive interval learning from recent completed cycles;
- `session_runtime` and `elapsed` strategies;
- state-safe preview/import for compatible legacy `elapsed` trackers on `dev`;
- English and Swedish translations;
- local Home Assistant brand icons;
- Hassfest and HACS validation in CI.

The first real `session_runtime` tracker, Braun Oral-B, has passed side-by-side parity checks for normal runtime accumulation, session reset, restart behavior, maintenance baseline persistence, short-cycle filtering, battery metadata, and source-device linking. A full real charge cycle is still required before retiring the legacy Oral-B tracker.

## Supported strategies

| Strategy | Use case | Current status |
| --- | --- | --- |
| `session_runtime` | Source entity reports the duration of the current usage session | Beta |
| `elapsed` | Track wall-clock time since the previous maintenance action | Beta; legacy state import under test on `dev` |
| `cumulative_runtime` | Source exposes a monotonically increasing usage counter | Planned |
| adapters | Specialized sources such as Garmin Gear or Garmin Index Sleep | Planned |

`session_runtime` is the first production migration target and is designed to handle sources that reset between sessions without counting startup restores as new runtime.

## How learning works

Each completed maintenance cycle can become a history sample. The expected interval is calculated from recent samples once at least two valid cycles exist.

- fewer than 2 samples: **Startintervall**;
- 2–3 samples: **Preliminärt snitt**;
- 4 or more samples: **Inlärt snitt**.

The default history size is five samples and can be changed per tracker.

## Installation

There is no stable release yet.

For beta testing, install the `beta` branch manually and run it alongside the existing YAML implementation. Active development remains on `dev`. See [Installation](docs/installation.md).

After installation, add a tracker from:

**Settings → Devices & services → Add integration → Device Maintenance**

On `dev`, the first screen can also discover and preview compatible legacy `elapsed` trackers. See [Legacy import](docs/legacy-import.md).

## First migration target: Braun Oral-B

The first live parity test uses:

- strategy: `session_runtime`;
- source: `sensor.smart_series_8000_f2b0_varaktighet`;
- battery: `sensor.smart_series_8000_f2b0_batteri`;
- action: `Laddad`;
- starting interval: 90 minutes;
- history size: 5.

The legacy YAML implementation remains active during the beta test. Nothing is removed until the integration has demonstrated matching behavior across real usage and maintenance cycles.

## Branch model

Development follows a strict three-branch flow:

`dev` → `beta` → `main`

- `dev` — active development; schemas may still change;
- `beta` — testable pre-release builds and real Home Assistant migration validation;
- `main` — stable releases only.

Feature work does not go directly to `beta` or `main`.

## Documentation

- [Beta notes](docs/beta-notes.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Migration plan](docs/migration.md)
- [Legacy import](docs/legacy-import.md)
- [Development and release flow](docs/development.md)

## Roadmap

The current direction is:

1. observe Braun Oral-B across a full real charge cycle;
2. validate state-safe import for ordinary elapsed-time trackers;
3. migrate ordinary elapsed-time trackers;
4. add `cumulative_runtime` for activity-driven devices;
5. add adapters for Garmin Gear and Garmin Index Sleep;
6. move the Device Maintenance card from owning logic to acting as a UI client;
7. retire the legacy YAML implementation only after state-safe migration.

## License

MIT
