# LeadVille DB/Log Paths

- Config/assignments: `db/leadville.db` (read-only in bridge).
- Runtime writes: `db/leadville_runtime.db` (AMG timer events + sensor impacts).
- Verbose BT50 samples: `db/bt50_samples.db`.

All code must import paths from `impact_bridge.paths`. Do **not** hardcode paths.
Parsers are **only** imported from `impact_bridge.ble.parsers`.