# Beta notes

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
