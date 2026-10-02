# Device Maintenance beta

The current beta release is `0.1.0-beta.4`.

This release restores product-picture upload, replacement, and removal as a native Device Maintenance feature. The picture backend is owned by Device Maintenance and no longer depends on Garmin Connect.

Device Maintenance is still a pre-release integration. Test it alongside the existing legacy/YAML implementation and keep old trackers available until the new tracker has demonstrated state and behavior parity for that device.

For `0.1.0-beta.4`, verify picture upload/replacement/removal with Device Maintenance Card `0.2.0-dev.11`, including persistence across Home Assistant restart and browser reload. JPEG, PNG, and WebP up to 5 MB are supported.

See [Beta notes](docs/beta-notes.md), [Installation](docs/installation.md), and [Migration plan](docs/migration.md).
