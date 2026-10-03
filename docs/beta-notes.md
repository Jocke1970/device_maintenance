# Release notes and beta history

## 2026.10.1b1 — documentation cleanup

This prerelease aligns the public documentation with the actual stable/HACS setup after `2026.10.0`. It does not intentionally change backend behavior.

### Documentation fixes

- stable HACS installation is now the primary installation path;
- `main` is documented as the stable/default branch;
- HACS release delivery and prerelease-switch behavior are described accurately;
- `session_runtime` and `elapsed` are marked stable;
- pre-stable wording in configuration, migration, and legacy-import docs is made historical;
- the separately distributed Device Maintenance Card `0.2.0-dev.11` is explicitly documented.


## 2026.10.0 — stable

The tested backend from `0.1.0-beta.6` was promoted as the first calendar-versioned stable release, `2026.10.0`.

### Release mechanics

- versioning switches to calendar format `YYYY.MM.PATCH`;
- future beta versions use forms such as `2026.10.1b1`;
- stable versions pass through `beta` for validation but are published only from `main`;
- a dedicated stable workflow repeats Python syntax, Hassfest, and HACS validation before creating the GitHub release;
- the Lovelace card remains a separately distributed frontend at `0.2.0-dev.11`.

No backend feature behavior is intentionally changed by the versioning/release transition.


## 0.1.0-beta.6

This beta completes the HACS prerelease path while preserving the strict `dev → beta → main` model.

### Added

- `hide_default_branch: true` in `hacs.json`;
- explicit HACS custom-repository installation instructions;
- documentation for the transition to a stable-only `main` branch and release-based HACS delivery.

### Behavior

At the time of beta.6, HACS used published GitHub prereleases while the still-empty stable-only `main` branch was hidden from downloadable versions. This was the final bootstrap step before stable `2026.10.0` populated `main`.

Users who enable prerelease updates for the Device Maintenance repository can receive beta updates through HACS.

Beta.6 otherwise retains the backend and Device Maintenance Card `0.2.0-dev.11` test scope from beta.5.


## 0.1.0-beta.5

This beta adds a release path for HACS-managed prerelease updates while preserving the strict `dev → beta → main` branch model.

### Added

- dedicated `Publish beta` GitHub Actions workflow triggered only by pushes to `beta`;
- release gating with Python syntax compilation, Hassfest, and HACS validation;
- automatic GitHub prerelease creation using the exact manifest version as the release tag;
- idempotent release publishing so an existing version is not recreated;
- HACS installation/update documentation for prerelease users.

### Behavior

Feature work still starts on `dev`. A beta is prepared and validated on `dev`, promoted to `beta`, and only then published as a GitHub prerelease. HACS can consider that prerelease when prerelease updates are enabled for the repository.

Beta.5 otherwise retains the native picture backend and Device Maintenance Card `0.2.0-dev.11` test scope from beta.4.


## 0.1.0-beta.4

This beta restores product-picture management as a native Device Maintenance feature instead of relying on another integration.

### Added

- admin-only `device_maintenance/picture/upload` websocket command;
- admin-only `device_maintenance/picture/remove` websocket command;
- backend-owned storage in `/config/www/device_maintenance_card/pictures/`;
- JPEG, PNG, and WebP validation with a 5 MB size limit;
- atomic replacement with stale-extension cleanup;
- tracker lookup by `entry_id`, with the backend resolving the configured `picture_key`;
- Device Maintenance Card `0.2.0-dev.11` restores **Bild** upload/replace and remove controls directly below the product picture.

### Behavior

Picture changes are presentation-only. Uploading, replacing, or removing a picture does not modify maintenance runtime, learned history, manual battery percentage, usage count, or usage history.

The picture API is now owned by Device Maintenance and no longer depends on Garmin Connect's former generic card-picture websocket implementation.


## 0.1.0-beta.3

This beta adds two independent optional capabilities for devices that are not fully connected to Home Assistant.

### Added

- battery source selection: none, Home Assistant battery sensor, or manually entered battery percentage;
- native manual-battery number entity with persisted runtime state;
- optional manual usage counting with a native `+1 usage` button;
- editable current usage-count number for correcting missed or accidental increments;
- persisted `usage_history` stored per tracker;
- learned average usages per maintenance cycle after at least two completed non-zero cycles;
- `expected_usage_count`, `usages_remaining`, sample count, and confidence metadata on the maintenance sensor;
- capability settings are independent, so usage counting works without battery percentage and manual battery percentage works without usage counting;
- existing trackers with a configured `battery_entity` remain compatible and are inferred as sensor-backed battery mode;
- Python syntax compilation added to CI before beta promotion.

### Behavior

Registering the normal maintenance action still owns the maintenance-cycle boundary. If manual usage counting is enabled, the same action also archives the current non-zero usage count and resets it to zero. Battery percentage changes never register maintenance automatically.

This supports devices where only usage count is observable, as well as devices where battery percentage can be read from the device display while uses are counted manually.

### Known beta limitations

- usage counting is manual only; automatic counting from a Home Assistant entity is planned for a later version;
- manual battery percentage is contextual data and is not yet used to extrapolate battery drain per usage;
- the separate development Lovelace card does not yet expose all new auxiliary controls; the native Home Assistant entities are the beta control surface.


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
