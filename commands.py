from logger import *


def commands(connection, args, prefix):
    msg = args[1]
    if msg == "~print":
        log("---------------MODES--------------------------")
        log("A: " + str(connection.Amodes))
        log("B: " + str(connection.Bmodes))
        log("C: " + str(connection.Cmodes))
        log("D: " + str(connection.Dmodes))
        log("P: " + str(connection.Pmodes))
    elif msg == "~die":
        connection.write("QUIT :Controller requested disconnect")
