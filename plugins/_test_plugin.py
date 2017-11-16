from hook import load


@load
def on_load():
    return "Loaded"
