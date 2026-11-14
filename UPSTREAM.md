Based on learningcodewithAi/airprint-bridge, MIT licensed.

Upstream commit: 5398a2f85a250c4fd34d6b6794600dba3587e27c

Local changes: bundled ESC/P-R driver; A4, color and simplex defaults; no USB, HA API or host share access; CUPS loopback-only and web interface disabled; bounded CUPS job size and history disabled. Original attribution remains in LICENSE.

1.3.0 adds an ingress panel, bounded persistent job metadata, Supervisor health checks, optional maintenance via the separately licensed pinned Epson toolkit, and restores HA API access at user request. Maintenance operations require in-panel confirmation.
