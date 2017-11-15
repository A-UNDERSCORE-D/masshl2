from collections import defaultdict
from typing import Dict, List
from hook import RealHook


class EventManager:
    def __init__(self, bot):
        self.events: Dict[str, List[RealHook]] = defaultdict(list)
        self.bot = bot

    def _launch_hook_functions(self, name: str, **kwargs):
        kwargs["bot"] = self.bot
        kwargs["event_manager"] = self
        returns = []
        for hook in self.events[name.lower()]:
            try:
                returns.append(hook.fire(**kwargs))
            except Exception as e:
                hook.errors.append(e)

    def fire_event(self, name: str, **kwargs):
        self._launch_hook_functions(name, **kwargs)
        self.fire_post_event(name)

    def fire_post_event(self, name):
        for hook in self.events[name]:
            hook.post_hook()

    def add_event(self, name, hook: RealHook):
        self.events[name.lower()].append(hook)

