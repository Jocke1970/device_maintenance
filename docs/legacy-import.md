# Legacy import

`0.1.0-dev.4` starts the state-safe legacy migration path.

The first importer intentionally supports only ordinary `elapsed` trackers that expose the legacy Device Maintenance attributes used by the YAML implementation:

- `display_name`;
- `datetime_entity`;
- `history_entity`;
- `action_label`;
- `fallback_interval_days`;
- optional `battery_entity`.

The importer discovers compatible `sensor.device_maintenance_*` entities, shows a preview, then creates a normal Device Maintenance config entry.

## State preservation

The import copies:

- the previous maintenance timestamp from the referenced `input_datetime`;
- interval history from the referenced `input_text` JSON list;
- fallback interval;
- action label;
- optional battery entity.

Legacy history values are stored as days. They are converted to seconds before being written to the integration runtime store.

Imported runtime state is written to the Device Maintenance `Store` before the tracker starts. A temporary migration seed exists only while the config entry is being created and is removed from config-entry data during setup.

## Safety rules

Import is additive only:

- no YAML is modified;
- no legacy helper is deleted;
- no legacy history is reset;
- duplicate import of the same discovered legacy sensor is blocked;
- already configured tracker names are omitted from discovery;
- malformed history or timestamp data is surfaced as a preview warning instead of being silently invented.

The old and new trackers should remain active side by side until their displayed age, expected interval, history, and maintenance action behavior have been compared.

## Current limitations

This first importer does **not** yet migrate:

- `session_runtime` state such as Braun Oral-B cumulative totals and baselines;
- cumulative activity-runtime trackers;
- Garmin Gear-backed runtime;
- Garmin Index Sleep delayed-booking/exclusion state;
- frontend/card configuration.

Those cases need dedicated state mappings or adapters and will be added separately.

## Test flow

On a `dev` install:

1. open **Settings → Devices & services → Add integration → Device Maintenance**;
2. choose **Import legacy tracker**;
3. choose one compatible elapsed tracker;
4. review the timestamp, sample count, fallback interval, and warnings;
5. continue to create the tracker;
6. compare the new integration sensor against the old YAML sensor;
7. restart Home Assistant and verify that imported state remains intact.

Do not remove the legacy tracker as part of this test.
