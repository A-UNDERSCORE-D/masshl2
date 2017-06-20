class User:
    def __init__(self, nick: str, user: str, host: str):
        self.nick = nick
        self.user = user
        self.host = host
        self.channels = {}
        self.mask = self.nick + "!" + self.user + "@" + self.host

    def __eq__(self, other) -> bool:
        if type(other) == User:
            other = other.nick
        return self.nick.lower() == other.lower()

    @staticmethod
    def add(connection, mask):
        n, u = mask.split("!", 1)
        u, h = u.split("@", 1)
        if not connection.users.get(u):
            temp = User(n, u, h)
            connection.users[temp.nick] = temp
            return temp
        else:
            return connection.users[u]
