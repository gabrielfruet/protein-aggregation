import logging
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Union


class ExcludePyrosettaFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> Union[bool, logging.LogRecord]:
        return "src" in record.name


LOG_DIR = Path("./log")

if not LOG_DIR.exists():
    res = input("Do you wish to create a log dir in ./log?")
    if res.upper() in ["Y", "YES", "SIM", "S"]:
        LOG_DIR.mkdir()
    else:
        print("Not creating dir")
        exit(1)

# Logging configuration using dictConfig
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "exclude_pyrosetta": {
            "()": ExcludePyrosettaFilter,
        },
    },
    "formatters": {
        "default": {
            "format": "%(levelname)s - %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filters": ["exclude_pyrosetta"],
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filters": ["exclude_pyrosetta"],
            "filename": LOG_DIR / datetime.now().strftime("%d-%m-%Y-%H-%M-%S.log"),
            "mode": "w",
        },
    },
    "loggers": {
        "": {  # Root logger
            "level": "INFO",
            "handlers": ["file"],
        },
    },
}


# Apply the logging configuration
def config_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
