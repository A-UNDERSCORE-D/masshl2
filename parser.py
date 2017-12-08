import collections
import re
import typing
from typing import List, Tuple, Optional

from channel import Channel

if typing.TYPE_CHECKING:
    from user import User
    from connection import Connection
    from bot import Bot

PREFIX_RE = re.compile(r'(?P<nick>.+?)(?:!(?P<user>.+?))?(?:@(?P<host>.+?))?')


def parse_prefix(prefix):
    match = PREFIX_RE.fullmatch(prefix)
    return match.group('nick'), match.group('user'), match.group('host')


mode_tuple = collections.namedtuple("mode_tuple", "mode args adding")


# TODO: This WILL have a bug where type a modes require parameters
def parse_modes(mode_string: str, conn: 'Connection'):
    modes, *args = mode_string.split()
    adding = True
    out: List[mode_tuple] = []
    for mode in modes:
        if mode == "+" or mode == "-":
            adding = mode == "+"
            continue
        assert mode in conn.channel_modes, f"mode '{mode}' requested that isn't provided by {conn}"
        if mode in conn.a_modes:
            out.append(mode_tuple(mode, args.pop(0), adding))
        elif mode in (conn.b_modes | conn.p_modes):
            out.append(mode_tuple(mode, args.pop(0), adding))
        elif mode in conn.c_modes:
            if adding:
                out.append(mode_tuple(mode, args.pop(0), adding))
            else:
                out.append(mode_tuple(mode, None, adding))
        elif mode in conn.d_modes:
            out.append(mode_tuple(mode, None, adding))
    return out


class Message:
    def __init__(self, connection: 'Connection', args, prefix, msg_type) -> None:
        self.conn = connection
        self.args = args
        self.prefix = prefix
        self.type = msg_type
        self.target: typing.Union[User, Channel]
        self.origin: typing.Optional[User]
        self.message: str = ""
        self._parse_msg(prefix, args)
        self.split_msg = self.message.split(" ")
        self.eol_msg = [' '.join(self.split_msg[i:]) for i in range(len(self.split_msg))]

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

    @property
    def has_origin(self):
        return self.origin is not None
