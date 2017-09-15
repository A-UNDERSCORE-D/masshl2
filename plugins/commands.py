from handler import message
from typing import TYPE_CHECKING, Dict, Callable, NamedTuple
import permissions
if TYPE_CHECKING:
    from parser import Message
# from logger import *

# TODO: for masshl, channel notice checking too

# COMMANDS: Dict[str, List[Union[Callable, List, None]]] = {}


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


@message
def on_msg(msg: 'Message'):
    if not msg.message.startswith(msg.conn.cmdprefix):
        return

    cmd = msg.s_msg[0][1:]

    if len(msg) > 1:
        args = msg.s_msg[1:]
    else:
        args = []

    handler = COMMANDS.get(cmd)
    if handler and callable(handler.callback):
        if handler.perms and not permissions.check(msg, handler.perms):
            return "Perm check failed."
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


@command("reload")
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
                msg.target.send_message(str(resp))
            else:
                msg.target.send_message(f"Reloaded '{plugin_name}' successfully")

    return todo


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


@command("eval", perm=["admin"])
def command_eval(bot, conn):
    return "Perms Checked"
