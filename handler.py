from user import User
from channel import Channel
import base64
from logger import log, logall


def handler(connection, prefix, command, args):
    if command == "PING":
        connection.write("PONG :" + " ".join(args))
    elif command == "JOIN":
        onjoin(connection, prefix, args)
    elif command == "PART":
        onpart(connection, prefix, args)
    elif command == "KICK":
        onkick(connection, args)

    elif command == "CAP":
        handlecap(connection, args)
    elif command == "AUTHENTICATE":
        sendauth(connection)

    elif command == "001":
        onwelcome(connection)
    elif command == "353":
        onnames(connection, args)
    elif command == "904" or command == "903":
        capdecrement(connection)


def sendauth(connection):
    connection.write("AUTHENTICATE {}".format(base64.b64encode(
        (
            connection.nick + "\00" + connection.nsuser + "\00" +
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
    log("capcount = " + str(connection.capcount))


def capdecrement(connection):
    connection.capcount -= 1
    if connection.capcount <= 0:
        connection.write("CAP END")
    log("capcount = " + str(connection.capcount))


def onwelcome(connection):
    for command in connection.commands:
        connection.write(command)
    if not connection.cansasl:
        identify(connection)


def identify(connection):
    connection.write("PRIVMSG NickServ :IDENTIFY {nsnick} {nspass}".format(
        nsnick=connection.nsuser, nspass=connection.nspass
    ))


def onnames(connection, args):
    names = args[3:]
    log(str(names))
    for mask in names:
        mask = mask.strip()

        # if mask[0] == "@":


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
