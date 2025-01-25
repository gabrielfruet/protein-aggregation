from datetime import datetime
import logging
import logging.config
from pathlib import Path
from typing import Union

class ExcludePyrosettaFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> Union[bool,logging.LogRecord]:
        return 'pyrosetta' not in record.name 

LOG_DIR = Path('./log')

# Logging configuration using dictConfig
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'exclude_pyrosetta': {
            '()': ExcludePyrosettaFilter,
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filters': ['exclude_pyrosetta'],
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filters': ['exclude_pyrosetta'],
            'filename': LOG_DIR/datetime.now().strftime('%d-%m-%Y-%H-%M-%S.log'),
            'mode': 'w',
        },
    },
    'loggers': {
        '': {  # Root logger
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        },
    },
}


# Apply the logging configuration
def config_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
