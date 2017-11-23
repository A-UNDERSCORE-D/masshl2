import time
import random
from pprint import pprint
from typing import TYPE_CHECKING

from bot import Bot
from hook import message, command

if TYPE_CHECKING:
    from parser import Message
    from hook import MessageHook

# TODO: Add a ~recv command, emulates hexchat's /recieve
# TODO: cycle command.


@message
def on_msg(msg: 'Message', hook):
    if not msg.target:
        return
    args = []
    if msg.message.startswith(msg.conn.cmd_prefix):
        cmd = msg.split_msg[0][1:]
        if len(msg) > 1:
            args = msg.split_msg[1:]
    elif msg.startswith(msg.conn.nick):
        if len(msg) >= 2:
            cmd = msg.split_msg[1]
            if len(msg) > 2:
                args = msg.split_msg[2:]
        else:
            return
    else:
        return

    data = {
        "msg":  msg,
        "cmd":  cmd,
        "args": args,
        "conn": msg.conn,
        "bot":  msg.bot
    }
    print("command:", hook)
    msg.bot.call_hook(f"cmd_{cmd}", **data)


@command("msgme")
def msgme(msg: 'Message', args):
    msg.origin.send_message("requested")


@command("reload", perm=["bot_control"])
def reload(msg: 'Message', args, hook):
    print(hook)
    if len(args) < 1:
        msg.target.send_message("reload requires an argument")
        return

    def todo():
        for plugin_name in args:
            if plugin_name == 'antigravity':
                msg.target.send_message("https://xkcd.com/353/")
                continue
            if not plugin_name.startswith("plugins."):
                plugin_name = "plugins." + plugin_name
            resp = msg.bot.load_plugin(plugin_name)
            if resp:
                msg.target.send_message(f"{plugin_name} failed to load. Error: '{resp}'")
                if isinstance(resp, Exception):
                    msg.conn.log.exception(resp)
            else:
                msg.target.send_message(f"Reloaded '{plugin_name}' successfully")

    return todo


@command("unload", perm=["bot_control"])
def cmd_unload(args, bot: 'Bot'):
    if args:
        def todo():
            for plugin_name in args:
                if not plugin_name.startswith("plugins."):
                    plugin_name = "plugins." + plugin_name
                bot.plugin_manager.unload_plugin(plugin_name)
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
def command_eval(bot, hook: 'MessageHook'):
    def todo():
        hook.msg.target.send_message("Test2")
    return todo


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
    pprint(bot.config)
    pprint(bot.hooks)
    return "dumped to stdout."


@command("toggle_log", perm=["bot_control"])
def cmd_log_toggle(conn):
    conn.print_raw = not conn.print_raw


@command("test_perms", perm=["bot_control"])
def cmd_test_perms(msg):
    return "Passed"


@command("restart", perm=["bot_control"])
def cmd_restart(bot, args):
    bot.restart(" ".join(args) if args else None)


@command("xyzzy")
def xyzzy():
    curtime = time.time()
    if curtime % 42 == 0 or curtime % 47 == 0:
        return "You are in a maze of twisting passages, all alike."
    else:
        return random.choice(["ok", "Ok. Nothing happens", "Nothing happens."])
