

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

    @staticmethod
    def addusertochan(user, chan):
        temp = Membership(chan, user)
        user.channels.append(temp)
        chan.users.append(temp)

    @staticmethod
    def removeuserfromchan(user, chan):



class User:
    def __init__(self, nick, user, host):
        self.nick = nick
        self.user = user
        self.host = host
        self.channels = []
        self.mask = self.nick + "!" + self.user + "@" + self.host

# TODO: There must be a better way to do this, also, so, why not check if the one is in the nick
# TODO: and if it is replace the ones in other to match? that'd work for an equality check.
# TODO: also, nick class with this stuff there? the chan class already has some stuff for equality
# TODO: in it, so... idk, a channel is both a name and a thing, while a nick and user /could/
# TODO: be separate. Do I need to do this? the server will stop this before I see it, so...
    def __eq__(self, other: str):
        # if "{" in self.nick or "{" in other:
        #     pass
        # elif "}" in self.nick or "}" in other:
        #     pass
        # elif "|" in self.nick or "|" in other:
        #     pass

        if self.nick.lower() == other.lower():
            return True
        else:
            return False


class Channel:
    def __init__(self, name: str, count: int =10, action: list =None, warn: int =7, opchan: str ="",
                 watched: bool =False):
        self.name = name
        self.modes = ""
        self.count = count
        self.action = action if action else ["MODE {chan} +b {mask}", "KICK {chan} {nick}"]
        self.warn = warn
        self.opchan = opchan
        self.users = []
        self.watched = watched

    def __eq__(self, other: str):
        if self.name.lower() == other.lower():
            return True
        else:
            return False
