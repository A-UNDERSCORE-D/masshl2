from logger import log, logall
from user import User
from membership import Membership


class Channel:
    def __init__(self, name: str, count: int = 10, action: list = None,
                 warn: int = 7, opchan: str = "", watched: bool = False):

        self.name = name if name[0] != ":" else name[1:]
        self.modes = ""
        self.count = count
        self.action = action if action else ["MODE {chan} +b {mask}",
                                             "KICK {chan} {nick}"]
        self.warn = warn
        self.opchan = opchan
        self.users = {}
        self.watched = watched
        self.hasmodes = None

    def __eq__(self, other: str) -> bool:
        return self.name.lower() == other.lower()

    def adduser(self, connection, user: User):
        """
        Adds a user to a channel, if the user exists in our list

        :param user: 
        :param connection:
        :return: the membership object created
        """
        if connection.users.get(user.nick, None):
            temp = Membership(self, user)
            self.users[user.nick] = temp
            user.channels[self.name] = temp
            return temp
        else:
            raise ValueError("Unknown User")

    def deluser(self, connection, user: User):
        """
        deletes a user from our channel if the user is in the userlist and
        is a member of the channel

        :param user: User object to be added to the channel
        :param connection: Connection object to work on
        :return: 
        """
        if user and connection.users.get(user.nick, None):
            if self.users.get(user.nick):
                del self.users[user.nick]
                del user.channels[self.name]
                if len(user.channels) == 0:
                    del connection.users[user.nick]
        else:
            # raise ValueError("Unknown user")
            log("Got a part for an unknown user! WTF?")
