from hook import message, command, load, unload
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from channel import Channel
    from user import User
    from connection import Connection


@load
def onload(bot):
    bot.log("MASSHL PLUGIN: running on load hooks")
    if "masshl" not in bot.config:
        return
    config = bot.config["masshl"]
    bot.log(config)
    for conn in bot.connections:
        for channel in conn.channels:
            _load_data_onto_channel(channel, config[conn.name][channel.name])


def _load_data_onto_channel(channel: 'Channel', config: dict):
    channel.storage["masshl"].update(config)
