import socket
import ssl
import config
import os
import sys
import select
from logger import log
import fnmatch
from objs import *
import base64

channels = []
users = []

if config.config.get("SSL", False):
    sock = ssl.wrap_socket(socket.socket())
else:
    sock = socket.socket()

buffer = b""
uhnames = False


def sockread():
    readable, _, _ = select.select([sock], [], [], 3)
    if sock in readable:
        data = sock.recv(65535)

        if not data:
            sock.close()
            sys.exit("Socket Closed")
        global buffer
        buffer += data
        while b"\r\n" in buffer:
            rawl, buffer = buffer.split(b"\r\n", 1)
            line = rawl.decode()
            log(line, "ircin")
            if line[0] == ":":
                prefix, line = line.split(None, 1)
            else:
                prefix = None

            args = line.split(" ")
            command = args.pop(0)
            i = 0
            while i < len(args):
                if args[i][0] == ":":
                    args[i] = " ".join(args[i:])[1:]

                    del args[i + 1:]
                i += 1

            parse(prefix, command, args)


def sockwrite(data):
    if type(data) == bytes:
        sock.send(data + "\r\n".encode())
        log(data.decode(), "ircout")
    else:
        sock.send((data + "\r\n").encode())
        log(data, "ircout")


def auth():
    sockwrite("AUTHENTICATE {}".format(base64.b64encode(
        (config.config["nick"] + "\00" + config.config["nsident"] + "\00" + config.config["nspass"]
         ).encode()).decode()))


def cap(args):
    done = False
    global uhnames
    if args[1] == "LS":
        if "userhost-in-names" in args[2]:
            sockwrite("CAP REQ userhost-in-names")
            return
    elif args[1] == "ACK":
        if "userhost-in-names" in args[2]:
            uhnames = True
        if "sasl" in args[2]:
            sockwrite("AUTHENTICATE PLAIN")
    elif args[1] == "NAK":
        if "userhost-in-names" in args[2]:
            uhnames = False
        if "sasl" in args[2]:
            done = True
    if done:
        sockwrite("CAP END")


def onnames(args):
    pass


def onjoin(prefix, args):
    chan = Channel.check(args[0], True)
    user = User.check(prefix, True)
    chan.adduser(user)
    logall()


def onpart(prefix, args):
    user = User.check(prefix)
    chan = Channel.check(args[0])
    if user and chan:
        chan.deluser(user)
    logall()


def onkick(args):
    user = User.check(args[1])
    chan = Channel.check(args[0])
    if user and chan:
        chan.deluser(user)
    logall()


def logall():
    log("---------------------------------------CHANNELS---------------------------------------")
    for channel in channels:
        log(channel.name)
        for user in channel.users:
            log("  `-" + user.user.mask)
    log("----------------------------------------USERS------------------------------------------")
    for user in users:
        log(user.mask)
        for channel in user.channels:
            log("  `-" + channel.channel.name)


def connect():
    sock.connect((config.config["network"], config.config["port"]))
    sockwrite("CAP LS")
    sockwrite("USER " + config.config["user"] + " * * :realname")
    sockwrite("NICK " + config.config["nick"])


def parse(prefix, command, args):
    if command == "PING":
        sockwrite("PONG " + " ".join(args))
    elif command == "JOIN":
        onjoin(prefix, args)
    elif command == "PART":
        onpart(prefix, args)
    elif command == "KICK":
        onkick(args)

    elif command == "CAP":
        cap(args)
    elif command == "AUTHENTICATE":
        auth()

    elif command == "353":
        onnames(args)
    elif command == "904":
        sockwrite("CAP END")
    elif command == "903":
        sockwrite("CAP END")
