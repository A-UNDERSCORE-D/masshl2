# import string
# from typing import TYPE_CHECKING, List
#
# from hook import load, unload, timer, command
#
# if TYPE_CHECKING:
#     from channel import Channel
#
# DEFAULT_CONFIG = {
#     "connections": {
#
#     },
#     "g_nickignore":     list(string.ascii_letters),
#     "g_min_nicklength": 2,
#     "g_weighted_nicks": ["chanserv"],
#     "g_maskignore":     [],
#     "conf_ver": 1,
#     "networks": {
#         "snoonet": {
#             "#chan"
#         }
#     }
# }
#
# DEFAULT_CHAN_CONFIG = {
#     "name": "",
#     "opchan": "",
#     "action": [""],
#     "max_count": 0,
#     "reason": "",
# }
#
# # TODO: Why store data on channels, this makes us reliant on channels existing at startup.
# # TODO: Why not instead store data on membership objects, for the data that needs to be volatile, anyway
#
# # class ChannelConfig:
# #     def __init__(self, channel: str, conn, opchan: str = None, action: List[str] = None, reason: str = None,
# #                  count: int = 10):
# #         self._channel_name = channel
# #         self.reason: str = reason or "You have been banned for {time}. Do not mass highlight in {chan}"
# #         self._op_chan_name = opchan
# #         self.max_count = count
# #
# #         self.action = action if action is not None else ["KICK {chan} {nick} :{reason}"]
# #         self.conn = conn
# #         self.channel = self.conn.channels.get(self._channel_name)
# #         self.op_chan = self.conn.channels.get(self._op_chan_name)
# #
# #     @property
# #     def dict(self) -> dict:
# #         return {
# #             "channel": self._channel_name,
# #             "opchan":  self._op_chan_name,
# #             "action":  self.action,
# #             "count":   self.max_count,
# #             "reason":  self.reason,
# #             "conn":    self.conn.name
# #         }
# #
# #     def update(self):
# #         if self.channel is None:
# #             self.channel = self.conn.channels.get(self._channel_name)
# #         if self.op_chan is None and self._op_chan_name is not None:
# #             self.op_chan = self.conn.channels.get(self._op_chan_name)
#
# config = None
#
#
# @load
# def onload(bot):
#     bot.log("MASSHL PLUGIN: running on load func")
#     if "masshl" not in bot.plugin_data:
#         bot.plugin_data["masshl"] = DEFAULT_CONFIG
#         bot.config.save()
#         return
#     global config
#     config = bot.config["plugin_data"]["masshl"]
#     _config_update(bot)
#
#
# @unload
# def onunload(bot):
#     for conn in bot.connections:
#         for channel in conn.channels.values():
#             _unload_data_from_channel(channel)
#
#
# def _load_data_onto_channel(channel: 'Channel', conf: ChannelConfig):
#     channel.storage["masshl"] = conf
#
#
# def _unload_data_from_channel(channel: 'Channel'):
#     if "masshl" in channel.storage:
#         del channel.storage["masshl"]
#
#
# def _config_update(bot):
#     for conn in bot.connections:
#         for channel in conn.channels.values():
#             if channel.name in config:
#                 _load_data_onto_channel(channel, config[conn.name][channel.name])
#             if "masshl" in channel.storage:
#                 channel.storage["masshl"].update()
#
#
# @command("mhl_test")
# def cmd_test(bot):
#     test_conf = [ChannelConfig("#thisisatest", bot.connections[0])]
#     bot.config["plugin_data"]["masshl"] = {y.conn.name: y.dict for y in test_conf}
#     print(bot.config["plugin_data"])
#
#
# @timer(15)
# def on_tick(bot):
#     if config is None:
#         bot.log("No config")
#         return
#     _config_update(bot)
