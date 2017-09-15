from connection import Connection
from config import Config
import time
from selectors import DefaultSelector
import importlib
import pathlib
import inspect
from logger import Logger
from collections import defaultdict
from typing import Dict, List, Callable


class Bot:
    def __init__(self):
        self.connections = []
        self.selector = DefaultSelector()
        self.config = Config()
        self.running = False
        self.plugins = {}
        self.cwd = pathlib.Path().resolve()
        self.message_hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.name = "masshl"
        self.log = Logger(self)

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

    def stop(self, reason="Controller requested stop"):
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
            self.load_plugin('.'.join(file.parts).rsplit('.', 1)[0])
        print(self.message_hooks)

    def load_plugin(self, name):
        try:
            if name in self.plugins:
                self.unload(name)
            print("loading plugin", name)
            imported_module = importlib.import_module(name)
            if hasattr(imported_module, "_masshl_loaded"):
                importlib.reload(imported_module)
            else:
                setattr(imported_module, "_masshl_loaded", None)

        except Exception as e:
            self.log.exception(e)
            return e

        else:
            setattr(imported_module, "_masshl_loaded", None)
            self.plugins[name] = imported_module
            self._load_msg_hooks(imported_module, name)

    def unload(self, name):
        if name in self.plugins:
            del self.plugins[name]
        if name in self.message_hooks:
            del self.message_hooks[name]

    def _load_msg_hooks(self, plugin, name):
        for func in plugin.__dict__.values():
            if hasattr(func, "_isMessageCallback"):
                print(func.__module__, func)
                self.message_hooks[name].append(func)
                delattr(func, "_isMessageCallback")

    @staticmethod
    def launch_hook(func: Callable, **kwargs):
        sig = inspect.signature(func)
        args = []
        for arg in sig.parameters:
            assert arg in kwargs
            args.append(kwargs[arg])
        return func(*args)
