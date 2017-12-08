import weakref
from typing import DefaultDict, Dict
from collections import defaultdict


class Membership:
    def __init__(self, channel, user, is_op: bool = False, is_hop: bool = False,
                 is_voice: bool = False, is_admin: bool = False):
        self.is_op = is_op
        self.is_hop = is_hop
        self.is_voice = is_voice
        self.is_admin = is_admin
        self.channel = weakref.proxy(channel)
        self.user = user
        self.last_ping = 0
        self.storage: DefaultDict[str, Dict] = defaultdict(dict)

    def prefix(self) -> str:
        if self.is_admin:
            return "!"
        elif self.is_op:
            return "@"
        elif self.is_hop:
            return "%"
        elif self.is_voice:
            return "+"
        else:
            return ""
