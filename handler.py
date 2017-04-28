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
        cap(connection, args)
    elif command == "AUTHENTICATE":
        auth(connection)

    elif command == "353":
        onnames(connection, args)
    elif command == "904":
        connection.write("CAP END")
    elif command == "903":
        connection.write("CAP END")


def auth(connection):
    connection.write("AUTHENTICATE {}".format(base64.b64encode(
        (
            connection.nick + "\00" + connection.nsuser + "\00" + connection.nspass
         ).encode()).decode()))


# TODO: rewrite cap negotiation
def cap(connection, args):
    done = False
    if args[1] == "LS":
        if "userhost-in-names" in args[2]:
            connection.write("CAP REQ :userhost-in-names")
        if "sasl" in args[2] and connection.ssl:
            connection.write("CAP REQ :sasl")
        else:
            done = True

    elif args[1] == "ACK":
        if "userhost-in-names" in args[2]:
            connection.uhnames = True
        if "sasl" in args[2]:
            connection.write("AUTHENTICATE PLAIN")

    elif args[1] == "NAK":
        if "userhost-in-names" in args[2]:
            connection.uhnames = False
        if "sasl" in args[2]:
            done = True
    if done:
        connection.write("CAP END")


def onnames(connection, args):
    names = args[3:]
    log(str(names))
    for mask in names:
        if mask[-1] == " ":
            mask = mask[:-1]
        # if mask[0] == "@":


def onjoin(connection, prefix, args):
    if not connection.channels.get(args[0], None):
        Channel.add(connection, args[0])
    if not connection.users.get(prefix.split("!")[0], None):
        User.add(connection, prefix)
    if not connection.channels[args[0]].users.get(prefix.split("!")[0], None):
        connection.channels[args[0]].adduser(connection, connection.users[prefix.split("!")[0]])
    logall(connection)


def onpart(connection, prefix, args):
    chan = connection.channels.get(args[0], None)
    user = connection.users.get(prefix.split("!")[0], None)
    if not chan:
        log("WTF? I just got a part for a channel I dont have, channel was {c}".format(c=args))
        logall(connection)
    chan.deluser(connection, user)
    logall(connection)


def onkick(connection, args):
    user = connection.users.get(args[1], None)
    chan = connection.channels.get((args[0]), None)
    if user and chan:
        chan.deluser(connection, user)
    logall(connection)
