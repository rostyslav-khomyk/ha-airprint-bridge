# Deployment validation — 14 November 2026

Home Assistant OS 18.4, Core 2026.11.1, amd64. Installed from this GitHub repository using the Home Assistant App Store/Supervisor. Final build: 1.3.5.

## Confirmed

- Image builds successfully on the actual HA host.
- Startup selects the exact **EPSON ET-2500 Series, Epson Inkjet Printer Driver (ESC/P-R) for Linux** PPD.
- Host-network IPP listener answers Get-Printer-Attributes with A4, color, simplex and URF capabilities.
- PDF Print-Job accepted and paper output confirmed by the user.
- Admin sidebar is enabled; ingress HTML, health and status APIs respond successfully through Supervisor ingress.
- Direct LAN requests to the panel port return HTTP 403.
- Read-only maintenance identifies the ET-2500 via its standard SNMP model identity and reads status, page counters and waste counters.
- A requested nozzle-check command was sent via the app and its physical pattern output was confirmed by the user.
- User exercised the reset control. Subsequent independent reads reported the waste counter at zero. No reset was run automatically during installation.
- Supervisor watchdog, start-on-boot and HA API access are enabled. Automatic app updates are disabled.
- A completed CUPS test job remained visible after app updates/restarts; completed state was verified through the ingress history API.
- Direct nozzle/clean/power buttons were verified in the served 1.3.5 HTML.
- The temporary Mac gateway was stopped after HA printing was confirmed.
- Ten local tests pass, including ingress peer access, confirmation boundaries, wrong-model rejection, the ET-2500 identity path and the CUPS job-query protocol. Browser script syntax passes node --check.

## Limits

Normal head cleaning and experimental power cleaning have not been physically tested. The latter is not verified as Epson's complete Power Ink Flushing procedure. A zero counter does not establish the physical condition of waste pads.

The initial Mac proof of concept and its driver are separate from this Linux implementation. Only the Linux tests above establish HA deployment behavior.

An initial browser URL error was addressed using an explicit ingress base path; per-action result areas and a bounded maintenance activity log were added. CUPS queue definitions and bounded history metadata persist under /data; completed print document files remain disabled.

## Research

Native HA IPP integration provides monitoring, not a legacy-printer AirPrint conversion pipeline. Community print apps already exist, so this implementation adapts an MIT-licensed bridge rather than replacing CUPS, Avahi or the Linux drivers.

- [HA IPP integration](https://www.home-assistant.io/integrations/ipp)
- [Upstream bridge](https://github.com/learningcodewithAi/airprint-bridge)
- [Alternative app](https://github.com/aaronfagan/ha-airprint)
- [HA ingress](https://contributors.home-assistant.io/apps/guides/ingress/)
- [Epson Linux utility capabilities](https://download.ebz.epson.net/man/linux/utility.html)
- [Maintenance toolkit](https://github.com/Ircama/epson_print_conf/tree/2dc3bebacf314f22bd6484acdb2a7434c7cc00ad)
