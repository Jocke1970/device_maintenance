# Configuration

Each tracked maintenance item is represented by one Home Assistant config entry. The config flow asks for a tracker name, a tracking strategy, and what is actually charged, replaced, or serviced.

## Common concepts

### Maintenance / replacement item

The tracker stores structured metadata about the item being maintained. This is deliberately separate from the sensor that may report battery percentage.

Supported item types are:

- built-in battery;
- replaceable battery;
- filter;
- cartridge / refill;
- blade;
- CO₂ cylinder;
- other.

A built-in battery does not need quantity or specification metadata. Replaceable items can store a quantity and a free-text specification such as `CR2032`, `AA`, `HEPA H13`, or a replacement-part model.

Examples:

```text
Built-in battery
2 × AA
1 × CR2032
1 × HEPA H13
1 × QP420 blade
```

The maintenance sensor exposes stable machine-readable attributes:

```text
maintenance_item_type
maintenance_item_quantity
maintenance_item_specification
maintenance_item_summary
```

For compatibility with the Device Maintenance card, replaceable-battery trackers also expose a derived `battery_type` attribute such as `2 × AA`.

### Linked entity

A tracker can optionally be linked to a physical Home Assistant device through any entity belonging to that device. This is useful for `elapsed` trackers that have no runtime source and may not have a battery sensor.

The explicit linked entity is preferred for device attachment. If it is not configured, Device Maintenance falls back to the runtime source entity and then the battery percentage entity.

`linked_entity` is **device attachment metadata**, not a grouping mechanism. It should not point to the tracker's own Device Maintenance sensor or to another Device Maintenance tracker. If there is no real physical entity to attach to, leaving the field empty is correct.

### UI group

`ui_group` is optional presentation metadata. Give several independent trackers the same exact value when they belong to one physical product and should be shown together by the dynamic card.

Example:

```text
OneBlade QP6652          ui_group: oneblade_qp6652
OneBlade QP6652 Bladbyte ui_group: oneblade_qp6652
```

Each tracker still has its own config entry, runtime/history, prediction, maintenance item, and action button. Changing `ui_group` does not merge backend state and does not reset learned history.

Use `ui_group` for frontend grouping. Do not simulate grouping by pointing `linked_entity`, `battery_entity`, or `source_entity` at another Device Maintenance sensor.

### Action label

The action label describes what happened when the maintenance cycle is completed, for example:

- `Laddad`;
- `Batteri bytt`;
- `Filter bytt`;
- `Patron bytt`;
- `Blad bytt`;
- `CO₂-patron bytt`;
- `Underhåll utfört`.

New trackers receive a sensible default action label and button icon from the selected maintenance item type. The text remains editable.

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

A tracker can optionally reference a real battery percentage sensor. Device Maintenance exposes the current battery entity and percentage as sensor attributes for UI consumers.

This is different from the maintenance item. A tracker can describe a built-in battery even when no percentage sensor exists, or it can describe a replaceable battery while separately reading its current battery percentage from Home Assistant.

The battery entity must not point to the tracker itself or to another Device Maintenance maintenance sensor. During migration cleanup this kind of accidental reference was found to produce bogus battery metadata. Clear the field when no real percentage sensor exists.

Battery state does not currently alter the learned runtime interval in the Python backend; it is exposed as additional maintenance context.

### Initial last action

A newly created `elapsed` tracker asks when the current maintenance cycle started:

- **Now** — use the time the tracker is created;
- **Enter date/time** — seed the tracker with a known previous charge, replacement, or service time.

A custom date/time is normalized to UTC before it is written to Device Maintenance storage. The selected time may not be in the future. This initial timestamp is mutable runtime state rather than permanent tracker configuration, so the one-shot seed is removed from the config entry after setup.

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
| Maintenance item | Yes | Built-in battery | What is charged/replaced/serviced |
| Linked entity | No | — | Entity used to attach helper entities to a physical device |
| UI group | No | — | Shared frontend grouping key for several trackers on one product |
| Quantity | For replaceable items | 1 | Number changed together |
| Specification | Battery type required for replaceable battery; otherwise optional | — | Type/model/specification |
| Source entity | Yes | — | Sensor whose numeric state is session duration in seconds |
| Battery entity | No | — | Optional real percentage sensor |
| Action label | Yes | Based on item type | Text used for the maintenance action |
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
| Maintenance item | Yes | Built-in battery | What is charged/replaced/serviced |
| Linked entity | No | — | Entity used to attach helper entities to a physical device |
| UI group | No | — | Shared frontend grouping key for several trackers on one product |
| Quantity | For replaceable items | 1 | Number changed together |
| Specification | Battery type required for replaceable battery; otherwise optional | — | Type/model/specification |
| Battery entity | No | — | Optional real percentage sensor |
| Action label | Yes | Based on item type | Text used for the maintenance action |
| Start interval | Yes | 7 days | Used before learning has enough history |
| History size | Yes | 5 | Number of recent completed intervals retained |
| Last action | Yes | Now | Start the current cycle now or from a known previous date/time |

Registering the maintenance action stores the elapsed interval, records the new action timestamp, and starts the next cycle.

## Legacy import

The first migration implementation imports ordinary legacy `elapsed` trackers. In addition to last-action time, history, action label, fallback interval, and battery sensor, it attempts to preserve replacement-item metadata.

Import inference is intentionally conservative:

- an existing `battery_type` such as `2 × AA` becomes a replaceable-battery item;
- action/name text containing charge/laddning is treated as a built-in battery;
- battery replacement, filter, cartridge/refill, blade, and CO₂ wording are mapped to the corresponding generic item type;
- product names alone are not enough to infer a replacement action (`OneBlade` must not become a blade-replacement tracker simply because of its product name);
- unknown cases are imported as `other` and can be corrected in the options flow.

The import preview is non-destructive. Legacy helpers and sensors are not deleted or changed.

After import, verify entity-reference metadata as well as visible age/history. `battery_entity`, `linked_entity`, and `source_entity` should resolve to the intended real source/device entities and must not accidentally point back to Device Maintenance helper sensors.

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
action_icon
picture_key
ui_group
maintenance_item_type
maintenance_item_quantity
maintenance_item_specification
maintenance_item_summary
battery_type
battery_entity
battery_percent
linked_entity
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

Pressing the button registers the configured maintenance action and advances the learning cycle. The button icon is selected from the maintenance item type rather than from the localized action text.

## Editing a tracker

Mutable settings are exposed through the Home Assistant options flow. Maintenance item type, quantity, specification, linked entity, `ui_group`, battery entity, action text, learning interval, and history size can be edited without clearing runtime history.

For a built-in battery, quantity is normalized to 1 and specification is ignored.

Strategy identity and the primary runtime source definition are intentionally treated as structural configuration in the current development version. If a structural change is required during early development, removing and recreating the tracker may be safer than silently changing the meaning of existing runtime history.

## Dynamic card contract

The development Device Maintenance card discovers integration-native sensors through `backend=device_maintenance`, pairs action buttons by `entry_id`, and uses `ui_group` only for presentation grouping.

Current grouped-card behavior includes:

- one shared product title and picture;
- one row per independent maintenance tracker;
- separate urgency/progress, prognosis, metadata, and action button per row;
- a group status derived from the most urgent child tracker;
- localized display text for generic replacement-item metadata;
- responsive desktop/mobile layout.

Grouped presentation has been verified with OneBlade (charge + blade) and Air Wick (refill + battery).

## Planned configuration types

Future versions are expected to add:

- `cumulative_runtime` for monotonic usage counters;
- source attributes as well as source entity states;
- adapter-backed sources such as Garmin Gear;
- specialized adapters such as Garmin Index Sleep;
- frontend-assisted create/edit/delete flows.
