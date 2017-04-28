import time


def log(data: str, ltype: str = "log"):
    if ltype in ["ircin", "ircout", "log"]:
        if ltype == "ircin":
            print(time.asctime(), " : >>", data)
        elif ltype == "ircout":
            print(time.asctime(), " : <<", data)
        elif ltype == "log":
            print(time.asctime(), " : >!", data)
    else:
        raise ValueError("Unknown Log Type")


def logall(connection):
    log("---------------------------------------CHANNELS---------------------------------------")
    for channel in connection.channels:
        log(connection.channels[channel].name)
        for membership in connection.channels[channel].users:
            log("  `-" + connection.channels[channel].users[membership].user.mask)
    log("----------------------------------------USERS------------------------------------------")
    for user in connection.users:
        log(connection.users[user].mask)
        for channel in connection.users[user].channels:
            log("  `-" + channel)
