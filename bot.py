import importlib
import inspect
import pathlib
import time
import gc
from collections import defaultdict
from selectors import DefaultSelector
from typing import Dict, DefaultDict, List, Callable, Union
from fnmatch import fnmatch

from config import Config
from connection import Connection
from logger import Logger
from hook import InitHook, Hook
from permissions import check
from event import EventManager


class Bot:
    def __init__(self, name="Bot") -> None:
        self.connections: List[Connection] = []
        self.selector = DefaultSelector()
        self.config = Config()
        self.running = False
        self.is_restarting = False
        self.plugins = {}
        self.cwd = pathlib.Path().resolve()
        self.hooks: Dict[str, List[Hook]] = defaultdict(list)
        self.name = name
        self.log = Logger(self)
        self.storage: DefaultDict[str, Dict] = defaultdict(dict)
        self.start_time = time.time()

        # Event Mangler
        self.event_manager = EventManager(self)

    def run(self) -> bool:
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
            self.load_plugin('.'.join(file.parts).rsplit('.', 1)[0])

    def load_plugin(self, name: Union[List, str]):
        if name == "*":
            resp = self.load_plugin(list(self.plugins.keys()))
            for r in resp:
                print(r)
            return
        if isinstance(name, list):
            resp = []
            for plugin in name:
                print(self.load_plugin(plugin))
            return resp
        print(f"LOADING {name}")
        if not name.startswith("plugins."):
            name = "plugins." + name
        try:
            print("loading plugin", name)
            imported_module = importlib.import_module(name)
            if hasattr(imported_module, "_masshl_loaded"):
                print(f"CALLING RELOAD FOR {name}")
                importlib.reload(imported_module)
                if name in self.plugins:
                    print(f"CALLING UNLOAD FOR {name}")
                    self.unload(name)
            else:
                setattr(imported_module, "_masshl_loaded", None)
        except Exception as e:
            self.log.exception(e)
            return e

        else:
            setattr(imported_module, "_masshl_loaded", None)
            self._load_hooks(imported_module, name, "on_load*")
            responses = self.call_hook(f"on_load_{name}")
            ok = True
            for resp in responses:
                if isinstance(resp, Exception):
                    ok = False
            if not ok:
                self.log.error(f"Plugin {name} failed to load.")
                return

            self.plugins[name] = imported_module
            self._load_hooks(imported_module, name)

    def unload(self, name):
        if not name.startswith("plugins."):
            name = "plugins." + name

        self.event_manager.fire_event(f"on_unload_{name}")
        self.event_manager.remove_plugin_hooks(name)
        if name in self.plugins:
            del self.plugins[name]
            self.log.debug(f"REMOVING PLUGIN: {name}")
        # todo = []
        # for hook_name, hook_list in self.hooks.items():
        #     for hook in reversed(hook_list):
        #         if hook.plugin == name:
        #             if hook_name == f"on_unload_{name}":
        #                 todo.extend(self.call_hook(f"on_unload_{name}"))
        #             self.log.debug(f"REMOVING HOOK: {hook_name}: {hook}")
        #             hook_list.remove(hook)
        # self._cleanup_hooks()
        # self.handle_todos(todo)

    def _cleanup_hooks(self):
        new_hooks = {n: h for n, h in self.hooks.items() if h}
        self.hooks.clear()
        self.hooks.update(new_hooks)
        print(self.hooks)

    def _load_hooks(self, plugin, name, filters: str =None):
        self.log.debug(f"Loading {name}'s hooks." + (f" Filtered to {filters}" if filters else ""))
        for func in plugin.__dict__.values():
            if not callable(func):
                continue
            try:
                hooks = getattr(func, "_IsHook")
            except AttributeError:
                continue
            for hook in hooks:
                if filters is not None and not fnmatch(hook.hook_name, filters):
                    self.log.debug(f"SKIPPING {hook}, does not match filter ('{filters}')")
                    continue
                else:
                    to_log = f"loading new hook: {hook}"
                    if hook.data:
                        to_log += f" Hook has data; {hook.data}"
                    self.log.debug(to_log)
                    real_hook = hook.real_hook(hook, self)
                    self.event_manager.add_hook(hook.hook_name, real_hook)
                    delattr(func, "_IsHook")

    def launch_hook_func(self, func: Callable, **kwargs):
        sig = inspect.signature(func)
        kwargs["bot"] = self
        kwargs["start_time"] = self.start_time
        args = []
        for arg in sig.parameters:
            assert arg in kwargs, \
                f"Callback requested an argument that the hook launcher was not passed. it was '{arg}'"
            args.append(kwargs[arg])
        return func(*args)

    def call_hook(self, name, handle_errors=True, **kwargs) -> list:
        self.event_manager.fire_event(name, **kwargs)
        return []

        # tds = []
        # for hook in self.hooks[name.lower()]:
        #     tds.append(hook.fire(**kwargs))
        # for todo in tds:
        #     if callable(todo):
        #         todo()
        #         tds.remove(todo)
        # return tds


        # todos = []
        # name = name.lower()
        # if name not in self.hooks:
        #     return todos
        # for hook in self.hooks[name]:
        #     if hook.perms and not check(kwargs["msg"], hook.perms):
        #         kwargs["msg"].origin.send_notice("Sorry, you are not allowed to use this command")
        #         continue
        #     try:
        #         resp = self.launch_hook_func(hook.func, **kwargs)
        #     except Exception as e:
        #         todos.append((hook, e))
        #         self.log.exception(e)
        #         if handle_errors:
        #             self.log(f"Exception in {name}: {hook}")
        #             self.log_adminchans(f"Exception in {hook}: {type(e).__name__}: {str(e)}")
        #     else:
        #         todos.append((hook, resp))
        # return todos

    def handle_todos(self, todos, ret=False) -> list:
        resp = []
        for hook, todo in todos:
            if isinstance(todo, list):
                resp.extend(self.handle_todos(todo, True))
            if callable(todo):
                todo()
            elif ret:
                resp.append(todo)
            elif todo:
                self.log(f"{hook}: {todo}")
        return resp

    def log_everywhere(self, msg):
        self.log(msg)
        self.log_adminchans(msg)

    def log_adminchans(self, msg):
        for conn in self.connections:
            conn.log_adminchan(msg)

    @property
    def plugin_data(self):
        return self.config["plugin_data"]
