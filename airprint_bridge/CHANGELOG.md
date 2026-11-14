# 1.3.3

- Resolve browser requests against the HA ingress path explicitly.
- Separate each maintenance result and confirmation field; add a bounded activity log.
- Persist CUPS queue definitions together with job metadata across restarts.

# 1.3.2

- Retain job IDs in CUPS job queries so the sidebar can display history.

# 1.3.1

- Verify the ET-2500 using standard SNMP model identification; its profile has no EEPROM model-name field.
- Present read-only status and counters in plain language.

# 1.3.0

- Add admin ingress sidebar, recent jobs, and watchdog health endpoint.
- Add explicit, model-checked maintenance controls and counter snapshots.
- Restore HA API access; fix disabled boolean options.
- Keep completed print documents disabled and bound metadata retention.

# 1.2.2

- Bundle ET-2500 ESC/P-R and set A4/color/simplex defaults.
- Limit CUPS to loopback and remove unnecessary host access.
