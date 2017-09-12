import logging
import logging.config


def setup():
    CONFIG = {
        "version": 1,
        "formatters": {
            "ircin": {
                "format": "{asctime} [IRCIN      ] {message}"
            },
            "ircout": {
                "format": "{asctime} [IRCOUT     ] {message}"
            },
            "default": {
                "format": "{asctime} [{levelname:<10}] {message}"
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "ircout",
                "level": "INFO",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "ircin": {
                "level": "INFO",
                "formatter": "ircin",
                "handlers": "console"
            },
            "ircout": {
                "level": "INFO",
                "formatter": "ircout",
                "handlers": "console"
            },
            "def": {
                "level": "INFO",
                "formatter": "default",
                "handlers": "console"
            }
        }
    }
    logging.config.dictConfig(CONFIG)


setup()
