from typing import Callable, List


# TODO: Is there a reason this doesnt just load the Hook object onto the attribute?
def hook(*name, func=None, permissions=None, data=None) -> Callable:
    def _decorate(f):
        try:
            hook_list = getattr(f, "_IsHook")
        except AttributeError:
            hook_list = []
            setattr(f, "_IsHook", hook_list)
        # hook_list.extend((_hook.lower(), permissions) for _hook in name)
        hook_list.extend((Hook(_hook.lower(), f.__module__, f, permissions, data) for _hook in name))
        return f
    if func is not None:
        return _decorate(func)
    else:
        return _decorate


class Hook:
    def __init__(self, hook_name: str, plugin: str, func: Callable, req_perms: List = None, data=None):
        self.hook_name = hook_name
        self.plugin = plugin
        self.func = func
        self.perms: List = req_perms if req_perms is not None else []
        self.data = data

    def __str__(self):
        return f"{self.hook_name}: {self.plugin}; {self.func}"


# Below are for ease of use


def raw(*name) -> Callable:
    return hook(*(("raw_" + n) for n in name))


def message(func) -> Callable:
    return hook("message", func=func)


def load(func) -> Callable:
    return hook(f"on_load_{str(func.__module__)}", func=func)


def unload(func) -> Callable:
    return hook(f"on_unload_{func.__module__}", func=func)


def channel_init(func) -> Callable:
    return hook("channel_init", func=func)


def command(*name, perm=None) -> Callable:
    return hook(*(("cmd_" + n) for n in name), permissions=perm)


def connect_finish(func) -> Callable:
    return hook("connect_finish", func=func)


def tick(func) -> Callable:
    return hook("tick", func=func)


# Timer isn't guaranteed to happen at the time, but will never be early
def timer(time) -> Callable:
    return hook(f"timer_{time}")
