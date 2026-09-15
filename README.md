# Device Maintenance

[![Validate](https://github.com/Jocke1970/device_maintenance/actions/workflows/validate.yml/badge.svg)](https://github.com/Jocke1970/device_maintenance/actions/workflows/validate.yml)

A Home Assistant custom integration for self-learning device maintenance, runtime tracking, battery cycles, and service intervals.

> **Status:** `0.1.0-beta.2` is the current pre-release on the `beta` branch, intended for controlled real Home Assistant testing alongside the existing legacy/YAML implementation. Active development continues on `dev` as `0.1.0-dev.10`.

Device Maintenance is being rebuilt from a collection of YAML helpers, template sensors, scripts, and automations into a proper Home Assistant helper integration with persistent runtime state and a strategy-based backend.

## What it does

Device Maintenance tracks how long a device has been used, how long it has been since a maintenance action, and how often those actions normally occur. It can then estimate when the next charge, battery replacement, service, refill, or similar action is likely to be needed.

Current goals:

- configure trackers from the Home Assistant UI;
- keep mutable runtime state out of YAML and Git backups;
- learn expected intervals from real maintenance cycles;
- expose native Home Assistant entities for status and actions;
- describe what is actually charged or replaced with structured maintenance-item metadata;
- reuse the same backend for many different device types;
- link helper entities to the source device instead of creating duplicate physical devices;
- support explicit UI grouping so several maintenance trackers for one physical product can be shown together;
- migrate legacy timestamps and history without deleting the old implementation;
- keep the Lovelace frontend as a thin UI client rather than a second maintenance backend.

## Current versions

- beta: `0.1.0-beta.2`
- dev backend: `0.1.0-dev.10`
- current development Lovelace card: `0.2.0-dev.8`

The current backend provides:

- Home Assistant config flow and options flow;
- persistent runtime storage in Home Assistant `.storage`;
- one maintenance sensor per tracker;
- one native action button per tracker;
- stable `entry_id` metadata on both sensor and action button for dynamic frontend pairing;
- optional `ui_group` metadata for combining multiple trackers into one frontend device card;
- editable `picture_key` metadata so a tracker can reuse an existing Lovelace picture even when its display name differs from the image filename;
- structured metadata for built-in batteries, replaceable batteries, filters, cartridges/refills, blades, CO₂ cylinders, and other maintenance items;
- safer legacy metadata inference that avoids product-name false positives such as `OneBlade` being treated as a blade-replacement action;
- optional explicit linking to a physical Home Assistant device through an entity;
- an explicit initial last-action choice for new `elapsed` trackers (`Now` or a known date/time);
- battery metadata support;
- adaptive interval learning from recent completed cycles;
- `session_runtime` and `elapsed` strategies;
- state-safe legacy import for ordinary `elapsed` trackers;
- English and Swedish translations;
- local Home Assistant brand icons;
- Hassfest and HACS validation in CI.

The current development card dynamically discovers Device Maintenance sensors, pairs their action buttons through `entry_id`, renders pictures and maintenance metadata, sorts by urgency, and can combine several independent trackers into one product card through `ui_group`. Grouped presentation has been verified with Philips OneBlade (charge + blade replacement) and Air Wick (refill + battery replacement).

The first real `session_runtime` tracker, Braun Oral-B, has passed side-by-side parity checks for normal runtime accumulation, session reset, restart behavior, maintenance baseline persistence, short-cycle filtering, battery metadata, and source-device linking. A full real charge cycle is still required before retiring the legacy Oral-B tracker.

The first real legacy `elapsed` migration, Garmin Fenix 7 Pro Sapphire, has also preserved last-action time, history, fallback interval, calculated age, and state across a Home Assistant restart.

## Supported strategies

| Strategy | Use case | Current status |
| --- | --- | --- |
| `session_runtime` | Source entity reports the duration of the current usage session | Beta |
| `elapsed` | Track wall-clock time since the previous maintenance action | Beta; legacy import available |
| `cumulative_runtime` | Source exposes a monotonically increasing usage counter | Planned |
| adapters | Specialized sources such as Garmin Gear or Garmin Index Sleep | Planned |

`session_runtime` is designed to handle sources that reset between sessions without counting startup restores as new runtime.

## Maintenance item metadata

A tracker describes both **how the interval is measured** and **what is actually maintained**. Trackers can describe:

- built-in battery;
- replaceable battery, including quantity and battery type;
- filter;
- cartridge / refill;
- blade;
- CO₂ cylinder;
- another custom replacement item.

The optional battery percentage sensor is separate metadata. An `elapsed` tracker can also be explicitly linked to a physical Home Assistant device through any entity belonging to that device.

### UI grouping

Several trackers can belong to the same physical product while keeping independent history, prediction, and action buttons. Give those trackers the same optional **UI group** value in the integration options. The dynamic Device Maintenance card then renders them as one product card with several maintenance rows.

Examples:

```text
OneBlade QP6652          ui_group: oneblade_qp6652
OneBlade QP6652 Bladbyte ui_group: oneblade_qp6652

Air Wick Patronbyte      ui_group: air_wick
Air Wick Batteribyte     ui_group: air_wick
```

The backend still treats every row as an independent tracker. Grouping is presentation metadata only and must not be implemented by pointing `linked_entity`, `battery_entity`, or `source_entity` at another Device Maintenance tracker.

The card derives a shared product title from the common beginning of grouped tracker names, keeps separate progress/prognosis/action rows, and localizes generic replacement metadata such as `cartridge` and `blade` for display.

### Picture key

The dynamic card looks up product pictures from its `pictures` directory. New trackers default `picture_key` to a slug of the tracker name, but the key can be edited later in the tracker options without resetting runtime or learned history. This lets a renamed or more specifically named tracker reuse an existing image, for example `Oral B Genius Series D701 F2B0` can use `picture_key: braun_oral_b`.

New `elapsed` trackers also ask when the current maintenance cycle started. Choose **Now** when the action has just been performed, or enter the known previous action date/time so a tracker does not incorrectly start at zero age.

## How learning works

Each completed maintenance cycle can become a history sample. The expected interval is calculated from recent samples once at least two valid cycles exist.

- fewer than 2 samples: use the configured starting interval;
- 2–3 samples: use a preliminary average;
- 4 or more samples: use the learned average.

The default history size is five samples and can be changed per tracker.

## Installation

There is no stable release yet.

For beta testing, install the `beta` branch manually. Active development remains on `dev`. See [Installation](docs/installation.md).

After installation, add a tracker from:

**Settings → Devices & services → Add integration → Device Maintenance**

Because Device Maintenance declares itself as a Home Assistant helper integration, existing tracker entries are managed from the helper/config-entry UI rather than by creating duplicate integrations for each edit.

## First migration target: Braun Oral-B

The first live parity test uses:

- strategy: `session_runtime`;
- source: `sensor.smart_series_8000_f2b0_varaktighet`;
- battery: `sensor.smart_series_8000_f2b0_batteri`;
- action: charge completed;
- starting interval: 90 minutes;
- history size: 5.

## Branch model

Development follows a strict three-branch flow:

`dev` → `beta` → `main`

- `dev` — active development; schemas may still change;
- `beta` — testable pre-release builds and real Home Assistant validation;
- `main` — stable releases only.

Feature work does not go directly to `beta` or `main`.

## Documentation

- [Beta notes](docs/beta-notes.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Migration plan](docs/migration.md)
- [Development and release flow](docs/development.md)

## Roadmap

The current direction is:

1. keep the dynamic grouped card stable while the remaining backend tracker types are migrated;
2. add `cumulative_runtime` for activity-driven devices;
3. add adapters for Garmin Gear and Garmin Index Sleep;
4. validate the remaining special trackers and complete real-cycle parity tests;
5. decide the release packaging/path for the Lovelace card;
6. retire legacy import/YAML support before the stable release once migration is complete.

## License

MIT
