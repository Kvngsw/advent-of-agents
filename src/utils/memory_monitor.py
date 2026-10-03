"""Low-RAM memory watchdog and RSS memory monitor."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_rss_memory_mb() -> float:
    """Retrieve the current process Resident Set Size (RSS) memory in megabytes.

    Returns:
        Current RSS memory usage in MB.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_bytes = process.memory_info().rss
        mem_mb = mem_bytes / (1024 * 1024)
        
        # Warn if memory exceeds the strict 384 MiB constraint
        if mem_mb > 384.0:
            logger.warning(
                f"Memory usage warning: Current RSS is {mem_mb:.2f} MB, exceeding the 384 MB constraint!"
            )
        return mem_mb
    except ImportError:
        # Fallback if psutil is not installed
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return float(parts[1]) / 1024.0
        except Exception:
            pass
        return 0.0
