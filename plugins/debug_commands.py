from hook import command
import json


@command("event_manager", "bot_control")
def eventmanager_command(bot, event_manager, args):
    if len(args) < 1:
        return "You must supply an argument."
    subcommand = args.pop(0).lower()

    if subcommand == "debug":
        event_manager.debug = not event_manager.debug


@command("command_debug")
def command_debug(bot):
    tmp = {}
    for e in bot.event_manager.events:
        tmp[e] = [str(x) for x in bot.event_manager.events[e]]
    print(json.dumps(tmp, indent=2))
    return "Dumped to stdout"
