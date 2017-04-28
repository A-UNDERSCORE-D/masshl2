# import irc
from connection import Connection
from config import *
import sys
import signal
# TODO: NEEDS MOAR ASCII ART!


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
        nspass=config["nspass"]
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
    print("Socket Closed. This socket is no more, it has ceased to be."
          " Its expired and gone to meet its maker. THIS IS AN EX SOCKET!", file=sys.stderr)

if __name__ == "__main__":
    run()
