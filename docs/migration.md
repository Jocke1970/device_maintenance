# Migration plan

The existing Home Assistant YAML implementation remains the production source of truth until a Device Maintenance integration tracker has been tested against the same real device.

No legacy helper, automation, sensor, or card path is removed merely because an equivalent backend class exists.

The migration principle is always:

```text
create new tracker → run in parallel → compare → preserve state → cut over → remove legacy
```

## State that must be preserved

Depending on tracker type, migration may need to import:

- last maintenance action timestamp;
- cumulative runtime total;
- current runtime baseline;
- recent learned interval history;
- special correction/exclusion state used by an adapter.

A migration is not considered complete if the visible entity works but learned history or baseline state is silently reset.

## Phase 1 — Braun Oral-B proof

First migration target:

- display name: Braun Oral-B;
- strategy: `session_runtime`;
- source: `sensor.smart_series_8000_f2b0_varaktighet`;
- battery: `sensor.smart_series_8000_f2b0_batteri`;
- action: `Laddad`;
- starting interval: 90 minutes;
- history size: 5;
- max accepted session delta: 1200 seconds.

Why first: it exercises runtime accumulation, source restores, session resets, battery metadata, learned charge intervals, short-runtime minute formatting, restart behavior, and the maintenance action boundary without depending on Garmin adapters.

The current YAML implementation stays enabled while the integration runs in parallel.

Parity checks:

1. startup with an already non-zero toothbrush session must not add false runtime;
2. a normal increasing session must add only real new seconds;
3. a session reset must continue accumulation correctly;
4. Home Assistant restart must not duplicate runtime;
5. battery metadata must follow the selected battery entity;
6. pressing `Laddad` must store one valid interval and reset only the current baseline;
7. the next cycle must start from zero effective runtime while cumulative total remains monotonic;
8. learning labels and expected interval must match the intended history rules.

### Beta verification status

Before `0.1.0-beta.1`, the real Oral-B tracker was tested side by side with the legacy YAML implementation.

Verified:

- an already populated source value was ignored on startup rather than booked as new runtime;
- the first test session produced identical cumulative runtime in Python and legacy YAML;
- a Home Assistant restart preserved the total without double-counting;
- a source reset to zero did not add runtime;
- a second session after reset continued the cumulative total with zero difference from legacy;
- the maintenance action moved the Python baseline while preserving cumulative total;
- the deliberately short 26-second test cycle was correctly rejected from learning history;
- the moved baseline survived restart;
- sensor and action button linked to the existing toothbrush device;
- battery metadata followed the selected battery entity.

Still required before retiring the legacy Oral-B tracker:

- at least one complete real charge cycle;
- validation that a real cycle is stored as a learning sample;
- validation of the expected interval once multiple real samples exist;
- frontend cut-over to the integration-native tracker/action.

## Phase 2 — ordinary elapsed-time trackers

Move devices that currently follow the `input_datetime` + `input_text history` pattern to `elapsed`.

Known examples include:

- Garmin Fenix 7 Pro Sapphire;
- Garmin Index Scale;
- Withings Body Comp;
- Omron M7 Intelli IT;
- Remington HC4300;
- Skullshaver;
- Philips OneBlade charge cycle;
- Philips OneBlade blade replacement;
- SodaStream CO₂ cylinder replacement;
- Air Wick battery replacement;
- Air Wick refill replacement.

Before any of these are retired, the integration needs an explicit import path for the old last-action timestamp and interval history.

The desired result is continuity: adding the new integration must not make a mature tracker look newly initialized.

## Phase 3 — cumulative activity runtime

Add `cumulative_runtime` and source adapters for activity-driven devices:

- Garmin Edge 1040;
- Garmin Varia 511;
- Bontrager Ion 200 RT Flare;
- Stages Power L Shimano Ultegra R8100.

The old internal Stages `r8000` identifiers may need compatibility aliases during migration, but the displayed device identity is R8100.

Edge can use a simple cumulative entity attribute. Garmin Gear-backed devices need an adapter that resolves the correct gear record without embedding Garmin-specific parsing in the generic runtime strategy.

Migration must preserve the current cumulative-source baseline. Otherwise old lifetime activity would be mistaken for runtime in the new maintenance cycle.

## Phase 4 — Garmin Index Sleep Monitor

Index Sleep is deliberately migrated last.

The current runtime implementation contains important handling for delayed Garmin sleep booking after a charge, including pre-charge excluded seconds. That implementation is considered locked until a new adapter demonstrates parity.

Required parity scenarios include:

- normal overnight usage;
- charge action;
- Home Assistant restart;
- delayed sleep booking after a charge;
- later correction of an already booked sleep session;
- pre-charge usage exclusion;
- remaining-hours and remaining-nights estimates.

Do not simplify this behavior merely to fit the generic strategy interface. The adapter exists specifically so specialized accounting can remain specialized.

## Phase 5 — frontend cut-over and YAML retirement

Once the backend covers all production tracker types:

1. teach the Device Maintenance card to consume integration-native entities and actions;
2. add UI-assisted create/edit/delete flows;
3. import existing tracker state;
4. run legacy and new systems side by side long enough to validate results;
5. switch the card to the integration entities;
6. remove superseded YAML helpers, scripts, automations, and template sensors;
7. remove compatibility code from the card only after the final legacy tracker is gone.

## Removal rule

Legacy state is removed **last**.

For each tracker, the old implementation must remain recoverable until:

- the new tracker survives restart;
- at least one real maintenance cycle has been registered where practical;
- displayed runtime/age agrees with the old implementation;
- learned interval history is preserved or intentionally re-seeded;
- the action button is confirmed not to double-book maintenance.

## Promotion gates

### `dev` → `beta`

- config flow works in a real Home Assistant instance;
- no startup errors;
- storage survives restart and integration reload;
- the first migrated tracker agrees with legacy runtime;
- maintenance actions do not duplicate history;
- Hassfest passes;
- HACS validation passes;
- migration limitations are documented.

### `beta` → `main`

- migration is reversible or state-preserving;
- no duplicate maintenance actions can be booked accidentally;
- deleting a tracker cleans only that tracker's integration storage;
- card behavior is stable on desktop and mobile;
- production device history has been observed across real maintenance cycles;
- release documentation matches the actual supported strategies;
- no known migration blocker remains for the release scope.
