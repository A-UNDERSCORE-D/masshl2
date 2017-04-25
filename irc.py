import socket
import ssl
import config
import os
import sys
import select
from logger import log
import fnmatch
from objs import *

channels = []
users = []

if config.config.get("SSL", False):
    sock = ssl.socket(socket.socket())
else:
    sock = socket.socket()

buffer = b""


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
                    # TODO: This V. do I want to hand the arguments without the colon? idk,
                    # TODO: lets mess with this
                    args[i] = " ".join(args[i:])

                    del args[i + 1:]
                i += 1

            parse(prefix, command, args)


def sockwrite(data):
    sock.send((data + "\r\n").encode())
    log(data, "ircout")

# TODO: ok, parsing, here? in its own file? if its here this file will need a lot of functions,
# TODO: also, move them masshl stuff itself to its own file?


def parse(prefix, command, args):
    if command == "PING":
        sockwrite("PONG " + " ".join(args))
    elif command == "JOIN":
        onjoin(prefix, args)

# TODO: Alright, so...
# TODO: needs to check if there is a channel in the master list, if not, add make it. then:
# TODO: check if there is a user in the master userlist for the joining user, if not, make it. then:
# TODO: add the membership obj to the user and the channel. perhaps the constructor can do this?
# TODO: if not do it here. also, sets for chanlists? thats gonna mean for loops. but meh
# TODO: - A_D 25/4 0524


def onjoin(prefix, args):
    log("adding chan")
    chan = addchan(args[0])
    log("adding user")
    user = adduser(prefix)
    log("adding membership")
    Membership.addusertochan(user, chan)
    log("---------------------------------------CHANNEL----------------------------------------")
    for channel in channels:
        log(channel.name)
        for user in channel.users:
            log("    " + user.user.mask)
    log("-----------------------------------------USER---------------------------------------")
    for user in users:
        log(user.mask)
        for channel in user.channels:
            log("    " + channel.channel.name)


def adduser(mask):
    if mask[0] == ":":
        mask = mask[1:]
    n, u = mask.split("!", 1)
    u, h = u.split("@", 1)
    for user in users:
        log("checking users")
        if user == mask.split("!")[0]:
            return user
    temp = User(n, u, h)
    log("adding new user")
    users.append(temp)
    return temp


def addchan(name):
    for chan in channels:
        log("checking channels")
        if chan == name:
            return chan
    temp = Channel(name)
    log("adding user")
    channels.append(temp)
    return temp

# def onpm(msg, prefix):
#     prefix = prefix[1:]
#     pass

sock.connect((config.config["network"], config.config["port"]))
sockwrite("USER " + config.config["user"] + " * * :realname")
sockwrite("NICK " + config.config["nick"])
