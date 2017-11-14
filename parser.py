import re
import typing
from channel import Channel

if typing.TYPE_CHECKING:
    from user import User
    from connection import Connection
    from bot import Bot

PREFIX_RE = re.compile(r'(?P<nick>.+?)(?:!(?P<user>.+?))?(?:@(?P<host>.+?))?')


def parse_prefix(prefix):
    match = PREFIX_RE.fullmatch(prefix)
    return match.group('nick'), match.group('user'), match.group('host')


class Message:
    def __init__(self, connection: 'Connection', args, prefix, msg_type):
        self.conn = connection
        self.args = args
        self.prefix = prefix
        self.type = msg_type
        self.target: typing.Union[User, Channel]
        self.origin: typing.Optional[User]
        self.message: str = ""
        self._parse_msg(prefix, args)
        self.split_msg = self.message.split(" ")
        self.eol_msg = [' '.join(args[i:]) for i in range(len(args))]

    @property
    def bot(self) -> 'Bot':
        return self.conn.bot

# TODO: suppress the error messages during connect, they're not needed then and add to clutter
    def _parse_msg(self, prefix, args):
        nick, user, host = parse_prefix(prefix)
        if args[0][0] in self.conn.chantypes:
            self.target = self.conn.channels.get(args[0])
        else:
            self.target = self.conn.users.get(args[0])
        self.origin = self.conn.users.get(nick)
        if not self.origin and prefix != self.conn.server:
            self.conn.log.debug("WTF? Got a message from someone I dont know")
        if not self.target and args[0] != self.conn.nick:
            self.conn.log.debug("WTF? Got a message pointed at nothing")
        self.message = args[1]

    @property
    def is_chan_message(self) -> bool:
        return isinstance(self.target, Channel)

    def casefold(self):
        return self.message.casefold()

    def __str__(self):
        return f"{self.prefix} {self.type} :{' '.join(self.args)}"

    def __len__(self):
        return len(self.split_msg)

    def __eq__(self, other):
        return self.message == other

    def __contains__(self, item):
        return item in self.split_msg or item in self.message

    def startswith(self, other: str) -> bool:
        return self.message.startswith(other)

    def lower(self) -> str:
        return self.message.lower()
