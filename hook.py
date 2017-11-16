from typing import Callable, List, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from parser import Message

# TODO: make hooks manage the firing of events, or create an event object that stores hooks and fires them when needed.


class Hook:
    def __init__(self, hook_name: str, plugin: str, func: Callable, real_hook: 'RealHook',
                 req_perms: List = None, data=None):
        self.hook_name = hook_name
        self.plugin = plugin
        self.func = func
        self.perms: List = req_perms if req_perms is not None else []
        self.data = data
        self.real_hook = real_hook

    def __str__(self):
        return f"{self.hook_name}: {self.plugin}; {self.func}"


class RealHook:
    def __init__(self, init_hook: Hook, bot):
        self.errors = []
        self.bot = bot
        self.name = init_hook.hook_name
        self.plugin = init_hook.plugin
        self.func = init_hook.func
        self.perms = init_hook.perms
        self.data = init_hook.data
        self.todo = []
        self.type = self.__class__.__name__

    def __str__(self):
        return f"{self.type} '{self.name}': {self.plugin}; {self.func}"

    def fire(self, **kwargs):
        sig = inspect.signature(self.func)
        kwargs["bot"] = self.bot
        kwargs["start_time"] = self.bot.start_time
        kwargs["hook"] = self
        args = []
        for arg in sig.parameters:
            assert arg in kwargs, \
                f"Callback requested an argument that the hook launcher was not passed. it was '{arg}'"
            args.append(kwargs[arg])
        try:
            ret = self.func(*args)
            if ret:
                self.todo.append(ret)
        except Exception as e:
            self.errors.append(e)

    def handle_error(self):
        done = []
        for error in self.errors:
            self.bot.log_everywhere(f"exception in {self}. {type(error).__name__}: {str(error)}. See stdout for trace.")
            self.bot.log.exception(error)
            done.append(error)
        self.errors[:] = [e for e in self.errors if e not in done]

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
        self.handle_error()
        self.handle_return()


class MessageHook(RealHook):
    def __init__(self, init_hook: Hook, bot):
        super().__init__(init_hook, bot)
        self.msg: 'Message' = None

        # Because pycharm... again
        return

    def fire(self, **kwargs):
        self.msg = kwargs["msg"]
        super().fire(**kwargs)

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


def hook(*name, real_hook=RealHook, func=None, permissions=None, data=None) -> Callable:
    def _decorate(f):
        try:
            hook_list = getattr(f, "_IsHook")
        except AttributeError:
            hook_list = []
            setattr(f, "_IsHook", hook_list)
        # hook_list.extend((_hook.lower(), permissions) for _hook in name)
        hook_list.extend((Hook(_hook.lower(), f.__module__, f, real_hook, permissions, data) for _hook in name))
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
    return hook(f"on_load_{str(func.__module__)}", func=func)


def unload(func) -> Callable:
    return hook(f"on_unload_{func.__module__}", func=func)


def channel_init(func) -> Callable:
    return hook("channel_init", func=func)


def command(*name, perm=None) -> Callable:
    return hook(*(("cmd_" + n) for n in name), permissions=perm, real_hook=MessageHook)


def connect_finish(func) -> Callable:
    return hook("connect_finish", func=func)


def tick(func) -> Callable:
    return hook("tick", func=func)


# Timer isn't guaranteed to happen at the time, but will never be early
def timer(time) -> Callable:
    return hook(f"timer_{time}")
