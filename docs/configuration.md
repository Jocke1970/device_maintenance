# Configuration

Each tracked maintenance item is represented by one Home Assistant config entry. The config flow asks for a tracker name and a strategy, then presents the fields relevant to that strategy.

## Common concepts

### Action label

The action label describes what happened when the maintenance cycle is completed, for example:

- `Laddad`
- `Batteri bytt`
- `Servad`
- `Patron bytt`
- `Blad bytt`

Each tracker exposes a Home Assistant button that registers this action.

### Start interval

The configured fallback interval is used until enough real history exists to calculate a learned interval.

Learning states are:

- fewer than 2 valid samples: `Startintervall`;
- 2–3 samples: `Preliminärt snitt`;
- 4 or more samples: `Inlärt snitt`.

Once at least two samples exist, the expected interval is the arithmetic mean of the stored history.

### History size

The default history size is 5. The oldest sample is discarded when the configured limit is exceeded.

Intervals shorter than 60 seconds are not stored as learning samples.

### Battery entity

A tracker can optionally reference a battery percentage sensor. Device Maintenance exposes the current battery entity and percentage as sensor attributes for UI consumers.

Battery state does not currently alter the learned runtime interval in the Python backend; it is exposed as additional maintenance context.

## `session_runtime`

Use `session_runtime` when the source sensor reports the duration of the current usage session and resets between sessions.

Typical source behavior:

```text
0 → 1 → 2 → 3 → ... → 0
```

or a new session may appear as:

```text
120 → 1 → 2 → 3
```

### Fields

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| Name | Yes | — | Display name of the tracker |
| Strategy | Yes | `session_runtime` | Runtime strategy |
| Source entity | Yes | — | Sensor whose numeric state is session duration in seconds |
| Battery entity | No | — | Optional percentage sensor |
| Action label | Yes | `Laddad` | Text used for the maintenance action |
| Start interval | Yes | 90 min | Used before learning has enough history |
| History size | Yes | 5 | Number of recent completed intervals retained |
| Max session delta | Yes | 1200 s | Largest accepted delta for one state transition |

### Runtime rules

The current implementation intentionally handles startup and restore events conservatively:

- numeric → larger numeric: add the positive difference;
- numeric → smaller numeric: treat it as a session reset and add the new value;
- `unknown`/`unavailable` → numeric: source restore only, add no runtime;
- invalid, negative, or implausibly large values are ignored;
- a single accepted transition delta cannot exceed the configured max session delta.

Registering the maintenance action stores the completed runtime interval as a history sample when valid, moves the baseline to the current cumulative total, and records the action time.

## `elapsed`

Use `elapsed` for maintenance that is based on ordinary wall-clock time since the previous action.

Examples include charging a device, changing a filter, replacing a refill, changing a blade, or scheduled service where no runtime source is required.

### Fields

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| Name | Yes | — | Display name of the tracker |
| Strategy | Yes | `elapsed` | Wall-clock strategy |
| Battery entity | No | — | Optional percentage sensor |
| Action label | Yes | `Laddad` | Text used for the maintenance action |
| Start interval | Yes | 7 days | Used before learning has enough history |
| History size | Yes | 5 | Number of recent completed intervals retained |

Registering the maintenance action stores the elapsed interval, records the new action timestamp, and starts the next cycle.

## Native entities

Each tracker currently creates two entities.

### Maintenance sensor

Suggested entity ID:

```text
sensor.device_maintenance_<name>
```

For `session_runtime`, the native sensor state is runtime in hours. For `elapsed`, the native state is age in days.

Common attributes include:

```text
backend
entry_id
display_name
strategy
action_label
picture_key
battery_entity
battery_percent
source_entity
source_available
sample_count
confidence
progress_percent
last_action
```

`session_runtime` additionally exposes:

```text
source_total_seconds
baseline_seconds
expected_interval_hours
hours_remaining
```

`elapsed` additionally exposes:

```text
expected_interval_days
days_remaining
```

### Action button

Suggested entity ID:

```text
button.device_maintenance_<name>_action
```

Pressing the button registers the configured maintenance action and advances the learning cycle.

## Editing a tracker

Mutable settings are exposed through the Home Assistant options flow. Strategy identity and the primary source definition are intentionally treated as structural configuration in the first development version.

If a structural change is required during early development, removing and recreating the tracker may be safer than silently changing the meaning of existing runtime history.

## Planned configuration types

Future versions are expected to add:

- `cumulative_runtime` for monotonic usage counters;
- source attributes as well as source entity states;
- adapter-backed sources such as Garmin Gear;
- specialized adapters such as Garmin Index Sleep;
- import of existing legacy timestamps, baselines, and history;
- frontend-assisted create/edit/delete flows.
