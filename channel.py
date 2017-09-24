from membership import Membership
from user import User
from typing import Dict, DefaultDict
from collections import defaultdict


class Channel:
    def __init__(self, name: str, connection):

        self.name = name if name[0] != ":" else name[1:]
        self.modes = ""
        self.memberships = {}
        self.hasmodes = None
        self.receivingnames = False
        self.admins = []
        self.connection = connection
        self.bot = self.connection.bot

        self.storage: DefaultDict[str, Dict] = defaultdict(dict)
        print(f"CHANNEL_INIT {self}")
        self.bot.call_hook("channel_init", chan=self, conn=self.connection)

    def __eq__(self, other: str) -> bool:
        return self.name.lower() == other.lower()

    def __str__(self):
        return self.name

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

    def deluser(self, user: 'User'):
        """
        deletes a user from our channel if the user is in the userlist and
        is a member of the channel

        :param user: User object to be added to the channel
        :return: 
        """
        try:
            del self.memberships[user.nick]
        except KeyError:
            self.connection.log("Attempted to remove a non-existent user from a channel")

    def get_user(self, nick: str) -> 'User':
        """Return the user object from a membership object on this channel"""
        return self.get_member(nick).user

    def get_member(self, nick: str) -> 'Membership':
        """Return the membership object for a user"""
        return self.memberships[nick]

    def send_message(self, msg: str):
        self.connection.write(f"PRIVMSG {self.name} :{msg}")

    def send_notice(self, msg: str):
        self.connection.write(f"NOTICE {self.name} :{msg}")
