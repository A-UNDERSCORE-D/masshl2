import importlib
import inspect
import pathlib
import time
import gc
from collections import defaultdict
from selectors import DefaultSelector
from typing import Dict, List, Callable

from config import Config
from connection import Connection
from logger import Logger
from hook import Hook

class Bot:
    def __init__(self, name="masshl"):
        self.connections = []
        self.selector = DefaultSelector()
        self.config = Config()
        self.running = False
        self.is_restarting = False
        self.plugins = {}
        self.cwd = pathlib.Path().resolve()
        self.message_hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.hooks: Dict[str, List[Hook]] = defaultdict(list)
        self.name = name
        self.log = Logger(self)
        self.storage = {}

    def run(self):
        self._load_plugins()
        self.log.debug(self.hooks)
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

        self.running = False

    def restart(self, reason=None):
        if reason is None:
            reason = "Controller requested restart"
        self.is_restarting = True
        self.stop(reason)

    def _load_plugins(self):
        path = pathlib.Path("plugins").resolve().relative_to(self.cwd)
        for file in path.glob("*.py"):
            self.load_plugin('.'.join(file.parts).rsplit('.', 1)[0])
        print(self.message_hooks)

    def load_plugin(self, name):
        if not name.startswith("plugins."):
            name = "plugins." + name
        try:
            print("loading plugin", name)
            imported_module = importlib.import_module(name)
            if hasattr(imported_module, "_masshl_loaded"):
                importlib.reload(imported_module)
                if name in self.plugins:
                    self.unload(name)
            else:
                setattr(imported_module, "_masshl_loaded", None)
        except Exception as e:
            self.log.exception(e)
            return e

        else:
            setattr(imported_module, "_masshl_loaded", None)
            resp = self._run_onload_hooks(imported_module, name)
            if not isinstance(resp, Exception):
                self.plugins[name] = imported_module
                self._load_msg_hooks(imported_module, name)
                self._load_hooks(imported_module, name)
            else:
                self.log.error(f"Plugin {name} failed to load.")
                return resp

    def unload(self, name):
        if not name.startswith("plugins."):
            name = "plugins." + name
        if name in self.plugins:
            del self.plugins[name]
        if name in self.message_hooks:
            del self.message_hooks[name]
        for hooktype in self.hooks.values():
            for hook in reversed(hooktype):
                if hook.plugin == name:
                    print(f"REMOVING HOOK: {hook}")
                hooktype.remove(hook)

    def _load_msg_hooks(self, plugin, name):
        for func in plugin.__dict__.values():
            if hasattr(func, "_isMessageCallback"):
                print(func.__module__, func)
                self.message_hooks[name].append(func)
                delattr(func, "_isMessageCallback")

    def _run_onload_hooks(self, plugin, name):
        ok = True
        for func in plugin.__dict__.values():
            if hasattr(func, "_isOnLoadCallback"):
                data = {"name": name}
                try:
                    self.launch_hook_func(func, **data)
                except Exception as e:
                    ok = e
                    self.log.exception(e)
                delattr(func, "_isOnLoadCallback")
        return ok

    def _load_hooks(self, plugin, name):
        self.log(f"Loading {name}'s 'new' hooks")
        for func in plugin.__dict__.values():
            if not hasattr(func, "_IsHook"):
                continue
            hooks = getattr(func, "_IsHook")
            for hook in hooks:
                self.log(f"loading new hook {hook}: {func}")
                self.hooks[hook].append(Hook(name, func))
            delattr(func, "_IsHook")

    def launch_hook_func(self, func: Callable, **kwargs):
        sig = inspect.signature(func)
        print(f"CALLING {func}")
        kwargs["bot"] = self
        args = []
        for arg in sig.parameters:
            assert arg in kwargs, \
                f"Callback requested an argument that the hook launcher was not passed. it was '{arg}'"
            args.append(kwargs[arg])
        return func(*args)

    def call_hook(self, name, **kwargs):
        todos = []
        name = name.lower()
        if name not in self.hooks:
            return
        for hook in self.hooks[name]:
            try:
                resp = self.launch_hook_func(hook.func, **kwargs)
            except Exception as e:
                todos.append((hook, e))
            else:
                todos.append((hook, resp))
        return todos

