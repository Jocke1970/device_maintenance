# Installation

Device Maintenance is currently in beta. Published beta versions are intended for controlled real Home Assistant testing alongside the existing legacy/YAML implementation.

## Beta install

The integration lives in:

```text
custom_components/device_maintenance/
```

Install the current beta from the Home Assistant terminal:

```bash
cd /config
rm -rf /tmp/device_maintenance

git clone --depth 1 --branch beta \
  https://github.com/Jocke1970/device_maintenance.git \
  /tmp/device_maintenance

rm -rf /config/custom_components/device_maintenance
mkdir -p /config/custom_components
cp -R /tmp/device_maintenance/custom_components/device_maintenance \
  /config/custom_components/device_maintenance

rm -rf /tmp/device_maintenance
```

Then restart Home Assistant.

After restart, add the integration from:

**Settings → Devices & services → Add integration → Device Maintenance**

If Device Maintenance does not appear in the integration picker, verify that this file exists:

```text
/config/custom_components/device_maintenance/manifest.json
```

and check the Home Assistant log for import or manifest errors.

## Updating a beta install

Repeat the beta installation command above, then restart Home Assistant. Existing config entries and runtime state are stored by Home Assistant and are not part of the copied Python package.

Back up Home Assistant before testing a newer beta against important state.

## Development install

For active development, replace `--branch beta` with:

```text
--branch dev
```

The `dev` branch may contain incomplete work and should only be used when deliberately testing the next change before promotion to beta.

## HACS

The repository contains `hacs.json` and is validated in CI.

Beta versions are published as GitHub prereleases after the normal promotion path:

```text
dev → beta → main
```

The `beta` branch has a dedicated publishing workflow. It repeats Python syntax, Hassfest, and HACS validation and only then publishes a GitHub prerelease using the manifest version as the release tag.

HACS uses published GitHub releases as version sources. To receive Device Maintenance beta updates through HACS, enable prerelease updates for the Device Maintenance repository in HACS. Stable users can leave prerelease updates disabled.

The manual `beta` branch installation above remains useful for recovery or deliberate branch-level testing.

## Safe testing alongside the legacy system

The current migration policy is parallel operation:

1. keep the existing YAML tracker enabled;
2. add the equivalent tracker through Device Maintenance;
3. compare runtime, history, maintenance actions, restart behavior, and battery metadata;
4. switch the frontend only after parity is demonstrated;
5. remove the old YAML tracker last.

Do not delete existing helpers merely because a new integration entity appears.

## First recommended test

The first test target is Braun Oral-B using `session_runtime`:

```text
Name: Braun Oral-B
Strategy: session_runtime
Source: sensor.smart_series_8000_f2b0_varaktighet
Battery: sensor.smart_series_8000_f2b0_batteri
Action: Laddad
Start interval: 90 min
History size: 5
Max session delta: 1200 s
```

The first beta was promoted only after the Oral-B tracker matched the legacy runtime across normal session accumulation, session reset, Home Assistant restart, maintenance baseline persistence, and short-cycle filtering.

See [Beta notes](beta-notes.md), [Configuration](configuration.md), and [Migration plan](migration.md) for more detail.
