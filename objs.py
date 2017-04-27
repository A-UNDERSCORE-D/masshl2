import irc
from logger import log


class Membership:
    def __init__(self, channel, user, isop: bool =False, ishop: bool =False,
                 isvoice: bool =False, isadmin: bool =False):
        self.isop = isop
        self.ishop = ishop
        self.isvoice = isvoice
        self.isadmin = isadmin
        self.channel = channel
        self.user = user
        self.last_ping = 0


class User:
    def __init__(self, nick: str, user: str, host: str):
        self.nick = nick
        self.user = user
        self.host = host
        self.channels = []
        self.mask = self.nick + "!" + self.user + "@" + self.host

    def __eq__(self, other):
        if type(other) == User:
            other = other.nick
        return self.nick.lower() == other.lower()

    @staticmethod
    def check(mask: str, add: bool =False):
        if mask[0] == ":":
            mask = mask[1:]
        log("checking users")
        for user in irc.users:
            if user == mask.split("!")[0]:
                return user
        if add:
            n, u = mask.split("!", 1)
            u, h = u.split("@", 1)
            temp = User(n, u, h)
            log("adding new user")
            irc.users.append(temp)
            return temp
        else:
            return False


class Channel:
    def __init__(self, name: str, count: int =10, action: list =None, warn: int =7, opchan: str ="",
                 watched: bool =False):
        self.name = name if name[0] != ":" else name[1:]
        self.modes = ""
        self.count = count
        self.action = action if action else ["MODE {chan} +b {mask}", "KICK {chan} {nick}"]
        self.warn = warn
        self.opchan = opchan
        self.users = []
        self.watched = watched

    def __eq__(self, other: str):
        return self.name.lower() == other.lower()

    def adduser(self, user: User):
        """
        Adds a user to a channel, if the user exists in our list
        :param user: 
        :return: 
        """
        if user in irc.users:
            temp = Membership(self, user)
            self.users.append(temp)
            user.channels.append(temp)

    def deluser(self, user: User):
        """
        deletes a user from our channel if the user is in the userlist and
        is a member of the channel
        :param user: User object to be added to the channel
        :return: 
        """
        if user in irc.users:
            for membership in self.users:
                if membership.user == user:
                    self.users.remove(membership)
                    user.channels.remove(membership)
                    if len(user.channels) == 0:
                        irc.users.remove(user)
                    break

    @staticmethod
    def check(name: str, add: bool =False):
        """
        checks for a channel in the channel list, optionally adding it if its not found
        :param name: name of the channel
        :param add: whether or not to add it if its not found
        :return: a channel object or False
        """
        log("checking channels")
        for chan in irc.channels:
            if chan == name:
                return chan
        if add:
            temp = Channel(name)
            log("adding new channel")
            irc.channels.append(temp)
            return temp
        else:
            return False
