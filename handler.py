import base64
import inspect

from logger import *
from user import User
from channel import Channel
from commands import on_command

# TODO: CTCP responses
# TODO: on nick function

HANDLERS = {}


def raw(*cmds):
    def _decorate(func):
        for cmd in cmds:
            HANDLERS.setdefault(cmd.upper(), []).append(func)
        return func

    return _decorate


def handler(connection, prefix, command, args):
    data = {
        "connection": connection,
        "prefix": prefix,
        "command": command,
        "args": args,
    }
    for func in HANDLERS.get(command, []):
        _internal_launch(func, data)


def _internal_launch(func, data):
    sig = inspect.signature(func)
    params = []
    for arg in sig.parameters.keys():
        assert arg in data
        params.append(data[arg])
    func(*params)


def identify(connection):
    connection.write("PRIVMSG NickServ :IDENTIFY {nsnick} {nspass}".format(
        nsnick=connection.nsuser, nspass=connection.nspass
    ))


@raw("PING")
def onping(connection, args):
    connection.write("PONG :" + " ".join(args))


@raw("AUTHENTICATE")
def sendauth(connection):
    auth_string = (connection.nick + "\00" + connection.nsuser + "\00"
                   + connection.nspass).encode()

    connection.write("AUTHENTICATE {}".format(
        base64.b64encode(auth_string).decode())
    )


@raw("CAP")
def handlecap(connection, args):
    command = args[1]
    if command == "LS":
        caplist = args[-1].split()
        caps = connection.caps.intersection(caplist)
        if len(caps) == 0:
            connection.write("CAP END")

        else:
            for cap in caps:
                connection.write("CAP REQ :{}".format(cap))
                capincrement(connection)

    elif command == "ACK":
        cap = args[2]
        if cap == "sasl":
            connection.cansasl = True
            capincrement(connection)
            connection.write("AUTHENTICATE PLAIN")
        elif cap == "userhost-in-names":
            connection.uhnames = True

        capdecrement(connection)

    elif command == "NAK":
        cap = args[2]
        capdecrement(connection)
        if cap == "userhost-in-names":
            connection.uhnames = False
        elif cap == "sasl":
            connection.cansasl = False


def capincrement(connection):
    connection.capcount += 1


def capdecrement(connection):
    connection.capcount -= 1
    if connection.capcount <= 0:
        connection.write("CAP END")


@raw("903")
def goodsasl(connection):
    capdecrement(connection)


@raw("904")
def badsasl(connection):
    capdecrement(connection)
    log("SASL login failed, attempting PRIVMSG based login", connection=connection)
    connection.cansasl = False


@raw("005")
def onisupport(connection, args):
    tokens = args[1:-1]
    for token in tokens:
        if "NETWORK" in token:
            connection.networkname = token.split("=")[1]

        elif "PREFIX" in token:
            pfx = token.split("=")[1]
            pfx, modes = pfx.split(")", 1)
            pfx = pfx[1:]
            connection.p_mode_d = dict(zip(pfx, modes))
            connection.p_modes.update(pfx)

        elif "CHANMODES" in token:
            modes = token.split("=")[1]
            a, b, c, d = modes.split(",")
            connection.a_modes.update(a)
            connection.b_modes.update(b)
            connection.c_modes.update(c)
            connection.d_modes.update(d)

        elif "EXCEPTS" in token:
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.banexept.add(mode)

        elif "INVEX" in token:
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.invex.add(mode)


@raw("376")
def onendmotd(connection):
    if not connection.cansasl:
        identify(connection)
    for command in connection.commands:
        connection.write(command)
    connection.join(connection.adminchan)
    connection.join(connection.joinchannels)


@raw("353")
def onnames(connection, args):
    names = args[3].split()
    chan: Channel = connection.channels[args[2]]

    # clear out the current user list
    if not chan.receivingnames:
        chan.receivingnames = True
        chan.memberships.clear()

    for mask in names:
        mask = mask.strip()
        admin, op, hop, voice = False, False, False, False
        if mask[0] in "!@%+":
            prefix = mask[0]
            mask = mask[1:]
            if prefix == "!":
                admin = True
            elif prefix == "@":
                op = True
            elif prefix == "%":
                hop = True
            elif prefix == "+":
                voice = True
        temp = User.add(connection, mask)

        chan.adduser(connection, temp, isop=op, ishop=hop,
                     isvoice=voice, isadmin=admin)


@raw("366")
def onnamesend(connection, args):
    chan = connection.channels[args[1]]
    chan.receivingnames = False
    logchan(chan)


@raw("JOIN")
def onjoin(connection, prefix, args):
    name = args[0]
    chan = connection.channels.get(args[0])
    nick = prefix.split("!")[0]
    if not chan:
        chan = Channel(name, connection)
        connection.channels[name] = chan

    try:
        user = connection.users[nick]
    except KeyError:
        user = User.add(connection, prefix)

    if nick not in chan.memberships:
        chan.adduser(connection, user)
    logall(connection)


@raw("PRIVMSG")
def onprivmsg(connection, args, prefix):
    if args[1].startswith(connection.cmdprefix):
        on_command(connection, args, prefix)


@raw("MODE")
def onmode(connection, args):
    target = args[0]
    modes = args[1]
    modeargs = args[2:]
    adding = True
    count = 0
    if target == connection.nick:
        return
    chan = connection.channels[target]
    for mode in modes:
        if mode == "+":
            adding = True
            continue
        elif mode == "-":
            adding = False
            continue
        elif mode in connection.a_modes:
            count += 1
        elif mode in connection.b_modes:
            count += 1
        elif mode in connection.c_modes:
            if adding:
                count += 1
        elif mode in connection.d_modes:
            pass
        elif mode in connection.p_modes:
            nick = modeargs[count]
            log(str(("+" if adding else "-") + mode + " " + nick))
            membership = chan.users[nick]

            if mode == "o":
                membership.isop = adding
            elif mode == "h":
                membership.ishop = adding
            elif mode == "v":
                membership.isvoice = adding
            elif mode == "Y":
                membership.isadmin = adding
            count += 1
            logchan(chan)


# TODO: Deal with parts/kicks for myself


@raw("PART")
def onpart(connection, prefix, args):
    chan: Channel = connection.channels.get(args[0])
    user: User = connection.users.get(prefix.split("!")[0])
    if not chan:
        log("WTF? I just got a part for a channel I dont have, "
            "channel was {c}".format(c=args))
        logall(connection)
        return

    if user.nick == connection.nick:
        del connection.channels[chan.name]
        log(connection.channels)
    else:
        chan.deluser(user)
    logall(connection)


@raw("KICK")
def onkick(connection, args):
    knick = args[1]
    kchan = args[0]
    user = connection.users.get(knick, None)
    chan = connection.channels.get(kchan, None)
    if user and chan:
        if user.nick == connection.nick:
            log("We were kicked from {}".format(kchan), connection=connection)
            del connection.channels[kchan]
            log(connection.channels)
        else:
            chan.deluser(connection, user)
    logall(connection)


@raw("NICK")
def onnick(connection, prefix, args):
    if not prefix:
        raise ValueError
    onick = prefix.split("!")[0]
    nnick = args[0]
    if onick == connection.nick:
        connection.nick = nnick
    user = connection.users.get(onick)
    user.renick(nnick)
    logall(connection)
