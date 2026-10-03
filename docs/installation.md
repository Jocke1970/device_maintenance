# Installation

Device Maintenance is available as a stable HACS-installable custom integration.

Current stable backend release:

```text
2026.10.0
```

The repository follows:

```text
dev → beta → main
```

`main` is the stable branch and the GitHub default branch. Stable HACS installs use published GitHub releases rather than arbitrary branch snapshots.

## Recommended: install with HACS

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add:

   ```text
   https://github.com/Jocke1970/device_maintenance
   ```

4. Select repository type **Integration**.
5. Open **Device Maintenance** in HACS.
6. Choose **Download** / **Install**.
7. Restart Home Assistant when HACS asks you to do so.

After restart, add the integration from:

**Settings → Devices & services → Add integration → Device Maintenance**

For normal use, leave prerelease updates disabled. HACS will then track stable GitHub releases such as `2026.10.0`.

## Beta / prerelease updates in HACS

Users who deliberately want to test prereleases can enable prerelease updates for the Device Maintenance repository in HACS.

Future prereleases use calendar-based versions such as:

```text
2026.10.1b1
2026.10.1b2
```

Prereleases follow the same promotion path:

```text
dev → beta
```

The `beta` branch publishes GitHub prereleases only after Python syntax, Hassfest, and HACS validation succeed.

Stable versions may pass through `beta` as release candidates, but the beta publisher intentionally does not publish a stable version as a prerelease. Stable GitHub releases are created only after promotion to `main`.

## Updating with HACS

When HACS offers a newer Device Maintenance release:

1. open the Device Maintenance repository in HACS;
2. review the offered version;
3. choose **Download** / **Update**;
4. restart Home Assistant when requested.

Device Maintenance runtime state is stored in Home Assistant storage and is not replaced by the HACS package update.

Back up Home Assistant before testing prereleases or migration-sensitive changes.

## Manual stable installation

HACS is the recommended installation method. For recovery or deliberate manual installation, install the exact stable tag rather than an arbitrary branch snapshot:

```bash
cd /config
rm -rf /tmp/device_maintenance

git clone --depth 1 --branch 2026.10.0 \
  https://github.com/Jocke1970/device_maintenance.git \
  /tmp/device_maintenance

rm -rf /config/custom_components/device_maintenance
mkdir -p /config/custom_components

cp -R \
  /tmp/device_maintenance/custom_components/device_maintenance \
  /config/custom_components/device_maintenance

rm -rf /tmp/device_maintenance
```

Then restart Home Assistant.

Verify that this file exists:

```text
/config/custom_components/device_maintenance/manifest.json
```

and that its version is:

```text
2026.10.0
```

If Device Maintenance does not appear in the integration picker after restart, check the Home Assistant log for import or manifest errors.

## Deliberate beta branch installation

For branch-level beta testing only, use:

```bash
cd /config
rm -rf /tmp/device_maintenance

git clone --depth 1 --branch beta \
  https://github.com/Jocke1970/device_maintenance.git \
  /tmp/device_maintenance

rm -rf /config/custom_components/device_maintenance
mkdir -p /config/custom_components

cp -R \
  /tmp/device_maintenance/custom_components/device_maintenance \
  /config/custom_components/device_maintenance

rm -rf /tmp/device_maintenance
```

Restart Home Assistant after copying the integration.

This path is intended for deliberate branch testing or recovery. Normal beta users should prefer HACS prerelease updates.

## Development install

For active development, replace the branch with:

```text
--branch dev
```

The `dev` branch may contain incomplete work and should only be installed when intentionally testing development changes.

## HACS repository behavior

The repository contains `hacs.json` and is validated in CI.

`main` is both:

- the stable branch;
- the GitHub default branch.

`hacs.json` sets:

```json
"hide_default_branch": true
```

This is intentional. HACS should offer published GitHub releases rather than an unversioned snapshot of the current default-branch HEAD.

Current release behavior:

- stable release → published from `main`;
- beta prerelease → published from `beta`;
- development build → never published as a HACS release.

## Lovelace card

The Device Maintenance Lovelace card is currently distributed separately from the backend integration.

Current tested frontend:

```text
Device Maintenance Card 0.2.0-dev.11
```

The card resource is:

```text
/local/device_maintenance_card/device-maintenance-card.js?v=0.2.0-dev.11
```

Resource type:

```text
JavaScript module
```

The custom card type is:

```yaml
type: custom:device-maintenance-card
```

Updating the backend through HACS does not automatically update this separate frontend resource.

## Safe migration from legacy YAML

The migration policy remains state-first:

1. keep the existing YAML tracker available;
2. add or verify the equivalent Device Maintenance tracker;
3. compare runtime, history, maintenance actions, restart behavior, and battery metadata;
4. switch the frontend only after parity is demonstrated;
5. remove the old YAML implementation last.

Do not delete legacy helpers merely because the integration has been installed.

## Historical first parity target

Braun Oral-B was the first `session_runtime` parity target:

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

Before the first beta promotion, the integration matched the legacy implementation for normal session accumulation, session reset, Home Assistant restart, maintenance baseline persistence, and short-cycle filtering.

See [Release notes and beta history](beta-notes.md), [Configuration](configuration.md), and [Migration plan](migration.md) for more detail.
