import socket
import ssl
import select
from logger import log
from handler import handler


class Connection:
    def __init__(self, config):
        self.port = config.port
        self.host = config.host
        self.ssl = config.isssl
        self.debug = config.debug
        self.joinchannels = config.channels or []
        self.nick = config.nick
        self.user = config.user
        self.gecos = config.gecos or ""
        self.nsuser = config.nsuser
        self.nspass = config.nspass
        self.commands = config.commands or [""]
        self.caps = config.caps or {"userhost-in-names", "sasl"}

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
            try:
                readable, _, _ = select.select([self.socket], [], [], 5)
                if self.socket in readable:
                    data = self.socket.recv(65535)
                    if not data:
                        self.close()
                    self.parse(data)

            except OSError as e:
                log("Error: {error}.".format(error=e), "error")

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

    def quit(self, message):
        self.write("QUIT :{msg}".format(msg=message))

    def close(self):
        self.socket.close()
        self.connected = False
