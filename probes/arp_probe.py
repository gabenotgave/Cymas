import subprocess
import logging

logger = logging.getLogger(__name__)

def get_active_device_count() -> int | None:
    """
    Returns the number of active devices on the local network by parsing the ARP cache.
    Returns None if the command fails to execute or parse.
    """
    try:
        # Run arp -a -n to get the raw ARP table without hostname resolution
        result = subprocess.run(
            ['arp', '-a', '-n'],
            capture_output=True,
            text=True,
            check=True
        )

        active_count = 0

        # Parse the output line by line
        for line in result.stdout.splitlines():
            # A valid, resolved entry has an IP in parentheses and is not marked incomplete
            if "(" in line and "(incomplete)" not in line:
                active_count += 1

        return active_count

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.exception("ARP probe failed: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error in ARP probe: %s", e)
        return None