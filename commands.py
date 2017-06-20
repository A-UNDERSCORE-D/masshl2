import inspect

from logger import *

# TODO: for masshl, channel notice checking too

COMMANDS = {}


def command(*cmds):
    def _decorate(func):
        for cmd in cmds:
            assert cmd not in COMMANDS
            COMMANDS[cmd] = func
        return func
    return _decorate


@command("print")
def printlog(connection):
    logcentered("MODES", connection=connection)
    log("A: " + str(connection.Amodes))
    log("B: " + str(connection.Bmodes))
    log("C: " + str(connection.Cmodes))
    log("D: " + str(connection.Dmodes))
    log("P: " + str(connection.Pmodes))


@command("die")
def die(connection):
    connection.quit("Controller requested disconnect")


@command("nickl")
def nickl(connection, channel):
    logcentered("nicks", connection=connection)
    for nick in channel.users.keys():
        print(nick)


@command("stop")
def stop(connection):
    connection.bot.stop("Controller requested disconnect")


@command("join")
def join(connection, cmdargs):
    connection.join(cmdargs)


@command("part")
def part(connection, cmdargs):
    connection.part(cmdargs)


def on_command(connection, args, prefix):
    temp = args[1][1:].split(None, 1)
    command = temp.pop(0)
    cmdargs = ""
    if temp:
        cmdargs = temp.pop(0)

    handler = COMMANDS.get(command)
    if handler:
        sig = inspect.signature(handler)
        channel = connection.channels.get(args[0])
        data = {
            "connection": connection,
            "channel": channel,
            "cmdargs": cmdargs,
        }
        args = [data[arg] for arg in sig.parameters.keys()]
        handler(*args)

