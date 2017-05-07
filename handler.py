import base64

from logger import *
from user import User
from channel import Channel
from commands import commands


def handler(connection, prefix, command, args):
    if command == "PING":
        connection.write("PONG :" + " ".join(args))
    elif command == "JOIN":
        onjoin(connection, prefix, args)
    elif command == "PART":
        onpart(connection, prefix, args)
    elif command == "KICK":
        onkick(connection, args)
    elif command == "PRIVMSG":
        onprivmsg(connection, args, prefix)
    elif command == "MODE":
        onmode(connection, args)

    elif command == "CAP":
        handlecap(connection, args)
    elif command == "AUTHENTICATE":
        sendauth(connection)

    elif command == "376":
        onendmotd(connection)
    elif command == "005":
        onisupport(connection, args)
    elif command == "353":
        onnames(connection, args)
    elif command == "366":
        onnamesend(connection, args)
    elif command == "904" or command == "903":
        capdecrement(connection)


def sendauth(connection):
    connection.write("AUTHENTICATE {}".format(base64.b64encode(
        (connection.nick + "\00" + connection.nsuser + "\00" +
         connection.nspass).encode()).decode()))


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


def onendmotd(connection):
    if not connection.cansasl:
        identify(connection)
    for command in connection.commands:
        connection.write(command)
    chans = ",".join(connection.joinchannels)
    connection.write("JOIN " + chans)


def identify(connection):
    connection.write("PRIVMSG NickServ :IDENTIFY {nsnick} {nspass}".format(
        nsnick=connection.nsuser, nspass=connection.nspass
    ))


def onprivmsg(connection, args, prefix):
    commands(connection, args, prefix)


# :Cloud-9.A_DNet.net 353 Roy_Mustang = #adtest :@Roy_Mustang
# :Cloud-9.A_DNet.net 366 Roy_Mustang #adtest :End of /NAMES list.


def onnames(connection, args):
    names = args[3].split()
    chan = connection.channels[args[2]]  # type: Channel

    # clear out the current user list
    if not chan.receivingnames:
        chan.receivingnames = True
        for user in chan.users:
            usero = chan.users[user].user  # type: User
            del usero.channels[chan.name]
        chan.users = {}

    for mask in names:
        mask = mask.strip()
        n, u = mask.split("!", 1)
        u, h = u.split("@", 1)
        admin, op, hop, voice = False, False, False, False
        if n[0] in ["!", "@", "%", "+"]:
            prefix = n[0]
            n = n[1:]
            if prefix == "!":
                admin = True
            elif prefix == "@":
                op = True
            elif prefix == "%":
                hop = True
            elif prefix == "+":
                voice = True
        if not connection.users.get(n):
            user = User(n, u, h)
            connection.users[n] = user

        chan.adduser(connection, connection.users[n], isop=op, ishop=hop,
                     isvoice=voice, isadmin=admin)


def onnamesend(connection, args):
    chan = connection.channels[args[1]]
    chan.receivingnames = False
    logchan(chan)


def onjoin(connection, prefix, args):
    chan = connection.channels.get(args[0])
    nick = prefix.split("!")[0]
    user = connection.users.get(nick)
    name = args[0]
    if not chan:
        connection.channels[name] = Channel(name)
    if not user:
        User.add(connection, prefix)
    if not connection.channels[name].users.get(nick):
        chan = connection.channels[name]
        user = connection.users[nick]
        chan.adduser(connection, user)
    logall(connection)


def onisupport(connection, args):
    tokens = args[1:-1]
    for token in tokens:
        if "NETWORK" in token:
            connection.networkname = token.split("=")[1]

        elif "PREFIX" in token:
            pfx = token.split("=")[1]
            pfx, modes = pfx.split(")", 1)
            pfx = pfx[1:]
            connection.Pmoded = dict(zip(pfx, modes))
            connection.Pmodes.update(pfx)

        elif "CHANMODES" in token:
            modes = token.split("=")[1]
            A, B, C, D = modes.split(",")
            connection.Amodes.update(A)
            connection.Bmodes.update(B)
            connection.Cmodes.update(C)
            connection.Dmodes.update(D)

        elif "EXCEPTS" in token:
            mode = token.split("=")[1]
            connection.Amodes.add(mode)
            connection.banexept.add(mode)

        elif "INVEX" in token:
            mode = token.split("=")[1]
            connection.Amodes.add(mode)
            connection.invex.add(mode)


def onmode(connection, args):
    target = args[0]
    modes = args[1]
    modeargs = args[2:]
    log(modeargs)
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

        elif mode in connection.Amodes:
            count += 1
        elif mode in connection.Bmodes:
            count += 1
        elif mode in connection.Cmodes:
            if adding:
                count += 1
        elif mode in connection.Dmodes:
            pass
        elif mode in connection.Pmodes:
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


def onpart(connection, prefix, args):
    chan = connection.channels.get(args[0], None)
    user = connection.users.get(prefix.split("!")[0], None)
    if not chan:
        log("WTF? I just got a part for a channel I dont have, "
            "channel was {c}".format(c=args))
        logall(connection)
    chan.deluser(connection, user)
    logall(connection)


def onkick(connection, args):
    user = connection.users.get(args[1], None)
    chan = connection.channels.get((args[0]), None)
    if user and chan:
        chan.deluser(connection, user)
    logall(connection)
