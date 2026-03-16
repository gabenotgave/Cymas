import netifaces
import logging

logger = logging.getLogger(__name__)

def get_default_gateway_netifaces() -> str | None:
    try:
        # Get all gateways
        gateways = netifaces.gateways()

        if not gateways:
            logger.error("No gateway information was returned by netifaces.")
            return None

        # Extract the default gateway for IPv4 (AF_INET)
        default_info = gateways.get('default')
        if not default_info:
            logger.error("No default gateway was found.")
            return None

        default_gateway_info = default_info.get(netifaces.AF_INET)
        if not default_gateway_info:
            logger.error("No default IPv4 gateway was found.")
            return None

        gateway_ip = default_gateway_info[0]
        if not gateway_ip:
            logger.error("Default gateway record did not include an IP address.")
            return None

        return gateway_ip
    except (KeyError, IndexError, TypeError) as e:
        logger.exception("Failed to parse gateway information: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error while reading gateway information: %s", e)
        return None