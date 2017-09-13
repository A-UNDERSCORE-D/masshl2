import time
import sys
import logging
import logging.config

# TODO: Use logging or look into it


class Logger:
    # Logger object also known as LogJect -linuxdaemon
    def __init__(self, conn):
        self._ircin_logger = logging.getLogger("ircin")
        self._ircout_logger = logging.getLogger("ircout")
        self._def_logger = logging.getLogger("default")
        self.conn = conn.name

    def ircin(self, message):
        self._ircin_logger.info(self.format(message))

    def ircout(self, message):
        self._ircout_logger.info(self.format(message))

    def info(self, message):
        self._def_logger.info(self.format(message))

    def debug(self, message):
        self._def_logger.debug(self.format(message))

    def error(self, message):
        self._def_logger.error(self.format(message))

    def exception(self, exception):
        self._def_logger.exception(exception)

    def format(self, message):
        return f"[{self.conn:^10}] {message}"

    def __call__(self, msg):
        self.info(msg)


def setup():
    config = {
        "version": 1,
        "formatters": {
            "ircin": {
                "format": "{asctime} [IRCIN ] {message}",
                "style": "{",
                "datefmt": "%H:%M:%S"
            },
            "ircout": {
                "format": "{asctime} [IRCOUT] {message}",
                "style": "{",
                "datefmt": "%H:%M:%S"
            },
            "default": {
                "format": "{asctime} [{levelname:<6}] {message}",
                "style": "{",
                "datefmt": "%H:%M:%S"
            }
        },

        "handlers": {
            "ircin": {
                "class": "logging.StreamHandler",
                "formatter": "ircin",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            },
            "ircout": {
                "class": "logging.StreamHandler",
                "formatter": "ircout",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            },
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "ircin": {
                "level": "INFO",
                "handlers": ["ircin"]
            },
            "ircout": {
                "level": "INFO",
                "handlers": ["ircout"]
            },
            "default": {
                "level": "DEBUG",
                "handlers": ["default"]
            }
        }
    }
    logging.config.dictConfig(config)


setup()


def logall(connection):
    connection.log(centered("CHANNELS"))
    for channel in connection.channels:
        connection.log.debug(connection.channels[channel].name)
        for membership in connection.channels[channel].memberships:
            connection.log.debug("  `-" + connection.channels[channel].memberships[membership].user.mask)

    connection.log(centered("USERS"))
    for user in connection.users:
        connection.log.debug(connection.users[user].mask)
        for channel in connection.users[user].memberships:
            connection.log.debug("  `-" + channel)


def logchan(channel):
    channel.connection.log(centered(f"USERS-ON-{channel.name}"))
    channel.connection.log.debug(channel.name)
    for user in channel.memberships:
        usero = channel.memberships[user]
        prefix = usero.prefix()
        channel.connection.log.debug(" `-" + prefix + user,)


def centered(msg):
    return f"{msg:-^65}"
