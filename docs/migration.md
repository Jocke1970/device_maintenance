# Migration plan

The existing Home Assistant YAML implementation remains the production source of truth for a tracker until the corresponding Device Maintenance integration tracker has been tested against the same real device.

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
- validation of the expected interval once multiple real samples exist.

The dynamic frontend can already consume the integration-native Oral-B tracker/action. The remaining Oral-B gate is real-cycle validation rather than frontend capability.

## Phase 2 — ordinary elapsed-time trackers

Move devices that follow the `input_datetime` + `input_text history` pattern to `elapsed`.

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

The current development/test installation has migrated the ordinary `elapsed` set to integration-native trackers. Garmin Fenix 7 Pro Sapphire was the first state-preserving proof and retained last-action time, history, fallback interval, calculated age, and state across restart.

The state-safe importer remains available during beta because migration is not yet considered a stable-release contract.

### Grouped-product validation

Some products legitimately have more than one independent maintenance tracker. These must stay separate in the backend and use `ui_group` only for frontend presentation.

Verified development examples:

```text
OneBlade QP6652          ui_group: oneblade_qp6652
OneBlade QP6652 Bladbyte ui_group: oneblade_qp6652
```

and Air Wick refill + battery replacement using one shared Air Wick UI group.

The dynamic card successfully renders these as one product with separate progress, prognosis, metadata, and action buttons.

### Post-import entity-reference validation

Migration is not complete until reference metadata is checked as well as timestamps/history.

Verify that:

- `battery_entity` points to a real battery percentage sensor or is empty;
- `linked_entity` points to an entity belonging to the real physical device or is empty;
- `source_entity` points to the intended source for source-driven strategies;
- none of those fields points to the tracker's own Device Maintenance sensor;
- none of those fields is used to point at another Device Maintenance tracker merely to create grouping.

A development cleanup found accidental self/cross references on the OneBlade trackers. Clearing those references did not reset runtime history because they are editable options/metadata. Grouping is now handled only through `ui_group`.

## Phase 3 — cumulative activity runtime

Add `cumulative_runtime` and source adapters for activity-driven devices:

- Garmin Edge 1040;
- Garmin Varia 511;
- Bontrager Ion 200 RT Flare;
- Stages Power L Shimano Ultegra R8100.

The old internal Stages `r8000` identifiers may need compatibility aliases during migration, but the displayed device identity is R8100.

Edge can use a simple cumulative entity attribute. Garmin Gear-backed devices need an adapter that resolves the correct gear record without embedding Garmin-specific parsing in the generic runtime strategy.

Migration must preserve the current cumulative-source baseline. Otherwise old lifetime activity would be mistaken for runtime in the new maintenance cycle.

A future generic `cumulative_counter`/counter-style strategy may also be useful for non-time maintenance such as counting SodaStream pump presses per CO₂ cylinder, but this remains a later design item and is not part of the current migration contract.

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

Frontend cut-over is now partly complete in development. The dynamic Device Maintenance card:

- consumes integration-native sensor/button entities;
- discovers trackers dynamically;
- pairs actions by `entry_id`;
- supports structured maintenance-item metadata;
- supports explicit `ui_group` product grouping;
- has been validated on desktop/mobile-style layouts with grouped OneBlade and Air Wick examples.

Remaining work before full YAML retirement:

1. finish special backend coverage (`cumulative_runtime`, Garmin Gear, Index Sleep);
2. complete real-cycle parity where still required;
3. decide the release packaging/path for the Lovelace card;
4. optionally add frontend-assisted create/edit/delete flows;
5. keep legacy and new systems side by side for every remaining special tracker until parity is proven;
6. remove superseded YAML helpers, scripts, automations, and template sensors only after the final cut-over;
7. remove temporary importer/compatibility code only when the stable release no longer needs it.

## Removal rule

Legacy state is removed **last**.

For each tracker, the old implementation must remain recoverable until:

- the new tracker survives restart;
- at least one real maintenance cycle has been registered where practical;
- displayed runtime/age agrees with the old implementation;
- learned interval history is preserved or intentionally re-seeded;
- the action button is confirmed not to double-book maintenance;
- entity-reference metadata has been checked for accidental self/cross Device Maintenance references.

## Promotion gates

### `dev` → `beta`

- config flow works in a real Home Assistant instance;
- no startup errors;
- storage survives restart and integration reload;
- migrated tracker state agrees with legacy behavior for the promoted scope;
- maintenance actions do not duplicate history;
- options edits do not unexpectedly reset runtime history;
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
- legacy importer/YAML retirement is intentional for the release scope;
- no known migration blocker remains for the release scope.
