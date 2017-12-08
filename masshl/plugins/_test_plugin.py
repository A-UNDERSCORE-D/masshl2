from masshl.hook import load


@load
def on_load():
    return "Loaded"
