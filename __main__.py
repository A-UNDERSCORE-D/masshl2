# import irc
from connection import Connection
from config import *
import sys
import signal
from random import choice
# TODO: NEEDS MOAR ASCII ART!

exits = ["Socket Closed. This socket is no more, it has ceased to be. Its "
         "expired and gone to meet its maker. THIS IS AN EX SOCKET!",
         "\"VOOM\"!? This socket wouldn't \"voom\" if you put four million "
         "volts through it!",
         "This socket does not know how not to be seen",
         "Socket, will you stand up please"
         ]


def run():
    print("MASSHL 2.0")
    print("By A_D")
    connection = Connection(
        port=config["port"],
        host=config["network"],
        isssl=config["SSL"],
        nick=config["nick"],
        user=config["user"],
        nsuser=config["nsident"],
        nspass=config["nspass"],
        commands=config["commands"],
        debug=config["debug"],
        channels=config["channels"]
    )
    connection.connect()
    original_handler = signal.getsignal(signal.SIGINT)

    # Called when we receive SIGINT, exits the connection gracefully
    def interrupted(signo, frame):
        connection.quit("Killed by user.")
        connection.close()
        signal.signal(signal.SIGINT, original_handler)

    signal.signal(signal.SIGINT, interrupted)

    while connection.connected:
        connection.read()
    print(choice(exits),
          file=sys.stderr)

if __name__ == "__main__":
    run()
