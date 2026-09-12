# Installation

Device Maintenance is currently in early development. Until the first `beta` or stable release is promoted, the `dev` branch should only be installed for deliberate testing.

## Development install

The integration lives in:

```text
custom_components/device_maintenance/
```

A simple test install from the Home Assistant terminal is:

```bash
cd /config
rm -rf /tmp/device_maintenance

git clone --depth 1 --branch dev \
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

## Updating a development install

Repeat the development install command above, then restart Home Assistant. The existing config entries and runtime state are stored by Home Assistant and are not part of the copied Python package.

During early development, storage and config schemas may still change. Back up Home Assistant before testing a newer `dev` revision against important state.

## HACS

The repository already contains `hacs.json` and is validated in CI, but the integration is not yet released from `main`.

For now, do not use the default branch as a normal HACS installation source. The intended progression is:

```text
dev → beta → main
```

Once a release is promoted to `main`, HACS becomes the normal installation target.

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

See [Configuration](configuration.md) for strategy details and [Migration plan](migration.md) for the full rollout order.
