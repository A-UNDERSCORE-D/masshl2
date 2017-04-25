import time


def log(data: str, ltype: str ="log",):
    if ltype in ["ircin", "ircout", "log"]:
        if ltype == "ircin":
            print(time.asctime(), " : >>", data)
        elif ltype == "ircout":
            print(time.asctime(), " : <<", data)
        elif ltype == "log":
            print(time.asctime(), " : >!", data)
    else:
        raise ValueError("Unknown Log Type")