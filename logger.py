import time
import sys


def log(data: str, ltype: str = "log"):
    if ltype.lower() in ["ircin", "ircout", "log", "err"]:
        if ltype.lower() == "ircin":
            print(time.asctime(), " : >>", data)
        elif ltype.lower() == "ircout":
            print(time.asctime(), " : <<", data)
        elif ltype.lower() == "log":
            print(time.asctime(), " : >!", data)
        elif ltype.lower() == "err":
            print(time.asctime(), " : !!", data, file=sys.stderr)
    else:
        raise ValueError("Unknown Log Type")


def logall(connection):
    log("-----------------------------CHANNELS----------------------------")
    for channel in connection.channels:
        log(connection.channels[channel].name)
        for membership in connection.channels[channel].users:
            log("  `-" +
                connection.channels[channel].users[membership].user.mask)

    log("-----------------------------USERS-------------------------------")
    for user in connection.users:
        log(connection.users[user].mask)
        for channel in connection.users[user].channels:
            log("  `-" + channel)
