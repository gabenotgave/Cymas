import socket
import time
import logging

logger = logging.getLogger(__name__)

def ping_dns(host: str) -> float | None:
    try:
        dns_start = time.perf_counter()
        socket.gethostbyname(host)
        dns_end = time.perf_counter()
        return (dns_end - dns_start) * 1000
    except Exception as e:
        logger.exception("Unexpected error during DNS resolution for host=%s: %s", host, e)
        return None