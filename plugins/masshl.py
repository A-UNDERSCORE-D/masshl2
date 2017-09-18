from handler import hook_message
from parser import Message


def sanitise_nicklist(msg: 'Message') -> set:
    nicks = set()
    for nick in msg.target.memberships:
        if len(nick) < 2 or nick == msg.origin or nick in msg.conn.global_nickignore or nick in msg.target.nick_ignore:
            continue
        nicks.add(nick)
    return nicks


def check_msg(msg: 'Message') -> int:
    nick_list = sanitise_nicklist(msg)
    checked_nicks = set()
    count = 0

    for nick in nick_list:
        if nick in msg and nick not in checked_nicks:
            checked_nicks.add(nick)
            count += 1
            if nick in msg.conn.bot_nicks:
                count += 1
    return count


@hook_message
def on_msg(msg: 'Message'):
    if msg.is_chan_message:
        count = check_msg(msg)
        msg.conn.log(f"Count: {count}")
        if count > 0:
            return f"count was: {count}"
