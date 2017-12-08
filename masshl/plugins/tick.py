from masshl.hook import tick
import time

last = 0


@tick
def watchdog(bot):
    global last
    now = time.time()
    if last == 0 and now - bot.start_time < 25:  # the 25 is in case we're reloaded
        last = bot.start_time
        startup_time = round(now - bot.start_time, 3)
        bot.log.debug(f"Startup took {startup_time}s.")
    elif last != 0 and now - last > 1.5:
        exec_time = round(now - last, 3)
        bot.log_everywhere(f"WARNING: Something is taking too long. Tick took {exec_time}s.")
    last = time.time()


@tick
def run_timer_hooks(bot):
    now = int(time.time())
    for h in bot.event_manager.events.keys():
        if h.startswith("timer_") and now % int(h.split("_")[1]) == 0:
            bot.call_hook(h, now=now)
