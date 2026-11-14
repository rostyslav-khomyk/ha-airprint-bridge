ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

# CUPS (the print engine), ippeveprinter (the AirPrint front end, in
# cups-ipp-utils), Avahi (network announcements), filters, and common
# libraries vendor drivers expect. Printer drivers themselves are installed
# at startup from the add-on options; vendor drivers are never bundled.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cups cups-client cups-bsd cups-filters cups-ipp-utils printer-driver-escpr \
        avahi-daemon avahi-utils libnss-mdns dbus \
        ghostscript poppler-utils python3 python3-cups python3-venv \
        libxml2 libjbig0 libglib2.0-0 libgtk2.0-0 libcups2 libcupsimage2 \
        curl ca-certificates jq tar gzip unzip procps iproute2 gawk snmp usbutils \
    && rm -rf /var/lib/apt/lists/*

COPY maintenance /opt/epson-maintenance
RUN python3 -m venv /opt/maintenance-venv \
    && /opt/maintenance-venv/bin/pip install --no-cache-dir \
       pysnmp==7.1.32 pysnmp-sync-adapter==1.1.0 pyprintlpr==1.1.1 \
       epson-escp2==1.0.4 PyYAML==6.0.3
COPY panel.py panel.html /opt/panel/
COPY cupsd.conf /etc/cups/cupsd.conf
COPY cupsd.conf /opt/default-cupsd.conf
COPY avahi-daemon.conf /etc/avahi/avahi-daemon.conf
COPY trim_ppd.awk /trim_ppd.awk
COPY run.sh install_driver.sh discover.sh notify.sh status.sh print_job.sh make_attrs.sh /
RUN chmod a+x /run.sh /install_driver.sh /discover.sh /notify.sh /status.sh /print_job.sh /make_attrs.sh

CMD [ "/run.sh" ]
