from typing import Callable


def hook(*name):
    def _decorate(func):
        try:
            hook_list = getattr(func, "_IsHook")
        except AttributeError:
            hook_list = []
            setattr(func, "_IsHook", hook_list)
        hook_list.extend(_hook.lower() for _hook in name)
        return func
    return _decorate


class Hook:
    def __init__(self, plugin: str, func: Callable):
        self.plugin: str = plugin
        self.func: Callable = func

    def __str__(self):
        return f"{self.plugin}: {self.func}"
