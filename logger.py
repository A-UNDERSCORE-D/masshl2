import time
import sys
import logging

# TODO: Use logging or look into it


class Logger:
    def __init__(self, conn):
        self._ircin_logger = logging.getLogger("ircin")
        self._ircout_logger = logging.getLogger("ircout")
        self._def_logger = logging.getLogger("def")
        self.conn = conn.name

    def ircin(self, message):
        self._ircin_logger.info(self.format(message))

    def ircout(self, message):
        self._ircout_logger.info(self.format(message))

    def info(self, message):
        print("called")
        self._def_logger.info(self.format(message))

    def format(self, message):
        print("formatting")
        return f"[{self.conn:^10}] {message}"


def log(data: str, ltype: str = "log", connection=None):
    if ltype.lower() in ["ircin", "ircout", "log", "error"]:
        curtime = time.strftime('%H:%M:%S')
        if connection:
            net = connection.name
        else:
            net = ""

        if ltype.lower() == "ircin":
            print(f"{curtime} : [{net:^10}] >> {data}")

        elif ltype.lower() == "ircout":
            print(f"{curtime} : [{net:^10}] << {data}")

        elif ltype.lower() == "log":
            print(f"{curtime} : [{net:^10}] >! {data}")

        elif ltype.lower() == "error":
            print(f"{curtime} : [{net:^10}] !! {data}", file=sys.stderr)
    else:
        raise ValueError("Unknown Log Type")


def logall(connection):
    logcentered("CHANNELS", connection=connection)
    for channel in connection.channels:
        log(connection.channels[channel].name, connection=connection)
        for membership in connection.channels[channel].memberships:
            log("  `-" +
                connection.channels[channel].memberships[membership].user.mask,
                connection=connection)

        logcentered("USERS", connection=connection)
    for user in connection.users:
        log(connection.users[user].mask, connection=connection)
        for channel in connection.users[user].memberships:
            log("  `-" + channel, connection=connection)


def logchan(channel):
    logcentered("USERS-ON-{}".format(channel.name), channel.connection)
    log(channel.name, connection=channel.connection)
    for user in channel.memberships:
        usero = channel.memberships[user]
        prefix = usero.prefix()
        log(" `-" + prefix + user, connection=channel.connection)


def logcentered(msg, connection=None):
    log("{:-^65}".format(msg), connection=connection)
