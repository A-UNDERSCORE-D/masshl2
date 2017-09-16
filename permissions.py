from fnmatch import fnmatch
from channel import Channel


def check(msg, perms):
    # check global admins first, then channel. then do special cases for "is_op"/hop etc
    mask = msg.origin.mask
    msg.conn.log(mask)
    for perm in perms:
        assert perm in ("bot_control", "chan_admin")
        if perm == "bot_control":
            for c in msg.conn.admins:
                if fnmatch(mask, c):
                    return True

        if perm == "chan_admin":
            if msg.target is Channel:
                for a in msg.target.admins:
                    if fnmatch(mask, a):
                        return True
    return False
