from logger import log
from membership import Membership
from user import User


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
        self.memberships = {}
        self.watched = watched
        self.hasmodes = None
        self.receivingnames = False
        self.nickignore = []
        self.maskignore = []
        self.connection = connection

    def __eq__(self, other: str) -> bool:
        return self.name.lower() == other.lower()

    def adduser(self, connection, user: User, isop: bool = False,
                ishop: bool = False, isvoice: bool = False,
                isadmin: bool = False):
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
        if user.nick in connection.users:
            temp = Membership(self, user, isop=isop, ishop=ishop,
                              isvoice=isvoice, isadmin=isadmin)
            self.memberships[user.nick] = temp
            user.memberships[self.name] = temp
            return temp
        else:
            raise ValueError("Unknown User")

    def deluser(self, user: User):
        """
        deletes a user from our channel if the user is in the userlist and
        is a member of the channel

        :param user: User object to be added to the channel
        :return: 
        """
        try:
            del self.memberships[user.nick]
        except KeyError:
            log("Attempted to remove a non-existent user from a channel")
