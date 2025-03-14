# config/logging_config.py

from typing import Dict, Any

LOGGING_CONFIG: Dict[str, Any] = {
    "VERSION": 1,
    "DISABLE_EXISTING_LOGGERS": False,
    "FORMATTERS": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "simple": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "HANDLERS": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filename": "logs/orthocfd.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "LOGGERS": {
        "OrthoCFD": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "ROOT": {
        "level": "INFO",
        "handlers": ["console"]
    }
}

