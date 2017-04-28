# import irc
from connection import Connection
from config import *
from handler import handler
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
    while True:
        connection.read()


if __name__ == "__main__":
    run()
