from __future__ import annotations

import logging
import sys


def configure_logging() -> None:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[console_handler], force=True)

