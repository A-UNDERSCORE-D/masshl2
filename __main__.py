# import irc
from connection import Connection
from config import Config
import sys
import signal
from random import choice
import time
from selectors import DefaultSelector, EVENT_READ
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
    config = Config()
    original_handler = signal.getsignal(signal.SIGINT)
    selector = DefaultSelector()
    connection = Connection(config=config, selector=selector)
    connection.connect()
    selector.register(connection, EVENT_READ)

    # Called when we receive SIGINT, exits the connection gracefully
    def interrupted(signo, frame):
        connection.quit("Killed by user.")
        time.sleep(1)
        connection.close()
        signal.signal(signal.SIGINT, original_handler)

    signal.signal(signal.SIGINT, interrupted)

    while connection.connected:
        events = selector.select(1)
        for sock, _ in events:
            sock.fileobj.read()
    print(choice(exits),
          file=sys.stderr)

if __name__ == "__main__":
    run()
