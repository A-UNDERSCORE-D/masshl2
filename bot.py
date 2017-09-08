from connection import Connection
from config import Config
import time
from selectors import DefaultSelector
import importlib
import pathlib


class Bot:
    def __init__(self):
        self.connections = []
        self.selector = DefaultSelector()
        self.config = Config()
        self.running = False
        self.plugins = {}
        self.cwd = pathlib.Path().resolve()

    def run(self):
        self._load_plugins()
        for network in self.config["connections"]:
            temp_connection = Connection(
                config=self.config["connections"][network],
                selector=self.selector, bot=self, name=network,
                debug=self.config["debug"]
            )
            self.connections.append(temp_connection)

        for connection in self.connections:
            connection.connect()

        self.running = True

        while self.running:
            event = self.selector.select(1)
            for file, _ in event:
                file.fileobj.read()
        self.selector.close()

    def stop(self, reason):
        for connection in self.connections:
            if not connection.hasquit:
                connection.quit(reason)
        time.sleep(1)
        for connection in self.connections:
            if connection.connected:
                connection.close()

        self.running = False

    def _load_plugins(self):
        path = pathlib.Path("plugins").resolve().relative_to(self.cwd)
        for file in path.glob("*.py"):
            self._load_plugin('.'.join(file.parts).rsplit('.', 1)[0])

    def _load_plugin(self, name):
        # TODO: Unload if its there
        assert name not in self.plugins
        print("loading plugin", name)
        self.plugins[name] = importlib.import_module(name)
