import logging
from datetime import datetime
import time

from probes.gateway import get_default_gateway_netifaces
from probes.arp_probe import get_active_device_count
from probes.dns_probe import ping_dns
from probes.http_probe import probe_http
from probes.ping_probe import ping_host
from probes.wifi_probe import get_wifi_stats
from probes import config
from data_io.writer import write_data

def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

def main() -> None:
    print("LANtern initiated.")
    gateway_addr = get_default_gateway_netifaces()

    try:
        while True:
            active_device_count = get_active_device_count()
            dns_probe_rtt = ping_dns(config.DNS_TEST_HOST)
            http_probe_rtt = probe_http(config.HTTP_TEST_HOST)
            ping_ext = ping_host(config.EXTERNAL_PING_HOST, config.PING_COUNT)
            ping_gw = ping_host(gateway_addr, config.PING_COUNT)
            wifi_stats = get_wifi_stats()

            # Build the row dict
            data = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "gateway_ip": gateway_addr,
                "device_count": active_device_count,
                "ping_gateway_avg_ms": ping_gw[0] if ping_gw else None,
                "ping_gateway_loss_pct": ping_gw[1] if ping_gw else None,
                "ping_external_avg_ms": ping_ext[0] if ping_ext else None,
                "ping_external_loss_pct": ping_ext[1] if ping_ext else None,
                "dns_resolution_ms": dns_probe_rtt,
                "http_ttfb_ms": http_probe_rtt,
                "wifi_ssid": wifi_stats.get("ssid"),
                "wifi_rssi_dbm": wifi_stats.get("rssi_dbm"),
                "wifi_noise_dbm": wifi_stats.get("noise_dbm"),
                "wifi_snr_db": wifi_stats.get("snr_db"),
                "wifi_channel": wifi_stats.get("channel"),
                "wifi_tx_rate_mbps": wifi_stats.get("tx_rate_mbps"),
            }

            # Write data to CSV file
            write_data(data, config.CSV_PATH)

            print("LANtern record logged.")

            time.sleep(config.INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("LANtern exiting gracefully.")

if __name__ == "__main__":
    configure_logging()
    main()