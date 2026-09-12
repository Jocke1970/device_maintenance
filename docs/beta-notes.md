# Beta notes

## 0.1.0-beta.2

This is the second Device Maintenance beta release.

The main focus is safer real-world configuration and migration: ordinary `elapsed` trackers can now preserve existing state, maintenance/replacement items are represented with structured metadata, and new elapsed trackers can start from either the current time or a known previous action date/time.

### Added

- state-safe legacy import for ordinary `elapsed` trackers;
- structured maintenance-item metadata for built-in batteries, replaceable batteries, filters, cartridges/refills, blades, CO₂ cylinders, and other items;
- quantity and specification metadata for replaceable items, including compatibility `battery_type` values such as `2 × AA`;
- optional explicit linking to a physical Home Assistant device through an entity;
- maintenance-action icons derived from the maintenance item type;
- initial last-action selection for new `elapsed` trackers;
- custom date/time seeding for an already-running maintenance cycle;
- backward-compatible maintenance-item inference for trackers created before the new metadata fields existed;
- improved legacy import preview and metadata inference.

### Real Home Assistant validation before beta

The promoted build was tested in a real Home Assistant instance before release.

Verified:

- Braun Oral-B `session_runtime` regression remained intact after the configuration changes;
- Oral-B cumulative runtime and maintenance baseline persisted correctly;
- Garmin Fenix 7 Pro Sapphire legacy `elapsed` migration preserved last-action time, history, fallback interval, calculated age, and state across restart;
- a new elapsed tracker using **Now** preserved its last-action timestamp across restart;
- a new elapsed tracker using a historical date/time immediately reported the correct age and remaining interval;
- historical date/time handling remained correct across local timezone conversion and restart;
- replaceable-battery metadata produced the expected `2 × AA` quantity/specification/summary and action;
- generic replacement metadata produced the expected `1 × HEPA H13` filter summary and action;
- built-in battery, replaceable battery, and filter action icons were correct;
- Hassfest and HACS validation passed on the development build before promotion.

### Beta policy

Keep the existing YAML tracker enabled while testing migrated devices. Do not remove legacy helpers until state and behavior have been verified for the corresponding tracker.

The current migration sequence remains:

```text
create/import tracker → run in parallel → compare → preserve state → cut over → remove legacy
```

### Still not included

- `session_runtime` legacy-state migration;
- `cumulative_runtime`;
- Garmin Gear adapters;
- Garmin Index Sleep adapter;
- integration-native Lovelace card cut-over;
- stable release guarantees.

## 0.1.0-beta.1

This is the first Device Maintenance beta release.

The beta is intentionally narrow: it proves the new Home Assistant-native backend and begins real migration testing without removing the existing YAML implementation.

### Included

- config-flow based tracker creation;
- persistent runtime state in Home Assistant storage;
- native maintenance sensor and action button;
- source-device linking for helper entities;
- battery metadata;
- adaptive interval learning;
- `session_runtime` strategy;
- `elapsed` strategy;
- Swedish and English translations;
- local integration branding;
- Hassfest and HACS validation.

### Braun Oral-B parity verified before beta

The first real tracker has been tested side by side with the legacy YAML implementation.

Verified:

- startup with an already populated session source does not book false runtime;
- normal session deltas match the legacy implementation exactly;
- session reset continues cumulative runtime correctly;
- Home Assistant restart does not duplicate runtime;
- total runtime survives restart;
- maintenance action moves the runtime baseline correctly;
- a deliberately short test cycle is rejected from learning history;
- action baseline survives restart;
- integration entities link to the existing toothbrush device rather than creating a duplicate device.

A complete real charge cycle is still required before the Oral-B legacy tracker is retired.

### Beta policy

Keep the existing YAML tracker enabled while testing the beta. Do not remove legacy helpers until state and behavior have been verified for the corresponding tracker.

The current migration sequence remains:

```text
create new tracker → run in parallel → compare → preserve state → cut over → remove legacy
```

### Not yet included

- legacy-state import for ordinary elapsed trackers;
- `cumulative_runtime`;
- Garmin Gear adapters;
- Garmin Index Sleep adapter;
- integration-native Lovelace card cut-over;
- stable release guarantees.
