class Membership:
    def __init__(self, channel, user, isop: bool = False, ishop: bool = False,
                 isvoice: bool = False, isadmin: bool = False):
        self.isop = isop
        self.ishop = ishop
        self.isvoice = isvoice
        self.isadmin = isadmin
        self.channel = channel
        self.user = user
        self.last_ping = 0
