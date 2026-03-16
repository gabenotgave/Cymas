import os
import csv

FIELDNAMES = [
    # Metadata
    "timestamp",              # ISO 8601 — anchor for all time-series analysis
    "gateway_ip",             # logged once but useful if the router IP ever changes

    # Device count
    "device_count",           # ARP active device count — your primary independent variable

    # Ping: local
    "ping_gateway_avg_ms",    # isolates LAN/WiFi congestion from WAN issues
    "ping_gateway_loss_pct",  # packet loss to gateway — even 1% is significant

    # Ping: external
    "ping_external_avg_ms",   # isolates ISP-side issues from local issues
    "ping_external_loss_pct", # external packet loss — points to FastBridge if high

    # DNS
    "dns_resolution_ms",      # hidden bottleneck; high here = router DNS choking

    # HTTP
    "http_ttfb_ms",           # best single proxy for perceived slowness

    # WiFi radio
    "wifi_ssid",              # sanity check — flags if device roamed to wrong band
    "wifi_rssi_dbm",          # signal strength; should be above -70 dBm
    "wifi_noise_dbm",         # noise floor; context for interpreting RSSI
    "wifi_snr_db",            # derived: rssi - noise; <25 dB causes retransmissions
    "wifi_channel",           # detects channel congestion patterns over time
    "wifi_tx_rate_mbps",      # drops sharply when radio is struggling
]

def write_data(data: dict, csv_path: str) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)