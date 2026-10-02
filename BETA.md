# Device Maintenance beta

The next beta release candidate is `0.1.0-beta.5`.

This release keeps the native Device Maintenance picture backend from beta.4 and adds the release plumbing needed for HACS-managed beta updates.

## HACS beta delivery

After `dev → beta` promotion, the `beta` branch runs a dedicated release workflow. The workflow repeats Python syntax, Hassfest, and HACS validation before publishing a GitHub prerelease whose tag matches the integration manifest version.

HACS uses published GitHub releases as version sources. Users who enable prerelease updates for Device Maintenance can therefore receive beta updates through HACS instead of manually copying the `beta` branch.

Device Maintenance is still a pre-release integration. Test it alongside the existing legacy/YAML implementation and keep old trackers available until the new tracker has demonstrated state and behavior parity for that device.

For `0.1.0-beta.5`, continue validating picture upload/replacement/removal with Device Maintenance Card `0.2.0-dev.11`, including persistence across Home Assistant restart and browser reload.

See [Beta notes](docs/beta-notes.md), [Installation](docs/installation.md), and [Migration plan](docs/migration.md).
