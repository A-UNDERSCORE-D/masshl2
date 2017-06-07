from logger import *


def checknicks(connection, msg, chan):
    nicklist = list(filter(lambda x: x not in connection.global_nickignore
                           and x not in chan.nickignore, chan.nicklist))
    matchednicks = set(filter(lambda x: x in nicklist, msg.split()))
    logcentered("CHECKNICKS-TEST")
    log(str(matchednicks))
    log(str(len(matchednicks)))
