import string

from hook import load, message, command
from channel import Channel
from user import User
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from parser import Message

__plugin_name__ = "masshl2"

DEFAULT_CHANNEL_CONFIG = {
    "max_count": 0,
    "mask_ignore": []
}

DEFAULT_NETWORK_CONFIG = {
    "nick_ignore":    [],
    "mask_ignore":    [],
    "weighted_nicks": [],
    "channels": {}
}

DEFAULT_CONFIG = {
    "global":   {
        "nick_length":    2,
        "nick_ignore":    list(string.ascii_lowercase),
        # Nicks that are counted extra times, eg bots that shouldn't be pings
        "weighted_nicks": {"chanserv": 2},
        "ignored_masks":  [""],
        "debug": 0
    },

    # Network specific configurations, uses the above DEFAULT_NETWORK_CONFIG
    "networks": {},
}

config = None


# Fetch our config if it exists, if not, make it exist
@load
def onload(bot):
    plugin_data = bot.config["plugin_data"]
    if not plugin_data.get(__plugin_name__):
        plugin_data[__plugin_name__] = DEFAULT_CONFIG.copy()
        bot.config.save()
    global config
    config = plugin_data[__plugin_name__]


def scan_message(msg: 'Message', channel: Channel, source: User):
    chan_nick_list = {nick.casefold() for nick in channel.memberships.keys()}

    chan_nick_list.difference_update(config["global"]["nick_ignore"])

    msg_cf = msg.casefold()
    matched_nicks = {nick for nick in chan_nick_list if nick in msg_cf}

    count = len(matched_nicks)
    global_weighted_nicks = config["global"]["weighted_nicks"]
    network_weighted_nicks = config["networks"].get(msg.conn.name)
    for nick in matched_nicks:
        if nick in global_weighted_nicks:
            count += global_weighted_nicks[nick] - 1
        if network_weighted_nicks and nick in network_weighted_nicks:
            count += network_weighted_nicks[nick] - 1
    return count, matched_nicks


def try_ban(chan: Channel, user: User):
    pass


@message
def onmsg(msg: 'Message'):
    if msg.conn.name not in config["networks"]:
        if config["global"]["debug"] >= 3:
            msg.conn.log(f"got a message on a channel we don't watch. It was {msg}")
        return
    chan = msg.target
    user = msg.origin
    if not isinstance(chan, Channel) or not isinstance(user, User):
        # Either this was not directed at a channel, or we don't have an origin. Either way we can do nothing, so stop.
        return
    if chan.name not in config["networks"][msg.conn.name]:
        return
    count, nicks = scan_message(msg, chan, user)
    if config["debug"] > 0:
        msg.conn.log_adminchan(f"count was {count}, nicks was {nicks}")


@command("masshl_set_debug", perm=["bot_control"])
def debugprint(args):
    if len(args) >= 1:
        try:
            config["global"]["debug"] = int(args[0])
        except ValueError:
            return f"{args[0]} is not a valid number."
