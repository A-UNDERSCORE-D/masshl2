from handler import hook_message
from typing import TYPE_CHECKING, Dict, Callable, NamedTuple

import permissions
if TYPE_CHECKING:
    from parser import Message


class CommandHook(NamedTuple):
    callback: Callable
    perms: tuple = None


COMMANDS: Dict[str, CommandHook] = {}


def command(*cmds, perm=None):
    def _decorate(func):
        for cmd in cmds:
            assert cmd not in COMMANDS
            COMMANDS[cmd] = CommandHook(func, perms=tuple(perm or []))
        return func
    return _decorate


@hook_message
def on_msg(msg: 'Message'):
    args = []
    if msg.message.startswith(msg.conn.cmdprefix):
        cmd = msg.s_msg[0][1:]
        if len(msg) > 1:
            args = msg.s_msg[1:]
    elif msg.startswith(msg.conn.nick):
        cmd = msg.s_msg[1]
        if len(msg) > 2:
            args = msg.s_msg[2:]
    else:
        return

    handler = COMMANDS.get(cmd)
    if handler and callable(handler.callback):
        if handler.perms and not permissions.check(msg, handler.perms):
            msg.origin.send_notice("Sorry, you are not allowed to use this command")
            return
        func = handler.callback
        data = {
            "msg": msg,
            "cmd": cmd,
            "args": args,
            "conn": msg.conn,
            "bot": msg.bot
        }
        return msg.bot.launch_hook(func, **data)


@command("msgme")
def msgme(msg: 'Message', args):
    msg.origin.send_message("requested")


@command("reload", perm=["bot_control"])
def reload(msg: 'Message', args):
    if len(args) < 1:
        msg.target.send_message("reload requires an argument")
        return

    def todo():
        for plugin_name in args:
            if plugin_name == 'antigravity':
                msg.target.send_message("https://xkcd.com/353/")
                continue
            resp = msg.bot.load_plugin(plugin_name)
            if resp:
                msg.target.send_message(f"{plugin_name} failed to load. Error: '{resp}'")
            else:
                msg.target.send_message(f"Reloaded '{plugin_name}' successfully")

    return todo


@command("unload", perm=["bot_control"])
def cmd_unload(args, bot):
    if args:
        def todo():
            for arg in args:
                bot.unload(arg)
            return f"{' '.join(args)} unloaded"
        return todo
    else:
        return "This command requires an argument"


@command("say")
def say(args):
    return " ".join(args)


@command("print")
def cmd_print(msg):
    return str(msg.bot.message_hooks)


@command("raw")
def cmd_raw(conn, args):
    if len(args) < 1:
        return "raw requires an argument"
    conn.write(" ".join(args))


@command("die")
def cmd_die(bot):
    bot.stop()


@command("join")
def cmd_join(conn, args):
    if len(args) < 1:
        return "join requires an argument"
    conn.join(args)


@command("part")
def cmd_part(args, conn):
    if len(args) < 1:
        return "part requires an argument"
    chans = []
    reason = "Controller requested part"
    for chan in args:
        if chan.startswith(":"):
            reason = chan
            continue
        chans.append(chan)
    conn.part(chans, reason)


@command("eval", perm=["bot_control"])
def command_eval(bot, conn):
    return "Perms Checked"


@command("config", perm=["bot_control"])
def cmd_config(bot, msg):
    if len(msg) < 1:
        return "config requires an argument"
    subcommand = msg.s_msg[1]
    if subcommand == "save":
        name = None
        if len(msg) > 2:
            name = msg.s_msg[2]
        msg.target.send_message(str(name))
        msg.target.send_message(len(msg))
        bot.config.save(name)

    elif subcommand == "load":
        name = None
        if len(msg) > 2:
            name = msg[2]
        bot.config.load(name)

    elif subcommand == "update":
        bot.config.update_f_m()


@command("dump_config")
def cmd_dumpcfg(bot):
    print(bot.config)
    return "dumped to stdout."


@command("toggle_log", perm=["bot_control"])
def cmd_logtoggle(conn):
    conn.print_raw = not conn.print_raw


@command("restart", perm=["bot_control"])
def cmd_restart(bot, args):
    bot.restart(" ".join(args) if args else None)
