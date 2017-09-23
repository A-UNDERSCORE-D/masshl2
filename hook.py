from typing import Callable


def hook(*name, func=None):
    def _decorate(f):
        try:
            hook_list = getattr(f, "_IsHook")
        except AttributeError:
            hook_list = []
            setattr(f, "_IsHook", hook_list)
        hook_list.extend(_hook.lower() for _hook in name)
        return f
    if func is not None:
        _decorate(func)
    else:
        return _decorate


def raw(*name):
    return hook(*(("raw_" + n) for n in name))


def load(name):
    return hook(f"on_load_{name}")


def unload(name):
    return hook(f"on_unload_{name}")


def channel_init(func):
    return hook("channel_init", func=func)


class Hook:
    def __init__(self, plugin: str, func: Callable):
        self.plugin: str = plugin
        self.func: Callable = func

    def __str__(self):
        return f"{self.plugin}: {self.func}"
