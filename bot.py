import gc
import pathlib
import time
from collections import defaultdict
from selectors import DefaultSelector
from typing import Dict, DefaultDict, List

from config import Config
from connection import Connection
from event import EventManager
from hook import Hook
from logger import Logger
from plugin import PluginManager


class Bot:
    def __init__(self, name="Bot") -> None:
        self.connections: List[Connection] = []
        self.selector = DefaultSelector()
        self.config = Config()
        self.running = False
        self.is_restarting = False
        self.cwd = pathlib.Path().resolve()
        self.hooks: Dict[str, List[Hook]] = defaultdict(list)
        self.name = name
        self.log = Logger(self)
        self.storage: DefaultDict[str, Dict] = defaultdict(dict)
        self.start_time = time.time()

        # If you change this var while the bot is running you WILL break things.
        self.__loaded_attribute_name = "_masshl_loaded"  # "__is_a_loaded_plugin"

        # Event Mangler
        self.event_manager: EventManager = EventManager(self)

        # Plugin Mangler
        self.plugin_manager: PluginManager = PluginManager(self)

    def run(self) -> bool:
        self._load_plugins()
        self.log.debug(f"Loaded plugins: {self.plugin_manager.plugins}")
        self.log.debug(f"Loaded hooks: {self.event_manager.events}")
        for network in self.config["connections"]:
            temp_connection = Connection(
                config=self.config["connections"][network],
                selector=self.selector, bot=self, name=network,
                debug=self.config["debug"]
            )
            self.connections.append(temp_connection)
        gc.collect()
        for connection in self.connections:
            connection.connect()

        self.running = True

        while self.running:
            event = self.selector.select(1)
            for file, _ in event:
                file.fileobj.read()
            self.call_hook("tick")
        self.selector.close()
        return self.is_restarting

    def stop(self, reason=None):
        if reason is None:
            reason = "Controller requested stop"
        for connection in self.connections:
            if not connection.hasquit:
                connection.quit(reason)
        time.sleep(1)
        for connection in self.connections:
            if connection.connected:
                connection.close()

        self.config.save()
        self.running = False

    def restart(self, reason=None):
        if reason is None:
            reason = "Controller requested restart"
        self.is_restarting = True
        self.stop(reason)

    def _load_plugins(self):
        path = pathlib.Path("plugins").resolve().relative_to(self.cwd)
        for file in path.glob("[!_]*.py"):
            self.plugin_manager.load_plugin('.'.join(file.parts).rsplit('.', 1)[0])

    def load_plugin(self, plugin_name):
        self.plugin_manager.load_plugin(plugin_name)

    def call_hook(self, name, **kwargs):
        self.event_manager.fire_event(name, **kwargs)

    def log_everywhere(self, msg):
        self.log(msg)
        self.log_adminchans(msg)

    def log_adminchans(self, msg):
        for conn in self.connections:
            conn.log_adminchan(msg)

    @property
    def plugin_data(self):
        return self.config["plugin_data"]
