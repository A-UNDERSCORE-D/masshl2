import base64
from sys import exc_info

import parser
from channel import Channel
from logger import *
from typing import TYPE_CHECKING
from hook import raw
if TYPE_CHECKING:
    from connection import Connection
    from parser import Message
# TODO: CTCP responses

HANDLERS = {}


# def raw(*cmds):
#     def _decorate(func):
#         for cmd in cmds:
#             HANDLERS.setdefault(cmd.upper(), []).append(func)
#         return func
#
#     return _decorate


def hook_load(func):
    setattr(func, "_isOnLoadCallback", None)
    return func


# def handler(connection, prefix, tags, command, args):
#     data = {
#         "connection": connection,
#         "prefix": prefix,
#         "tags": tags,
#         "command": command,
#         "args": args,
#     }
#     for func in HANDLERS.get(command, []):
#         connection.bot.launch_hook_func(func, **data)
