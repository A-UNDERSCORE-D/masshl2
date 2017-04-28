import json
import os.path

config = {
    "network": "",
    "port": 6697,
    "SSL": True,
    "user": "MHL2",
    "nick": "MHL2",
    "nsident": "MHL",
    "nspass": "MHLPassword",
    "admins": ["A_D!*@*"],
    "debug": True
}

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

with open("config.json") as f:
    config = json.load(f)
