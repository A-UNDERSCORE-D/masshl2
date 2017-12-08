import base64

from masshl import parser
from masshl.channel import Channel
from masshl.connection import Connection
from masshl.hook import raw, unload
from masshl.logger import logall, logchan
from masshl.parser import Message


@raw("PING")
def on_ping(connection: 'Connection', args):
    connection.write("PONG :" + " ".join(args))


@raw("AUTHENTICATE")
def send_auth(connection: 'Connection'):
    auth_string = (connection.nick + "\00" + connection.nickserv_user + "\00" + connection.nickserv_pass).encode()
    connection.write("AUTHENTICATE {}".format(base64.b64encode(auth_string).decode()))


def do_sasl_auth(conn: 'Connection'):
    if conn.nickserv_user and conn.nickserv_pass:
        conn.write("AUTHENTICATE PLAIN")
    else:
        conn.log("SASL auth requested but no either no username or password was found to auth with")
        cap_decrement(conn)


def do_nickserv_auth(conn: 'Connection'):
    if conn.nickserv_user and conn.nickserv_pass:
        conn.write("PRIVMSG NickServ :IDENTIFY {nsnick} {nspass}".format(
            nsnick=conn.nickserv_user, nspass=conn.nickserv_pass
        ))
    else:
        conn.log("PRIVMSG auth requested but no either no username or password was found to auth with")


@raw("CAP")
def handle_cap(connection: 'Connection', args):
    caps = args[1].split("=")
    command = caps[0]
    if command == "LS":
        caplist = args[-1].split()
        caps = connection.caps.intersection(caplist)
        if len(caps) == 0:
            connection.write("CAP END")
        else:
            for cap in caps:
                connection.write("CAP REQ :{}".format(cap))
                cap_increment(connection)

    elif command == "ACK":
        cap = args[2]
        if cap == "sasl":
            connection.cansasl = True
            cap_increment(connection)
            do_sasl_auth(connection)
        elif cap == "userhost-in-names":
            connection.uhnames = True

        cap_decrement(connection)

    elif command == "NAK":
        cap = args[2]
        cap_decrement(connection)
        if cap == "userhost-in-names":
            connection.uhnames = False
        elif cap == "sasl":
            connection.cansasl = False


def cap_increment(connection: 'Connection'):
    connection.capcount += 1


def cap_decrement(connection: 'Connection'):
    connection.capcount -= 1
    if connection.capcount <= 0:
        connection.write("CAP END")


@raw("903")
def good_sasl(connection: 'Connection'):
    cap_decrement(connection)


@raw("904")
def bad_sasl(connection: 'Connection'):
    cap_decrement(connection)
    connection.log("SASL login failed, attempting PRIVMSG based login")
    connection.cansasl = False


@raw("001")
def on_welcome(connection: 'Connection', prefix):
    connection.server = prefix


@raw("004")
def on_my_info(connection: 'Connection', args):
    connection.user_modes = {mode for mode in args[3]}


@raw("005")
def on_isupport(connection: 'Connection', args):
    tokens = args[1:-1]
    for token in tokens:
        if "=" in token:
            token_name, _, args = token.partition("=")
            args = args or None
        else:
            token_name = token

        if token_name == "NETWORK":
            connection.network_name = token.split("=")[1]

        elif token_name == "PREFIX":
            pfx = token.split("=")[1]
            pfx, modes = pfx.split(")", 1)
            pfx = pfx[1:]
            connection.p_mode_d = dict(zip(pfx, modes))
            connection.p_modes.update(pfx)

        elif token_name == "CHANMODES":
            modes = token.split("=")[1]
            a, b, c, d = modes.split(",")
            connection.a_modes.update(a)
            connection.b_modes.update(b)
            connection.c_modes.update(c)
            connection.d_modes.update(d)

        elif token_name == "EXCEPTS":
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.ban_exemption.add(mode)

        elif token_name == "INVEX":
            mode = token.split("=")[1]
            connection.a_modes.add(mode)
            connection.invex.add(mode)

        elif token_name == "CHANTYPES":
            connection.chantypes = list(args)


@raw("376")
def on_end_motd(connection: 'Connection'):
    if not connection.cansasl:
        do_nickserv_auth(connection)
    for command in connection.commands:
        connection.write(command)
    connection.join(connection.adminchan)
    connection.join(connection.join_channels)


@raw("353")
def on_names(connection: 'Connection', args):
    names = args[3].split()
    chan: Channel = connection.channels[args[2]]

    # clear out the current user list
    if not chan.receivingnames:
        chan.receivingnames = True
        chan.memberships.clear()

    for mask in names:
        mask = mask.strip()
        admin, op, hop, voice = False, False, False, False
        # TODO: un-hardcode this
        if mask[0] in "!@%+":
            prefix = mask[0]
            mask = mask[1:]
            if prefix == "!":
                admin = True
            elif prefix == "@":
                op = True
            elif prefix == "%":
                hop = True
            elif prefix == "+":
                voice = True

        temp = connection.get_user(mask)
        chan.adduser(connection, temp, isop=op, ishop=hop,
                     isvoice=voice, isadmin=admin)


@raw("366")
def on_name_send(connection: 'Connection', args):
    chan = connection.channels[args[1]]
    chan.receivingnames = False
    logchan(chan)


@raw("JOIN")
def on_join(connection: 'Connection', prefix, args):
    name = args[0]
    chan = connection.channels.get(args[0])
    nick = prefix.split("!")[0]
    if not chan:
        chan = Channel(name, connection)
        connection.channels[name] = chan

    user = connection.get_user(prefix)

    if nick not in chan.memberships:
        chan.adduser(connection, user)
    logall(connection)


@raw("PRIVMSG")
def on_privmsg(connection: 'Connection', args, prefix):
    msg = parser.Message(connection, args, prefix, "PRIVMSG")
    on_msg(msg, connection)


@raw("NOTICE")
def onnotice(connection: 'Connection', args, prefix):
    msg = parser.Message(connection, args, prefix, "NOTICE")
    on_msg(msg, connection)


def on_msg(msg: 'Message', conn: 'Connection'):
    conn.bot.call_hook("message", msg=msg)


@raw("MODE")
def on_mode(connection: 'Connection', args):
    target = args[0]
    modes = args[1]
    mode_args = args[2:]
    adding = True
    count = 0
    if target == connection.nick:
        return
    chan = connection.channels[target]
    for mode in modes:
        if mode == "+":
            adding = True
            continue
        elif mode == "-":
            adding = False
            continue
        elif mode in connection.a_modes or mode in connection.b_modes:
            count += 1
        elif mode in connection.c_modes:
            if adding:
                count += 1
        elif mode in connection.d_modes:
            pass
        elif mode in connection.p_modes:
            nick = mode_args[count]
            connection.log(str(("+" if adding else "-") + mode + " " + nick))
            membership = chan.memberships[nick]
            if mode == "o":
                membership.is_op = adding
            elif mode == "h":
                membership.is_hop = adding
            elif mode == "v":
                membership.is_voice = adding
            elif mode == "Y":
                membership.is_admin = adding
            count += 1
            logchan(chan)


@raw("PART")
def on_part(connection: 'Connection', prefix, args):
    chan_name = args[0]
    try:
        chan = connection.channels[chan_name]
    except KeyError:
        connection.log("WTF? I just got a part for a channel I don't have, channel was {c}".format(c=chan_name))
        logall(connection)
        return

    nick = prefix.split("!")[0]
    try:
        user = chan.get_user(nick)
    except KeyError:
        connection.log("Received part for non-existent user '{}' from channel '{}'".format(nick, chan.name))
        return

    if user.nick == connection.nick:
        del connection.channels[chan.name]
        connection.log(connection.channels)
    else:
        chan.deluser(user)
    logall(connection)


@raw("KICK")
def on_kick(connection: 'Connection', args):
    kicked_nick = args[1]
    kicked_chan = args[0]

    try:
        user = connection.users[kicked_nick]
    except KeyError:
        connection.log("Handling kick for non-existent user")
        return

    try:
        chan = connection.channels[kicked_chan]
    except KeyError:
        connection.log("Handling kick from non-existent channel")
        return

    if user.nick == connection.nick:
        connection.log("We were kicked from {}".format(kicked_chan))
        del connection.channels[kicked_chan]
        connection.log(connection.channels)
    else:
        chan.deluser(user)
    logall(connection)


@raw("NICK")
def on_nick(connection: 'Connection', prefix, args):
    if not prefix:
        raise ValueError
    old_nick = prefix.split("!")[0]
    new_nick = args[0]
    if old_nick == connection.nick:
        connection.renick(new_nick)
    try:
        user = connection.users[old_nick]
    except KeyError:
        connection.log("Attempted to renick a non-existent user")
        return
    user.renick(new_nick)
    logall(connection)


@raw("QUIT")
def on_quit(connection: 'Connection', prefix):
    nick = prefix.split("!")[0]
    try:
        user = connection.users[nick]
    except KeyError:
        connection.log("Received quit from non-existent user '{}'".format(prefix))
        return

    connection.del_user(user)


# TODO: Does this still need to reload every plugin? Im not sure it does
@unload
def on_unload(bot):
    plugins = list(bot.plugins.keys())
    if __name__ in plugins:
        plugins.remove(__name__)

    def todo():
        bot.log("Reloading all plugins.")
        bot.load_plugin(plugins)

    return todo
