import time
import socket
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

def probe_http(url: str) -> float | None:
    try:
        http_start = time.perf_counter()
        res = urllib.request.urlopen(url, timeout=10)
        res.read(1)
        http_end = time.perf_counter()
        return (http_end - http_start) * 1000
    except urllib.error.URLError as e:
        logger.exception("Unexpected urllib error during HTTP probe for URL=%s: %s", url, e)
        return None
    except socket.timeout as e:
        logger.exception("Unexpected socket error during HTTP probe for URL=%s: %s", url, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error during HTTP probe for URL=%s: %s", url, e)
        return None