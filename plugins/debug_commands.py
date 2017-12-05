from typing import TYPE_CHECKING
from hook import command
import json

from parser import parse_modes

if TYPE_CHECKING:
    from bot import Bot
    from event import EventManager
    from channel import Channel
    from parser import Message


@command("event_manager", "bot_control")
def eventmanager_command(bot: 'Bot', event_manager: 'EventManager', args):
    if len(args) < 1:
        return "You must supply an argument."
    subcommand = args.pop(0).lower()

    if subcommand == "toggle_debug":
        event_manager.debug = not event_manager.debug
        return f"Event manager debug set to {event_manager.debug}"

    elif subcommand == "print":
        print(event_manager.events)
        return "Dumped to stdout."

    elif subcommand == "pretty_print":
        for event in event_manager.events:
            print(event)
            for hook in event_manager.events[event]:
                print(f"`- {hook}")
        return "Dumped to stdout."

    elif subcommand == "cleanup":
        def cleanup():
            event_manager._cleanup_events()
        return cleanup


@command("command_debug")
def command_debug(bot):
    tmp = {}
    for e in bot.event_manager.events:
        tmp[e] = [str(x) for x in bot.event_manager.events[e]]
    print(json.dumps(tmp, indent=2))
    return "Dumped to stdout"


@command("dump_connections")
def conn_debug(bot):
    return bot.connections


@command("test_mode")
def test_mode(target: 'Channel', msg: 'Message', conn):
    print(msg.eol_msg)
    return parse_modes(msg.eol_msg[1], conn)
