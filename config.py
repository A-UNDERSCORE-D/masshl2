import json
import os.path
import string
DEFAULT_CONFIG = {
            "networks": "irc.snoonet.org",
            "port": 6697,
            "SSL": True,
            "user": "MHL2",
            "nick": "MHL2",
            "gecos": "A_D's anti mass highlight bot",
            "nsident": "MHL",
            "nspass": "MHLPassword",
            "admins": ["A_D!*@*"],
            "debug": True,
            "commands": [],
            "cmdprefix": "~",
            "channels": "",
            "adminchan":
            "#HeJustKeptTalkingInOneLongIncrediblyUnbrokenSentence",
            "global_nickignore": [l for l in string.ascii_lowercase],
            "global_maskignore": ""
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
