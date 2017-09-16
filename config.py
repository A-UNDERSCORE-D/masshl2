import json
import os.path
import string

DEFAULT_CONFIG = {
    "connections": {
        "snoonet": {
            "network": "irc.snoonet.org",
            "port": 6697,
            "SSL": True,
            "user": "MHL2",
            "nick": "MHL2",
            "gecos": "A_D's anti mass highlight bot",
            "nsident": "MHL",
            "nspass": "MHLPassword",
            "admins": ["A_D!*@*"],
            "commands": [],
            "cmdprefix": "~",
            "channels": "",
            "adminchan":
                "#HeJustKeptTalkingInOneLongIncrediblyUnbrokenSentence",
            "global_nickignore": [l for l in string.ascii_lowercase],
            "global_maskignore": "",
            # debug or similar configs
            "print_raw": True
        },
    },

    "debug": True,
}


class Config(dict):
    def __init__(self, name: str = "config"):
        super().__init__()
        self.name = name
        self.clear()
        self.update(DEFAULT_CONFIG)
        self.load(self.name)

    def load(self, name=None):
        if not name:
            name = self.name
        if not os.path.exists(name + ".json"):
            with open(name + ".json", "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)

        with open(name + ".json") as f:
            self.update(json.load(f))

    def save(self, name=None):
        if not name:
            name = self.name
        with open(name, "w") as f:
            json.dump(self, f, indent=2)

    def update_f_m(self):
        self.update(DEFAULT_CONFIG)
        with open(self.name + ".json") as f:
            self.update(json.load(f))
        with open(self.name + ".json", "w") as f:
            json.dump(self, f, indent=2)
