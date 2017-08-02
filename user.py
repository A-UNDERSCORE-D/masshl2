from logger import log
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import channel
    import membership

class User:
    def __init__(self, nick: str, user: str, host: str, connection):
        self.nick = nick
        self.user = user
        self.host = host
        self.memberships = {}
        self.connection = connection

    def __eq__(self, other) -> bool:
        if type(other) == User:
            other = other.nick
        return self.nick.lower() == other.lower()

    @property
    def mask(self):
        return self.nick + "!" + self.user + "@" + self.host

    def renick(self, newnick):
        log("Running renick", connection=self.connection)
        for member in self.memberships:
            log(f"Checking memberships: {member}", connection=self.connection)
            member = self.memberships[member]
            member.channel.memberships[newnick] = member.channel.memberships[self.nick]
            del member.channel.memberships[self.nick]
        self.connection.users[newnick] = self.connection.users[self.nick]
        del self.connection.users[self.nick]
        self.nick = newnick

    @staticmethod
    def add(connection, mask):
        n, u = mask.split("!", 1)
        u, h = u.split("@", 1)
        if not connection.users.get(u):
            temp = User(n, u, h, connection)
            connection.users[temp.nick] = temp
            return temp
        else:
            return connection.users[u]
