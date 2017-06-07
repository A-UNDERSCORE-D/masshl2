import time
import sys


def log(data: str, ltype: str = "log"):
    if ltype.lower() in ["ircin", "ircout", "log", "error"]:
        if ltype.lower() == "ircin":
            print(time.asctime(), " : >>", data)
        elif ltype.lower() == "ircout":
            print(time.asctime(), " : <<", data)
        elif ltype.lower() == "log":
            print(time.asctime(), " : >!", data)
        elif ltype.lower() == "error":
            print(time.asctime(), " : !!", data, file=sys.stderr)
    else:
        raise ValueError("Unknown Log Type")


def logall(connection):
    logcentered("CHANNELS")
    for channel in connection.channels:
        log(connection.channels[channel].name)
        for membership in connection.channels[channel].users:
            log("  `-" +
                connection.channels[channel].users[membership].user.mask)

        logcentered("USERS")
    for user in connection.users:
        log(connection.users[user].mask)
        for channel in connection.users[user].channels:
            log("  `-" + channel)


def logchan(channel):
    logcentered("USERS-ON-{}".format(channel.name))
    log(channel.name)
    for user in channel.users:
        usero = channel.users[user]
        prefix = usero.prefix()
        log(" `-" + prefix + user)


def logcentered(msg):
    log("{:-^65}".format(msg))
