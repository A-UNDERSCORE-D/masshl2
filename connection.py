import socket
import ssl
from logger import log
from handler import handler


class Connection:
    def __init__(self, config, selector):
        self.port = config.port
        self.host = config.network
        self.ssl = config.SSL
        self.debug = config.debug
        self.joinchannels = config.channels or []
        self.nick = config.nick
        self.user = config.user
        self.gecos = config.gecos or ""
        self.nsuser = config.nsident
        self.nspass = config.nspass
        self.commands = config.commands
        self.adminchan = config.adminchan
        self.cmdprefix = config.cmdprefix
        self.global_nickignore = config.global_nickignore
        self.global_maskignore = config.global_maskignore

        self.config = config

        self.selector = selector
        self.caps = {"userhost-in-names", "sasl"}
        self.socket = socket.socket()
        self.buffer = b""
        self.uhnames = False
        self.channels = {}
        self.users = {}
        self.connected = False
        self.capcount = 0
        self.cansasl = False
        # Isupport stuff

        # adds or removes to a list, always has a parameter from the server
        self.Amodes = set()
        # changes a setting on a channel, must always have a parameter from the
        # server and from clients like o and k
        self.Bmodes = set()
        # must have a parameter when being set and must /not/ have one when
        # being unset, like F and H
        self.Cmodes = set()
        # changes a setting on a channel, NEVER has a parameter
        self.Dmodes = set()
        # modes with prefixes, are essentially type B
        self.Pmodes = set()
        self.Pmoded = {}
        self.banexept = set()
        self.invex = set()
        self.networkname = ""
        self.maxJtargets = 0

    def connect(self):
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)
        self.socket.connect((self.host, self.port))
        self.connected = True
        self.write("CAP LS")
        self.write("NICK {nick}".format(nick=self.nick))
        self.write("USER {user} * * :{gecos}".format(user=self.user,
                                                     gecos=self.gecos))

    def read(self):
        if self.connected:
            # readable, _, _ = select.select([self.socket], [], [], 5)
            # events = self.selector.select()
            # for readable, _ in events:
            #     if self.socket in readable:
            #         print(type(readable))
            data = self.socket.recv(65535)
            if not data:
                self.close()
            else:
                self.parse(data)

    def write(self, data):
        if isinstance(data, bytes):
            self.socket.send(data + b"\r\n")
            log(data.decode(), "ircout")
        else:
            self.socket.send((data + "\r\n").encode())
            log(data, "ircout")

    def parse(self, data):
        self.buffer += data
        while b"\r\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\r\n", 1)
            line = raw.decode()
            log(line, "ircin")
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
            handler(self, prefix, cmd, args)

    def joinchans(self, channels):
        chanstojoin: str = ""
        if isinstance(channels, list):
            chanstojoin = ",".join(channels)
        elif isinstance(channels, str):
            chanstojoin = channels
        if chanstojoin:
            self.write(f"JOIN {chanstojoin}")

    def quit(self, message):
        self.write("QUIT :{msg}".format(msg=message))
        self.socket.shutdown(socket.SHUT_WR)

    def close(self):
        self.selector.unregister(self)
        self.socket.close()
        self.connected = False

    def fileno(self):
        if self.socket:
            return self.socket.fileno()
        else:
            return -1
