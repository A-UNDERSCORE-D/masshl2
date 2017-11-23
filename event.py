from collections import defaultdict
from typing import Dict, List
from hook import Hook, command


# TODO: figure out why ~unload is not responding in-channel.
from plugin import Plugin


class EventManager:
    def __init__(self, bot) -> None:
        self.events: Dict[str, List[Hook]] = defaultdict(list)
        self.bot = bot
        self.debug = False

    def _internal_launch(self, hook: Hook, **kwargs):
        kwargs["bot"] = self.bot
        kwargs["event_manager"] = self
        hook.fire(**kwargs)

    # for external firing of single hook objects.
    def naked_fire(self, hook: Hook, **kwargs):
        return self._internal_launch(hook, **kwargs)

    def _launch_hook_functions(self, name: str, **kwargs):
        for hook in self.events[name.lower()]:
            self._internal_launch(hook, **kwargs)

    def fire_event(self, name: str, **kwargs):
        if not name.startswith("tick"):
            self.debug_log(f"[EVENT MANAGER] running hook: {name}")
        self._launch_hook_functions(name, **kwargs)
        self.fire_post_event(name)

    def fire_post_event(self, name):
        for hook in self.events[name]:
            hook.post_hook()

    def _cleanup_events(self):
        new_hooks = {n: h for n, h in self.events.items() if h}
        self.events.clear()
        self.events.update(new_hooks)

    def add_hook(self, name, hook: Hook):
        self.events[name.lower()].append(hook)

    def load_plugin_hooks(self, plugin: Plugin):
        self.debug_log(f"Loading hooks for {plugin}")
        for event in plugin.hooks:
            self.debug_log(f"`-Loading hook: {event}: {plugin.hooks[event]}")
            self.events[event] += plugin.hooks[event]

    def remove_plugin_hooks(self, plugin_name):
        self.bot.log(f"[EVENT MANAGER] unloading {plugin_name}")
        for hook_name, hook_list in self.events.items():
            to_remove = []
            for hook in hook_list:
                if hook.plugin == plugin_name:
                    self.debug_log(f"[EVENT MANAGER] Removing hook: {hook}")
                    to_remove.append(hook)
            for hook in to_remove:
                hook_list.remove(hook)
        self._cleanup_events()

    def debug_log(self, msg):
        if not self.debug:
            return
        self.bot.log.debug(msg)
