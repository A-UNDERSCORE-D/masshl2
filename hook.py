from typing import Callable, Dict, List, TYPE_CHECKING
import inspect
import permissions

if TYPE_CHECKING:
    from parser import Message


# Hook is loaded onto a function as an attribute by the hook function, its used to build a RealHook that is loaded onto
# a bots EventManager
class InitHook:
    def __init__(self, hook_name: str, plugin: str, func: Callable, real_hook: 'Hook', data=None):
        self.hook_name = hook_name
        self.plugin = plugin
        self.func = func
        self.data: Dict = data if data is not None else {}
        self.real_hook = real_hook

    def __str__(self):
        return f"{self.hook_name}: {self.plugin}; {self.func}"


# A RealHook represents a fireable hook, and can be subclassed to change the behaviour of returns etc
class Hook:
    def __init__(self, init_hook: InitHook, bot):
        self.errors = []
        self.bot = bot
        self.name = init_hook.hook_name
        self.plugin = init_hook.plugin
        self.func = init_hook.func
        self.data = init_hook.data
        self.todo = []
        self.type = type(self)

    def __str__(self):
        return f"{self.type} '{self.name}': {self.plugin}; {self.func}"

    def fire(self, **kwargs):
        sig = inspect.signature(self.func)
        kwargs["bot"] = self.bot
        kwargs["start_time"] = self.bot.start_time
        kwargs["hook"] = self
        args = []
        try:
            for arg in sig.parameters:
                assert arg in kwargs, \
                    f"Callback requested an argument that the hook launcher was not passed. it was '{arg}'"
                args.append(kwargs[arg])
            ret = self.func(*args)
            if ret:
                self.todo.append(ret)
        except Exception as error:
            # To allow subclasses to change how this behaves
            self.handle_error(error)

    def handle_error(self, error):
        self.bot.log_everywhere(f"exception in {self}. {type(error).__name__}: {str(error)}. See stdout for trace.")
        self.bot.log.exception(error)

    def handle_return(self):
        if self.todo:
            print(self.todo)
        done = []
        for todo in self.todo:
            if callable(todo):
                todo()
            else:
                self.bot.log(todo)
            done.append(todo)
        self.todo[:] = [t for t in self.todo if t not in done]

    def post_hook(self):
        self.handle_return()


class MessageHook(Hook):
    def __init__(self, init_hook: InitHook, bot) -> None:
        super().__init__(init_hook, bot)
        self.msg: 'Message' = None

    def pre_fire(self, kwargs):
        self.msg = kwargs["msg"]

    def fire(self, **kwargs):
        self.pre_fire(kwargs)
        return super().fire(**kwargs)

    def handle_return(self):
        done = []
        print(self, self.todo)
        for todo in self.todo:
            msg = ""
            if callable(todo):
                msg = todo()
            else:
                msg = str(todo)
            if msg:
                self.msg.target.send_message(msg)
            done.append(todo)
        self.todo[:] = [t for t in self.todo if t not in done]


class CommandHook(MessageHook):
    def __init__(self, init_hook: InitHook, bot):
        super().__init__(init_hook, bot)
        self.permissions: List = self.data.get("permissions", [])

    def fire(self, **kwargs):
        self.pre_fire(kwargs)
        if not self.permissions or permissions.check(self.msg, self.permissions):
            return super().fire(**kwargs)
        elif self.msg.has_origin:
            self.msg.origin.send_notice("Sorry, you are not allowed to use this command.")
            return False


def hook(*name, real_hook=Hook, func=None, data=None) -> Callable:
    def _decorate(f):
        # TODO: Is a third file a better idea for this? or perhaps making it a config?
        # because circular imports.
        from plugin import loaded_attr_name
        try:
            hook_list = getattr(f, loaded_attr_name)
        except AttributeError:
            hook_list = []
            setattr(f, loaded_attr_name, hook_list)
        # hook_list.extend((_hook.lower(), permissions) for _hook in name)
        hook_list.extend((InitHook(_hook.lower(), f.__module__, f, real_hook, data) for _hook in name))
        return f

    if func is not None:
        return _decorate(func)
    else:
        return _decorate


# Below are for ease of use
def raw(*name) -> Callable:
    return hook(*(("raw_" + n) for n in name))


def message(func) -> Callable:
    return hook("message", func=func, real_hook=MessageHook)


def load(func) -> Callable:
    return hook("on_load", func=func)


def unload(func) -> Callable:
    return hook("on_unload", func=func)


def channel_init(func) -> Callable:
    return hook("channel_init", func=func)


def command(*name, perm=None) -> Callable:
    data = {}
    if perm:
        if isinstance(perm, list):
            data["permissions"] = perm
        else:
            data["permissions"] = [perm]
    return hook(*(("cmd_" + n) for n in name), real_hook=CommandHook, data=data)


def connect_finish(func) -> Callable:
    return hook("connect_finish", func=func)


def tick(func) -> Callable:
    return hook("tick", func=func)


# Timer isn't guaranteed to happen at the time, but will never be early
def timer(time) -> Callable:
    return hook(f"timer_{time}")
