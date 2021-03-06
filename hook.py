from typing import Callable, List


def hook(*name, func=None, permissions=None):
    def _decorate(f):
        try:
            hook_list = getattr(f, "_IsHook")
        except AttributeError:
            hook_list = []
            setattr(f, "_IsHook", hook_list)
        hook_list.extend((_hook.lower(), permissions) for _hook in name)
        return f
    if func is not None:
        return _decorate(func)
    else:
        return _decorate


def raw(*name):
    return hook(*(("raw_" + n) for n in name))


def message(func):
    return hook("message", func=func)


def load(func):
    return hook(f"on_load_{str(func.__module__)}", func=func)


def unload(func):
    return hook(f"on_unload_{func.__module__}", func=func)


def channel_init(func):
    return hook("channel_init", func=func)


def command(*name, perm=None):
    return hook(*(("cmd_" + n) for n in name), permissions=perm)


class Hook:
    def __init__(self, plugin: str, func: Callable, req_perms: List =None):
        self.plugin: str = plugin
        self.func: Callable = func
        self.perms: List = req_perms if req_perms is not None else []

    def __str__(self):
        return f"{self.plugin}: {self.func}"
