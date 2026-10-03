# Installation

Device Maintenance supports HACS installation from published GitHub releases. The current stable release is `2026.10.0`; prerelease users can opt into future beta releases.

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

Releases follow the normal promotion path:

```text
dev → beta → main
```

The `beta` branch publishes only beta prereleases. Stable calendar versions pass through `beta` without creating a prerelease and are published only after promotion to `main`.

To install the beta through HACS:

1. open HACS;
2. open the three-dot menu and choose **Custom repositories**;
3. add `https://github.com/Jocke1970/device_maintenance`;
4. select repository type **Integration**;
5. install Device Maintenance from HACS;
6. enable prerelease updates for the Device Maintenance repository if you want HACS to track beta releases.

The repository keeps `main` for stable releases only. Until the first stable release exists, `hacs.json` hides the default branch from HACS version choices so users select published releases instead of the intentionally empty stable branch.

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
