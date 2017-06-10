from logger import *

# TODO: for masshl, channel notice checking too


def printlog(connection, **kwargs):
    logcentered("MODES", connection=connection)
    log("A: " + str(connection.Amodes))
    log("B: " + str(connection.Bmodes))
    log("C: " + str(connection.Cmodes))
    log("D: " + str(connection.Dmodes))
    log("P: " + str(connection.Pmodes))


def die(connection, **kwargs):
    connection.quit("Controller requested disconnect")


def nickl(connection, channel, **kwargs):
    logcentered("nicks", connection=connection)
    for nick in channel.nicklist:
        print(nick)


def stop(connection, **kwargs):
    connection.bot.stop("Controller requested disconnect")


def join(connection, cmdargs, **kwargs):
    connection.join(cmdargs)


def part(connection, cmdargs, **kwargs):
    connection.part(cmdargs)

commands = {
    "die": die,
    "print": printlog,
    "nickl": nickl,
    "stop": stop,
    "join": join,
    "part": part
}


def on_command(connection, args, prefix):
    temp = args[1][1:].split(None, 1)
    command = temp.pop(0)
    cmdargs = ""
    if temp:
        cmdargs = temp.pop(0)

    if command in commands:
        channel = connection.channels.get(args[0])
        commands[command](connection=connection,
                          channel=channel,
                          cmdargs=cmdargs)

