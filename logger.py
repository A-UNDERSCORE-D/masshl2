import time
import sys


# TODO: Use logging or look into it


def log(data: str, ltype: str = "log", connection=None):
    if ltype.lower() in ["ircin", "ircout", "log", "error"]:
        curtime = time.strftime('%H:%M:%S')
        if connection:
            net = "{:^10}".format(connection.name)
        else:
            net = "{:^10}".format("")

        if ltype.lower() == "ircin":
            print(f"{curtime} : [{net}] >> {data}")

        elif ltype.lower() == "ircout":
            print(f"{curtime} : [{net}] << {data}")

        elif ltype.lower() == "log":
            print(f"{curtime} : [{net}] >! {data}")

        elif ltype.lower() == "error":
            print(f"{curtime} : [{net}] !! {data}", file=sys.stderr)
    else:
        raise ValueError("Unknown Log Type")


def logall(connection):
    logcentered("CHANNELS", connection=connection)
    for channel in connection.channels:
        log(connection.channels[channel].name, connection=connection)
        for membership in connection.channels[channel].users:
            log("  `-" +
                connection.channels[channel].users[membership].user.mask,
                connection=connection)

        logcentered("USERS", connection=connection)
    for user in connection.users:
        log(connection.users[user].mask, connection=connection)
        for channel in connection.users[user].channels:
            log("  `-" + channel, connection=connection)


def logchan(channel):
    logcentered("USERS-ON-{}".format(channel.name), channel.connection)
    log(channel.name, connection=channel.connection)
    for user in channel.users:
        usero = channel.users[user]
        prefix = usero.prefix()
        log(" `-" + prefix + user, connection=channel.connection)


def logcentered(msg, connection=None):
    log("{:-^65}".format(msg), connection=connection)
