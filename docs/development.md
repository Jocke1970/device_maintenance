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

Device Maintenance uses calendar-based versions.

Stable releases use:

```text
YYYY.MM.PATCH
```

Examples:

```text
2026.10.0
2026.10.1
2026.11.0
```

Beta prereleases use the same calendar base with a compact beta suffix:

```text
2026.10.2b1
2026.10.2b2
```

Development builds use a development suffix:

```text
2026.10.2-dev.1
```

The manifest version and documented version must agree before promotion.

Published beta versions have GitHub prereleases with matching tags. The `beta` publishing workflow publishes only prerelease versions and intentionally skips stable calendar versions that are passing through `beta` on their way to `main`.

Stable versions are published only from `main` by the dedicated stable release workflow, after Python syntax, Hassfest, and HACS validation all pass.

Historical `0.1.0-beta.x` builds remain valid historical prereleases but are no longer the versioning scheme for new releases.

## Validation

The repository uses GitHub Actions validation.

Current checks include:

- Python syntax compilation;
- Home Assistant Hassfest;
- HACS validation.

`dev` may use development-only validation exceptions where explicitly documented, but every promotion to `beta` and `main` must pass the full release-facing checks.

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
- optional usage cycles archive only once and reset the current count safely;
- manual battery values persist without registering maintenance actions;
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
