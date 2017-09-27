from hook import tick, load, hook
import time

last = 0


@tick
def watchdog(bot):
    global last
    now = time.time()
    if last == 0 and now - bot.start_time < 25:
        last = bot.start_time
        startup_time = round(now - bot.start_time, 3)
        bot.log.debug(f"Startup took {startup_time}s.")
    elif last != 0 and now - last > 1.5:
        exec_time = round(now - last, 3)
        bot.log_everywhere(f"WARNING: Something is talking too long. Tick took {exec_time}s.")
    last = time.time()


@tick
def run_timer_hooks(bot):
    now = time.time()
    nowint = int(now)
    if int(now) % 5 == 0:
        bot.call_hook("timer_5s", now=now)
    if nowint % 30 == 0:
        bot.call_hook("timer_30s", now=now)
    if nowint % 60 == 0:
        bot.call_hook("timer_60s", now=now)
