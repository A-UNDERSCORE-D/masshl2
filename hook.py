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
# TODO: Hook object with the plugin name one it, this removes a level to the hook dict
