# Development and release flow

Device Maintenance uses a strict three-branch model:

```text
dev → beta → main
```

## Branch responsibilities

### `dev`

Active development happens here.

Allowed:

- new strategies;
- storage/config schema changes;
- experimental migration helpers;
- frontend compatibility work;
- incomplete but reviewable features.

The `dev` branch may be installed for deliberate testing, but it is not a production contract.

### `beta`

`beta` is for testable pre-release builds.

A change reaches `beta` only after it has already been developed and validated on `dev`.

Expected characteristics:

- config flow works in a real Home Assistant instance;
- storage survives restart/reload;
- the release scope is documented;
- known migration limitations are explicit;
- CI is green;
- no intentional destructive migration behavior remains.

No feature work starts directly on `beta`.

### `main`

`main` contains stable releases only.

A release reaches `main` only after the corresponding beta has survived real use and migration testing.

No experimental code should be committed directly to `main`.

## Promotion rule

Promotion is one-way:

```text
dev → beta → main
```

If a problem is found in `beta`, fix it on `dev` first and then promote the corrected state again.

If a stable defect requires a hotfix, the resulting fix still needs to be reconciled back into `dev` so branch history does not diverge permanently.

## Versioning

Development versions use a suffix such as:

```text
0.1.0-dev.1
0.1.0-dev.2
```

Beta builds use a pre-release identifier, for example:

```text
0.1.0-beta.1
```

Stable releases use normal semantic versions:

```text
0.1.0
0.2.0
1.0.0
```

The manifest version and documented version must agree before promotion.

The first beta promotion is `0.1.0-beta.1`. It was gated on a real Braun Oral-B parity test covering session accumulation, reset handling, restart persistence, maintenance baseline persistence, and short-cycle learning rejection.

## Validation

The repository uses GitHub Actions validation.

Current checks include:

- Home Assistant Hassfest;
- HACS validation.

`dev` may temporarily relax repository-publishing checks that are unrelated to Python correctness during bootstrap, but `beta` and `main` are intended to pass the full release-facing checks.

A green CI run is necessary but not sufficient for promotion. Device Maintenance persists user state, so real Home Assistant runtime tests are part of the release gate.

## Development principles

### Keep configuration and state separate

Config entries describe what a tracker is. Home Assistant storage records what has happened to it.

Do not put frequently changing runtime state back into YAML or config entry data merely because it is easy to serialize there.

### Keep strategies generic

A strategy should implement a reusable accounting model such as:

- elapsed wall-clock time;
- per-session runtime accumulation;
- cumulative runtime baseline subtraction.

Brand- or integration-specific lookup belongs in an adapter.

### Preserve state before cleanup

Migration work must import or intentionally map old timestamps, baselines, and history before legacy entities are removed.

Deleting old YAML is the final migration step, not the first.

### Keep the frontend thin

The Lovelace card may display state and invoke backend actions. It must not become the owner of runtime baselines, learning history, or source restore logic.

### Avoid duplicate physical devices

Device Maintenance is a helper integration. If the tracked source already belongs to a physical Home Assistant device, maintenance entities should link to that device rather than create another representation of the hardware.

## Testing a change locally

During early development the practical loop is:

1. update `dev`;
2. copy `custom_components/device_maintenance` into the Home Assistant config directory;
3. restart Home Assistant;
4. inspect startup logs;
5. create or reload the test tracker;
6. verify entity states and attributes;
7. exercise the maintenance action;
8. restart again and verify persisted state;
9. compare against the legacy implementation where a migration target exists.

For source-driven strategies, include startup with a non-zero source value in the test matrix. This catches false runtime booking during entity restore.

## Pull request / review checklist

Before promoting a meaningful backend change, verify:

- no accidental runtime is added on startup;
- state survives restart;
- history is not double-booked;
- deletion removes only the correct entry state;
- invalid source states do not corrupt totals;
- options reload cleanly;
- sensor attributes remain internally consistent;
- translations match new config fields;
- README/docs describe the actual behavior;
- CI passes.

## Documentation ownership

The documentation is part of the release surface.

Update the relevant file when behavior changes:

- `README.md` — project overview and current public status;
- `docs/beta-notes.md` — current beta scope, verified behavior, and known limitations;
- `docs/installation.md` — installation and update path;
- `docs/configuration.md` — strategy and entity contract;
- `docs/architecture.md` — backend design boundaries;
- `docs/migration.md` — state-safe migration order;
- `docs/development.md` — branch, validation, and release policy.
