import socket
import ssl
from selectors import EVENT_READ
from weakref import WeakValueDictionary

import parser
from logger import Logger
from typing import DefaultDict, Dict
from collections import defaultdict
from user import User
from channel import Channel


class Connection:
    def __init__(self, config: dict, selector, bot, name, debug):
        self.port = config["port"]
        self.host = config["network"]
        self.is_ssl = config["SSL"]
        self.debug = debug
        self.joinchannels = config["channels"]
        self.nick = config["nick"]
        self.user = config["user"]
        self.gecos = config["gecos"]
        self.nsuser = config["nsident"]
        self.nspass = config["nspass"]
        self.commands = config["commands"]
        self._adminchan = config["adminchan"]
        self.admins = config["admins"]
        self.cmdprefix = config["cmdprefix"]
        self.global_nickignore = config["global_nickignore"]
        self.global_maskignore = config["global_maskignore"]
        self.bot_nicks = config["bot_nicks"]
        self.print_raw = config["print_raw"]
        self.bot = bot
        self.name = name

        self.selector = selector
        self.caps = {"userhost-in-names", "sasl"}
        self.socket = socket.socket()
        self.buffer = b""
        self.uhnames = False
        self.channels = {}
        self.chantypes = []
        self.users = WeakValueDictionary()
        self.connected = False
        self.hasquit = False
        self.capcount = 0
        self.cansasl = False

        self.log = Logger(self)

        # Isupport stuff

        # adds or removes to a list, always has a parameter from the server
        self.a_modes = set()
        # changes a setting on a channel, must always have a parameter from the
        # server and from clients like o and k
        self.b_modes = set()
        # must have a parameter when being set and must /not/ have one when
        # being unset, like F and H
        self.c_modes = set()
        # changes a setting on a channel, NEVER has a parameter
        self.d_modes = set()
        # modes with prefixes, are essentially type B
        self.p_modes = set()
        self.p_mode_d = {}
        self.banexept = set()
        self.invex = set()
        self.networkname = ""
        self.server = ""
        self.maxJtargets = 0

        self.storage: DefaultDict[str, Dict] = defaultdict(dict)

# TODO: Support IRCv3.2 CAPS, CAP LS 302
    def connect(self):
        if self.is_ssl:
            self.socket = ssl.wrap_socket(self.socket)
        self.socket.connect((self.host, self.port))
        self.connected = True
        self.selector.register(self, EVENT_READ)
        self.write("CAP LS")
        self.write("NICK {nick}".format(nick=self.nick))
        self.write("USER {user} * * :{gecos}".format(user=self.user, gecos=self.gecos))

    def read(self):
        if self.connected:
            data = self.socket.recv(65535)
            if not data:
                self.close()
            else:
                self.parse(data)

    def write(self, data):
        if not self.connected:
            return
        if isinstance(data, bytes):
            self.socket.send(data + b"\r\n")
            if self.print_raw:
                self.log.ircout(data.decode())
        else:
            self.socket.send((data + "\r\n").encode())
            if self.print_raw:
                self.log.ircout(data)

    def parse(self, data):
        self.buffer += data
        while b"\r\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\r\n", 1)
            line = raw.decode(errors="replace")
            if self.print_raw:
                self.log.ircin(line)
            if line[0] == "@":
                tags, line = line.split(None, 1)
            else:
                tags = None
            if line[0] == ":":
                prefix, line = line.split(None, 1)
                prefix = prefix[1:]
            else:
                prefix = None

            args = line.split(" ")
            cmd = args.pop(0)
            i = 0
            while i < len(args):
                if args[i][0] == ":":
                    args[i] = " ".join(args[i:])[1:]
                    del args[i + 1:]
                i += 1
            # handler(self, prefix, tags, cmd, args)
            data = {
                "connection": self,
                "prefix": prefix,
                "tags": tags,
                "cmd": cmd,
                "args": args
            }
            responses = self.bot.call_hook("raw", **data)
            responses.extend(self.bot.call_hook("raw_" + cmd, **data))
            for _, resp in responses:
                if isinstance(resp, Exception):
                    self.log.exception(resp)
                elif resp:
                    self.log(resp)

    def join(self, channels):
        chanstojoin: str = ""
        if isinstance(channels, list):
            chanstojoin = ",".join(channels)
        elif isinstance(channels, str):
            chanstojoin = channels
        if chanstojoin:
            self.write(f"JOIN {chanstojoin}")

    def part(self, channels, msg=None):
        chanstopart: str = ""
        if isinstance(channels, list):
            chanstopart = ",".join(channels)
        elif isinstance(channels, str):
            chanstopart = channels
        if chanstopart:
            if msg:
                self.write(f"PART {chanstopart} {msg}")
            else:
                self.write(f"PART {chanstopart}")

    def quit(self, message):
        self.write("QUIT :{msg}".format(msg=message))
        self.socket.shutdown(socket.SHUT_WR)
        self.hasquit = True

    def close(self):
        self.selector.unregister(self)
        self.socket.close()
        self.connected = False

    def fileno(self):
        if self.socket:
            return self.socket.fileno()
        else:
            return -1

    def get_user(self, prefix: str) -> 'User':
        nick, ident, host = parser.parse_prefix(prefix)
        try:
            return self.users[nick]
        except KeyError:
            user = User(nick, ident, host, self)
            self.users[user.nick] = user
            return user

    def del_user(self, nick) -> None:
        if isinstance(nick, str):
            user = self.users[nick]
        else:
            user = nick
        to_delete = [
            membership.channel for membership in user.memberships.values()
        ]
        for chan in to_delete:
            chan.deluser(user)

    @property
    def adminchan(self) -> 'Channel':
        """Plugins should not store a reference to this"""
        return self.channels.get(self._adminchan, None) or self._adminchan

    def log_adminchan(self, msg: str):
        if isinstance(self.adminchan, Channel):
            self.adminchan.send_message(msg)
        else:
            self.log.error(msg)
