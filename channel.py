from logger import log, logall
from user import User
from membership import Membership


class Channel:
    def __init__(self, name: str, connection, count: int = 10,
                 action: list = None, warn: int = 7, opchan: str = "",
                 watched: bool = False):

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
        self.receivingnames = False
        self.nickignore = []
        self.maskignore = []
        self.connection = connection

    def __eq__(self, other: str) -> bool:
        return self.name.lower() == other.lower()

    def adduser(self, connection, user: User, isop: bool =False,
            ishop: bool =False, isvoice: bool =False, isadmin: bool =False):
        """
        Adds a user to a channel, if the user exists in our list

        :param user: 
        :param connection:
        :param isop: bool, sets whether the user is opped in the channel
        :param ishop: bool, sets whether the user is hopped in the channel
        :param isvoice: bool, sets whether the user is voiced in the channel
        :param isadmin: bool, sets whether the user is marked as an admin 
        in the channel
        :return: Membership, the membership object created
        """
        if connection.users.get(user.nick, None):
            temp = Membership(self, user, isop=isop, ishop=ishop,
                              isvoice=isvoice, isadmin=isadmin)
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

    def cleanup(self):
        log("cleanup called")
        userlist = []
        for user in self.users:
            log("collecting users")
            usero = self.users[user].user
            userlist.append(usero)
        log(str(userlist))
        for user in userlist:
            log(f"removing user: {user.nick}")
            self.deluser(self.connection, user)
        log("deleting self")
        del self.connection.channels[self.name]
