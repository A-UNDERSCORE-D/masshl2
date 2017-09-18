import signal
import sys
import time
import os
from random import choice

from bot import Bot

# TODO: NEEDS MOAR ASCII ART!

exits = ["Socket Closed. This socket is no more, it has ceased to be. Its expired and gone to meet its maker. "
         "THIS IS AN EX SOCKET!",
         "\"VOOM\"!? This socket wouldn't \"voom\" if you put four million volts through it!",
         "This socket does not know how not to be seen",
         "Socket, will you stand up please"
         ]


def run():
    print("MASSHL 2.0")
    print("By A_D")
    original_handler = signal.getsignal(signal.SIGINT)
    stopped = False
    bot = Bot()

    # Called when we receive SIGINT, exits the connection gracefully
    def interrupted(signo, frame):
        if bot:
            bot.stop("Caught SIGINT")
        else:
            nonlocal stopped
            stopped = True
        # bot.selector.close()

        signal.signal(signal.SIGINT, original_handler)

    signal.signal(signal.SIGINT, interrupted)

    restart = bot.run()
    if restart:
        time.sleep(0.5)
        if stopped:
            print("Stopped while restarting.")
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)

    print(choice(exits), file=sys.stderr)


if __name__ == "__main__":
    run()
