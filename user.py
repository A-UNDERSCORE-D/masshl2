import weakref
from weakref import WeakValueDictionary

from logger import log
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import channel


class User:
    def __init__(self, nick: str, user: str, host: str, connection):
        self.nick = nick
        self.user = user
        self.host = host
        self.memberships = WeakValueDictionary()
        self.connection = weakref.proxy(connection)

    def __eq__(self, other) -> bool:
        if type(other) == User:
            other = other.nick
        return self.nick.lower() == other.lower()

    @property
    def mask(self):
        return self.nick + "!" + self.user + "@" + self.host

    def renick(self, newnick):
        log("Running renick", connection=self.connection)
        for name, membership in self.memberships.items():
            log(f"Checking memberships: {membership}", connection=self.connection)
            me = membership.channel.memberships.pop(self.nick)
            membership.channel.memberships[newnick] = me
        self.connection.users[newnick] = self.connection.users.pop(self.nick)
        self.nick = newnick

    @staticmethod
    def add(connection, mask):
        nick, ident = mask.split("!", 1)
        ident, host = ident.split("@", 1)
        try:
            return connection.users[nick]
        except KeyError:
            temp = User(nick, ident, host, connection)
            connection.users[temp.nick] = temp
            return temp
