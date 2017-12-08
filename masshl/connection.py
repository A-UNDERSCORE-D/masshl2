import socket
import ssl
from collections import defaultdict
from selectors import EVENT_READ
from typing import DefaultDict, Dict, TYPE_CHECKING
from weakref import WeakValueDictionary

from masshl import parser
from masshl.channel import Channel
from masshl.logger import Logger
from masshl.user import User

if TYPE_CHECKING:
    from typing import List, Union
    from masshl.bot import Bot

socket.setdefaulttimeout(5)


class Connection:
    def __init__(self, config: dict, selector, bot, name, debug) -> None:
        self.port: str = config["port"]
        self.host: str = config["network"]
        self.is_ssl: bool = config["SSL"]
        self.debug: bool = debug
        self.join_channels: list = config["channels"]
        self.nick: str = config["nick"]
        self.user: str = config["user"]
        self.gecos: str = config["gecos"]
        self.nickserv_user: str = config["nsident"]
        self.nickserv_pass: str = config["nspass"]
        self.commands: List[str] = config["commands"]
        self._admin_chan: str = config["adminchan"]
        self.admins: List[str] = config["admins"]
        self.cmd_prefix: str = config["cmdprefix"]
        self.print_raw: bool = config["print_raw"]
        self.bot: 'Bot' = bot
        self.name: str = name

        self.selector = selector
        self.caps = {"userhost-in-names", "sasl"}
        self.socket = socket.socket()
        self.buffer = b""
        self.uhnames = False
        self.channels = {}
        self.chantypes = []     # TODO: Should this be a set?
        self.users = WeakValueDictionary()
        self.connected = False
        self.hasquit = False
        self.capcount = 0
        self.cansasl = False
        self.last_ping = ""
        self.last_ping_time = 0

        self.log = Logger(self)

        # ISupport stuff

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
        # modes with prefixes, essentially type B
        self.p_modes = set()
        self.p_mode_d = {}
        self.user_modes = set()
        self.ban_exemption = set()
        self.invex = set()
        self.network_name = ""
        self.server = ""
        self.max_join_targets = 0

        self.storage: DefaultDict[str, Dict] = defaultdict(dict)

    # TODO: Support IRCv3.2 CAPS, CAP LS 302
    def connect(self):
        def debuglog(msg):
            if self.debug:
                self.log.debug(msg)

        debuglog("called")
        if self.is_ssl:
            self.socket = ssl.wrap_socket(self.socket)
        debuglog("connect start")
        self.socket.connect((self.host, self.port))
        debuglog("connect end")
        self.connected = True
        self.selector.register(self, EVENT_READ)
        self.write("CAP LS")
        self.write("NICK {nick}".format(nick=self.nick))
        self.write("USER {user} * * :{gecos}".format(user=self.user, gecos=self.gecos))

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

    def read(self):
        if self.connected:
            data = self.socket.recv(65535)
            if not data:
                self.close()
            else:
                self.handle_data(data)

    def handle_data(self, data):
        self.buffer += data
        while b"\r\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\r\n", 1)
            line = raw.decode(errors="replace")
            self.parse(line)

    def parse(self, line):
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

        data = {
            "connection": self,
            "prefix":     prefix,
            "tags":       tags,
            "cmd":        cmd,
            "args":       args
        }
        self.bot.call_hook("raw", **data)
        self.bot.call_hook("raw_" + cmd, **data)

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

    def fileno(self) -> int:
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
    def adminchan(self) -> 'Union[Channel, str]':
        """Plugins should not store a reference to this"""
        return self.channels.get(self._admin_chan, self._admin_chan)

    def log_adminchan(self, msg: str):
        if isinstance(self.adminchan, Channel):
            self.adminchan.send_message(msg)
        else:
            self.log.error(msg)

    @property
    def channel_modes(self):
        return self.a_modes | self.b_modes | self.c_modes | self.p_modes

    def renick(self, new_nick):
        self.nick = new_nick

    def __str__(self):
        return f"Connection: {self.name} on {self.network_name}."