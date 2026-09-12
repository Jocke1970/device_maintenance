# Migration plan

The existing Home Assistant YAML implementation remains the production source of truth until a Device Maintenance integration tracker has been tested against the same real device.

No legacy helper, automation, sensor, or card path is removed merely because an equivalent backend class exists.

## Phase 1 — Braun Oral-B proof

First migration target:

- display name: Braun Oral-B
- strategy: `session_runtime`
- source: `sensor.smart_series_8000_f2b0_varaktighet`
- battery: `sensor.smart_series_8000_f2b0_batteri`
- action: `Laddad`
- starting interval: 90 minutes
- history size: 5

Why first: it exercises runtime accumulation, source restores, session resets, battery metadata, learned charge intervals, and short-runtime minute formatting without depending on Garmin adapters.

The current YAML implementation stays enabled while the integration runs in parallel. We compare cumulative runtime and a complete charge cycle before switching the card to the integration entity.

## Phase 2 — ordinary elapsed-time trackers

Move devices that currently follow the `input_datetime` + `input_text history` pattern to `elapsed`.

Known examples include:

- Garmin Fenix 7 Pro Sapphire
- Garmin Index Scale
- Withings Body Comp
- Omron M7 Intelli IT
- Remington HC4300
- Skullshaver
- Philips OneBlade charge cycle
- Philips OneBlade blade replacement
- SodaStream CO₂ cylinder replacement
- Air Wick battery replacement
- Air Wick refill replacement

Existing last-action timestamps and learned history should be imported before legacy helpers are removed. The integration therefore needs an explicit migration/import path before this phase is promoted beyond `dev`.

## Phase 3 — cumulative activity runtime

Add `cumulative_runtime` and source adapters for the activity-driven devices:

- Garmin Edge 1040
- Garmin Varia 511
- Bontrager Ion 200 RT Flare
- Stages Power L Shimano Ultegra R8100

The old internal Stages `r8000` identifiers may need compatibility aliases during migration, but the displayed device identity is R8100.

Edge can use a simple cumulative entity attribute. Garmin Gear-backed devices need an adapter that can resolve the correct gear record without embedding Garmin-specific parsing in the generic runtime strategy.

## Phase 4 — Garmin Index Sleep Monitor

Index Sleep is deliberately migrated last.

The current runtime implementation contains important handling for delayed Garmin sleep booking after a charge, including pre-charge excluded seconds. It is considered locked until a new adapter demonstrates parity against the production sensor across charge, delayed-booking, correction, restart, and overnight cases.

Do not simplify this behavior during generic backend work.

## Phase 5 — frontend cut-over and YAML retirement

Once the backend covers all production tracker types:

1. teach the Device Maintenance card to consume integration-native entities/actions;
2. add UI create/edit/delete flows;
3. migrate tracker state;
4. run legacy and new systems side by side long enough to validate results;
5. remove superseded YAML helpers, scripts, automations, and template sensors;
6. remove compatibility code from the card only after the final legacy tracker is gone.

## Promotion gates

### dev → beta

- config flow works in a real HA instance;
- no startup errors;
- storage survives restart/reload;
- first migrated tracker agrees with legacy runtime;
- HACS validation and hassfest pass.

### beta → main

- migration is reversible or state-preserving;
- no duplicate maintenance actions can be booked accidentally;
- removal cleans integration storage for the deleted tracker;
- card behavior is stable on desktop and mobile;
- production device history has been observed across real maintenance cycles.
