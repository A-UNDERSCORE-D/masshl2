import json
import os.path

DEFAULT_CONFIG = {
            "network": "",
            "port": 6697,
            "SSL": True,
            "user": "MHL2",
            "nick": "MHL2",
            "gecos": "A_D's anti mass highlight bot",
            "nsident": "MHL",
            "nspass": "MHLPassword",
            "admins": ["A_D!*@*"],
            "debug": True,
            "commands": ["JOIN ##ldtest"],
            "cmdprefix": "~",
            "channels": "#ADTEST",
            "adminchan":
            "#HeJustKeptTalkingInOneLongIncrediblyUnbrokenSentence"
        }


class Config(dict):

    def __init__(self, name: str ="config"):
        super().__init__()
        self.name = name
        self.clear()
        self.update(DEFAULT_CONFIG)
        self.load(self.name)

    def load(self, name):
        if not os.path.exists(name + ".json"):
            with open(name + ".json", "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)

        with open(name + ".json") as f:
            self.update(json.load(f))

    def __getattr__(self, item):
        if item in self:
            return self.get(item)
        else:
            raise AttributeError(item + " Not found")

    def save(self, name):
        with open(name) as f:
            json.dump(self, f, indent=2)
