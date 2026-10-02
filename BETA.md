# Device Maintenance beta

The next beta release candidate is `0.1.0-beta.6`.

This release finalizes the HACS beta path introduced in beta.5.

## HACS beta delivery

Device Maintenance beta versions are published as GitHub prereleases only after `dev → beta` promotion and release validation.

The repository deliberately keeps `main` for stable releases only. Because there is no stable release yet, `hacs.json` now sets `hide_default_branch: true` so HACS offers published releases rather than the intentionally empty stable-only default branch.

Users can add Device Maintenance as a custom HACS integration repository and enable prerelease updates for the repository to receive beta updates.

Device Maintenance remains pre-release software. Continue testing alongside the existing legacy/YAML implementation until tracker parity is verified.

For `0.1.0-beta.6`, continue validating picture upload/replacement/removal with Device Maintenance Card `0.2.0-dev.11`.

See [Beta notes](docs/beta-notes.md), [Installation](docs/installation.md), and [Migration plan](docs/migration.md).
