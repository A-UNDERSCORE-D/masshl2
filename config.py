import json
import os.path

config = {
    "network": "10.4.77.22",
    "port": 6667,
    "SSL": False,
    "user": "ADTEST3",
    "nick": "ADTEST3",
    "nsident": "",
    "nspass": "",
    "admins": ["A_D!*@*"]
}


if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
else:
    with open("config.json", "r") as f:
        config = json.load(f)