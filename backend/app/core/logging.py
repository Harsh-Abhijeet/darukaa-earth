"""Structured logging for Darukaa.Earth."""

import logging
import sys

def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Quiet overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger("darukaa_earth")

logger = setup_logging()
