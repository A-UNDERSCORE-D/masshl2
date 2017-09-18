import weakref
from typing import TYPE_CHECKING, List, Union
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from connection import Connection


class User:
    def __init__(self, nick: str, user: str, host: str, connection: 'Connection'):
        self.nick = nick
        self.user = user
        self.host = host
        self.memberships = WeakValueDictionary()
        self.connection = weakref.proxy(connection)

        # masshl stuff
        self.last_ping = [0, ""]

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            other = other.nick

        if isinstance(other, str):
            return self.nick.lower() == other.lower()

        return NotImplemented

    def __str__(self):
        return self.nick

    @property
    def mask(self) -> str:
        return self.nick + "!" + self.user + "@" + self.host

    def renick(self, newnick: str):
        self.connection.log("Running renick")
        for name, membership in self.memberships.items():
            self.connection.log(f"Checking memberships: {membership}")
            me = membership.channel.memberships.pop(self.nick)
            membership.channel.memberships[newnick] = me
        self.connection.users[newnick] = self.connection.users.pop(self.nick)
        self.nick = newnick

    def send_message(self, msg: str):
        self.connection.write(f"PRIVMSG {self.nick} :{msg}")

    def send_notice(self, msg: str):
        self.connection.write(f"NOTICE {self.nick} :{msg}")
