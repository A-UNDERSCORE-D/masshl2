import base64
from sys import exc_info

import parser
from channel import Channel
from logger import *

# TODO: CTCP responses

HANDLERS = {}


def raw(*cmds):
    def _decorate(func):
        for cmd in cmds:
            HANDLERS.setdefault(cmd.upper(), []).append(func)
        return func

    return _decorate


def handler(connection, prefix, tags, command, args):
    data = {
        "connection": connection,
        "prefix": prefix,
        "tags": tags,
        "command": command,
        "args": args,
    }
    for func in HANDLERS.get(command, []):
        connection.bot.launch_hook(func, **data)


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
    caps = args[1].split("=")
    command = caps[0]
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
    connection.log("SASL login failed, attempting PRIVMSG based login")
    connection.cansasl = False


@raw("001")
def onwelcome(connection, prefix):
    connection.server = prefix


@raw("005")
def onisupport(connection, args):
    tokens = args[1:-1]
    for token in tokens:
        if "=" in token:
            token_name, _, args = token.partition("=")
            args = args or None
        else:
            token_name = token

        if token_name == "NETWORK":
            connection.networkname = token.split("=")[1]

        elif token_name == "PREFIX":
            pfx = token.split("=")[1]
            pfx, modes = pfx.split(")", 1)
            pfx = pfx[1:]
            connection.p_mode_d = dict(zip(pfx, modes))
            connection.p_modes.update(pfx)

        elif token_name == "CHANMODES":
            modes = token.split("=")[1]
            a, b, c, d = modes.split(",")
            connection.a_modes.update(a)
            connection.b_modes.update(b)
            connection.c_modes.update(c)
            connection.d_modes.update(d)

        elif token_name == "EXCEPTS":
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.banexept.add(mode)

        elif token_name == "INVEX":
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.invex.add(mode)

        elif token_name == "CHANTYPES":
            connection.chantypes = list(args)


@raw("376")
def onendmotd(connection):
    if not connection.cansasl:
        identify(connection)
    for command in connection.commands:
        connection.write(command)
    connection.join(connection._adminchan)
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
        # TODO: un-hardcode this
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

        temp = connection.get_user(mask)
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

    user = connection.get_user(prefix)

    if nick not in chan.memberships:
        chan.adduser(connection, user)
    logall(connection)


def hook_message(func):
    setattr(func, "_isMessageCallback", None)
    return func


@raw("PRIVMSG")
def onprivmsg(connection, args, prefix):
    msg = parser.Message(connection, args, prefix, "PRIVMSG")
    on_msg(msg, connection)


@raw("NOTICE")
def onnotice(connection, args, prefix):
    msg = parser.Message(connection, args, prefix, "NOTICE")
    on_msg(msg, connection)


def on_msg(msg, conn):
    todo = []
    for plugin in msg.conn.bot.message_hooks:
        for func in msg.conn.bot.message_hooks[plugin]:
            try:
                res = conn.bot.launch_hook(func, msg=msg)
            except Exception as e:
                conn.log.exception(e)
                ex_type, ex_info, ex_trace = exc_info()
                msg.target.send_message(f"{func.__name__} in {func.__module__} just broke. Who wrote it? "
                                        f"I want their head. Exception: {ex_type.__name__}: {ex_info}. "
                                        f"see stdout for trace")
            else:
                if res:
                    todo.append(res)
    for res in todo:
        if callable(res):
            res()
        else:
            msg.target.send_message(str(res))


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
        elif mode in connection.a_modes or mode in connection.b_modes:
            count += 1
        elif mode in connection.c_modes:
            if adding:
                count += 1
        elif mode in connection.d_modes:
            pass
        elif mode in connection.p_modes:
            nick = modeargs[count]
            connection.log(str(("+" if adding else "-") + mode + " " + nick))
            membership = chan.memberships[nick]
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


@raw("PART")
def onpart(connection, prefix, args):
    chan_name = args[0]
    try:
        chan = connection.channels[chan_name]
    except KeyError:
        connection.log("WTF? I just got a part for a channel I don't have, channel was {c}".format(c=chan_name))
        logall(connection)
        return

    nick = prefix.split("!")[0]
    try:
        user = chan.get_user(nick)
    except KeyError:
        connection.log("Received part for non-existent user '{}' from channel '{}'".format(nick, chan.name))
        return

    if user.nick == connection.nick:
        del connection.channels[chan.name]
        connection.log(connection.channels)
    else:
        chan.deluser(user)
    logall(connection)


@raw("KICK")
def onkick(connection, args):
    knick = args[1]
    kchan = args[0]

    try:
        user = connection.users[knick]
    except KeyError:
        connection.log("Handling kick for non-existent user")
        return

    try:
        chan = connection.channels[kchan]
    except KeyError:
        connection.log("Handling kick from non-existent channel")
        return

    if user.nick == connection.nick:
        connection.log("We were kicked from {}".format(kchan))
        del connection.channels[kchan]
        connection.log(connection.channels)
    else:
        chan.deluser(user)
    logall(connection)


@raw("NICK")
def onnick(connection, prefix, args):
    if not prefix:
        raise ValueError
    onick = prefix.split("!")[0]
    nnick = args[0]
    if onick == connection.nick:
        connection.nick = nnick
    try:
        user = connection.users[onick]
    except KeyError:
        connection.log("Attempted to renick a non-existent user")
        return
    user.renick(nnick)
    logall(connection)


@raw("QUIT")
def onquit(connection, prefix):
    nick = prefix.split("!")[0]
    try:
        user = connection.users[nick]
    except KeyError:
        connection.log("Received quit from non-existent user '{}'".format(prefix))
        return

    connection.del_user(user)
