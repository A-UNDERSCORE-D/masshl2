import importlib
from typing import TYPE_CHECKING, List, Dict
from collections import defaultdict
from hook import Hook, InitHook

if TYPE_CHECKING:
    from bot import Bot
    from event import EventManager


class PluginManager:
    def __init__(self, bot):
        self.__loaded_attribute_name = "_loaded_plugin"
        self.bot: 'Bot' = bot
        self.event_manager: 'EventManager' = self.bot.event_manager
        self.plugins: List[Plugin] = []

    def load_plugin(self, plugin_name):
        self.bot.log.debug(f"Loading plugin: {plugin_name}")
        try:
            imported_module = importlib.import_module(plugin_name)
        except Exception as e:
            self.bot.log_everywhere(f"Error during plugin load for {plugin_name}: {type(e).__name__}; {e}")
            self.bot.log.exception(e)
            return

        if hasattr(imported_module, self.__loaded_attribute_name):
            imported_module = self.reload_plugin(plugin_name)

        plugin = Plugin(imported_module, self.bot, self)
        try:
            for hook in plugin.on_load_hooks:
                self.event_manager._internal_launch(hook, **{"plugin": plugin})
        except Exception as e:
            self.bot.log_everywhere(f"Error during on load hooks for {plugin_name}: {type(e).__name__}; {e}")
            self.bot.log.exception(e)
            return

        # All hooks have succeeded, load the plugin
        self.plugins.append(plugin)
        self.event_manager.load_plugin_hooks(plugin)
        setattr(plugin.module, self.__loaded_attribute_name, None)

    def reload_plugin(self, *args) -> 'module':
        pass

    def load_all_plugins(self):
        pass


loaded_attr_name = "_loaded_hook"


class Plugin:
    def __init__(self, plugin_module: 'module', bot: 'Bot', plugin_manager: PluginManager):
        self.module = plugin_module
        self.bot: 'Bot' = bot
        self.event_manager = self.bot.event_manager
        self.plugin_manager = self.event_manager

        self.on_load_hooks: List[Hook] = []
        self.on_unload_hooks: List[Hook] = []
        self.hooks: Dict[str, List['Hook']] = defaultdict(list)

        self.__loaded_hook_name = loaded_attr_name

        self._load_hooks()

    def _load_hooks(self):
        for func in self.module.__dict__.values():
            if not callable(func):
                continue
            try:
                hooks: List[InitHook] = getattr(func, self.__loaded_hook_name)
            except AttributeError:
                # This isn't a hook
                continue

            for init_hook in hooks:
                hook = Hook(init_hook, self.bot)
                if hook.name == "on_load":
                    self.on_load_hooks.append(hook)
                elif hook.name == "on_unload":
                    self.on_unload_hooks.append(hook)
                else:
                    self.hooks[hook.name.lower()].append(hook)

            delattr(func, self.__loaded_hook_name)
        self.bot.log.debug(f"Finished loading hooks onto {self}: {self.hooks}")

    def _unload_hooks(self):
        pass

    def __str__(self):
        return f"Plugin: {self.module}"
