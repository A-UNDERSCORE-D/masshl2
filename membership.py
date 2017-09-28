import weakref
from typing import DefaultDict, Dict
from collections import defaultdict


class Membership:
    def __init__(self, channel, user, isop: bool = False, ishop: bool = False,
                 isvoice: bool = False, isadmin: bool = False):
        self.isop = isop
        self.ishop = ishop
        self.isvoice = isvoice
        self.isadmin = isadmin
        self.channel = weakref.proxy(channel)
        self.user = user
        self.last_ping = 0
        self.storage: DefaultDict[str, Dict] = defaultdict(dict)

    def prefix(self) -> str:
        if self.isadmin:
            return "!"
        elif self.isop:
            return "@"
        elif self.ishop:
            return "%"
        elif self.isvoice:
            return "+"
        else:
            return ""
