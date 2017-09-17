from handler import hook_message
from parser import Message


def scan_msg(msg: 'Message'):
    count = 0
    # Get the nick list from the keys of the membership dict on the channel object
    nick_list = msg.target.memberships.keys()
    checked_nicks = set()
    lower_msg = msg.lower()
    msg.conn.log.debug(nick_list)
    for nick in nick_list:
        nick = nick.lower()
        if nick in checked_nicks:
            continue

        if nick in msg.conn.bot_nicks:
            count += 2
        else:
            if nick in lower_msg:
                count += 1
                checked_nicks.add(nick)
        if count >= msg.target.count:
            return count
        # msg.conn.log.debug(f"Count: {count}")
    return count


@hook_message
def on_msg(msg: 'Message'):
    if msg.is_chan_message:
        count = scan_msg(msg)
        # return f"count was: {count}"
