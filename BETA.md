# Device Maintenance beta

The current beta is `0.1.0-beta.2`. The next candidate, `0.1.0-beta.3`, adds independent manual battery-percentage and usage-count capabilities.

Device Maintenance is still a pre-release integration. Test it alongside the existing legacy/YAML implementation and keep the old tracker available until the new tracker has demonstrated state and behavior parity for that device.

For `0.1.0-beta.3`, pay particular attention to persisted manual battery values, usage-count corrections, +1 usage registration, usage-history rollover on the normal maintenance action, and restart/reload behavior.

See [Beta notes](docs/beta-notes.md), [Installation](docs/installation.md), and [Migration plan](docs/migration.md).
