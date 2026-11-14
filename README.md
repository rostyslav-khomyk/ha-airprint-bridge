# Epson AirPrint Bridge for Home Assistant

A small adaptation of [AirPrint Bridge](https://github.com/learningcodewithAi/airprint-bridge), using its existing CUPS + ippeveprinter + Avahi implementation. This is a Home Assistant **App Store repository**, not a Marketplace/HACS integration.

The app runs as a container on Home Assistant OS. It accepts AirPrint jobs from iPhone/iPad and uses Linux ESC/P-R to drive a network-connected Epson ET-2500. It requires no always-on Mac.

## Install

1. Settings → Apps → App Store → menu → Repositories.
2. Add `https://github.com/rostyslav-khomyk/ha-airprint-bridge`.
3. Install **Epson AirPrint Bridge**. The first install builds the image locally.
4. Before starting, set `printer_uri` to `socket://YOUR_PRINTER_IP:9100`. Reserve that printer IP in your router.
5. Keep A4 paper loaded, start the app, and wait for **Ready** in its logs.
6. On your iPhone, use Share → Print → **Epson ET-2500 (HA)**.

Default options are A4, color, simplex, ET-2500 driver match and port 8631. ESC/P-R is bundled during the image build; no driver download URL or runtime driver package is needed. Set `debug_logging: true` temporarily for troubleshooting.

## Networking and access

- Host networking is required for LAN mDNS discovery. TCP 8631 must be free and reachable by your phone; UDP 5353 multicast must reach the same LAN.
- CUPS listens only on loopback TCP 631 and its local socket. Its web interface is off. Do not expose it remotely.
- IPP printing on 8631 is unauthenticated: deploy only on a trusted LAN, without Internet forwarding. The printer's port 9100 connection is also unencrypted.
- Home Assistant API access is enabled for app notifications and optional upstream status sensors. USB, host D-Bus, host share mapping, Docker API and privileged mode are not requested.
- Only one print app should own ports 631/8631 on the HA host.

## Persistence and limitations

Supervisor persists app options and `/data`, including TLS certificates and the gateway spool. CUPS queue definitions persist under `/data/cups-config`; job metadata persists under `/data/cups-spool`. Startup reapplies the configured printer options without deleting the queue. Do not make manual CUPS configuration changes expecting them to persist. Backup this app using Supervisor's normal app backup.

CUPS has a 50 MiB per-request limit and a 20-job limit; completed CUPS job documents are deleted; metadata for up to 20 jobs is retained for up to 24 hours. The separate IPP front end may retain failed spool documents under `/data/spool`; inspect/clear them when retiring the app. Gateway completion means CUPS accepted a job, not that paper emerged. Cancellation after handoff is not synchronized. This fork remains experimental and has not had a full security audit.

The ET-2500 model must exist in the bundled ESC/P-R package. The startup log prints the selected driver. Do not substitute a generic driver merely to make startup succeed. The ingress panel can read Epson status and waste counters on demand. Scanner support is not included.

## Validation

See [VALIDATION.md](VALIDATION.md) for actual deployment results. The earlier Mac PoC proved the physical printer path and iPhone discovery/printing; it used Apple's Epson driver and is not evidence that Linux ESC/P-R has printed until separately tested.

## Rollback

Stop **Epson AirPrint Bridge** in Settings → Apps. Disable Start on boot to keep it stopped. Your physical printer and other HA apps are unchanged. To remove it completely, uninstall this app, then remove this repository from the App Store. Uninstall removes the app's data; keep a Supervisor app backup first if you want its settings/certificates.

## Development

The image is built from the app's `Dockerfile` and architecture mapping in `build.yaml` (amd64 and aarch64). Driver packages come from Debian Bookworm repositories during build. This deployment is tested on amd64; aarch64 is inherited support until separately tested. Run `python3 -m unittest discover -s tests` for configuration checks. Supervisor builds the actual Linux image during installation.

MIT licensed. See [LICENSE](LICENSE), [UPSTREAM.md](UPSTREAM.md), and the preserved [upstream README](docs/UPSTREAM-README.md).

## Sidebar and maintenance (1.3.0)

Open the app's **Open Web UI** button or enable **Show in sidebar**. Home Assistant ingress authenticates access; only Supervisor's ingress peer is accepted on port 8098. This fixed port was checked on the deployment host; change it in both config and panel if it conflicts on another host. Supervisor watchdog probes the panel health endpoint, which checks CUPS, Avahi and the IPP front end. The main process also exits if the panel dies.

The panel shows queue state and bounded recent job history. Its explicit maintenance actions are nozzle check, normal head clean, experimental power clean, and waste-counter reset. Maintenance commands come from a pinned copy of Ircama's `epson_print_conf` and `epson-escp2==1.0.4`. Every maintenance request verifies the network printer identifies as ET-2500. Write actions require a typed confirmation and an empty print queue. No maintenance runs on install or startup.

**These maintenance writes are not yet hardware-validated in this deployment.** Sending a power-clean command is not evidence that it implements Epson's full Power Ink Flushing procedure. Follow [Epson's ET-2500 flushing instructions](https://epson.ca/faq/SPT_C11CE92201~faq-284698) for the official procedure. Service/replace the physical waste pads before resetting their counter. Reset snapshots the relevant EEPROM bytes and serial to `/data/maintenance`, then uses the upstream tool's verified writes; failures/partial writes must be reviewed before any retry. No automatic retry or automatic restoration is performed.

Maintenance toolkit source: [Ircama/epson_print_conf](https://github.com/Ircama/epson_print_conf/tree/2dc3bebacf314f22bd6484acdb2a7434c7cc00ad), EUPL-1.2. The source and license are included under `airprint_bridge/maintenance`, separately from the MIT print bridge. `worker.py` is EUPL-1.2. See also [Epson Linux utility capabilities](https://download.ebz.epson.net/man/linux/utility.html).

A false-valued option bug inherited from upstream (`jq // empty`) was fixed so disabled sensors stay disabled rather than attempting unauthorized API updates.

Version 1.3.3 resolves requests against the explicit HA ingress base path and separates results/errors for every maintenance control. A bounded 50-event maintenance activity log is kept in memory for the current app session.
