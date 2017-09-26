from hook import tick, load
import time

last = 0


@tick
def tick_test(bot):
    global last
    now = time.time()
    if last == 0 and now - bot.start_time < 25:
        last = bot.start_time
        bot.log(f"Startup took {now - bot.start_time}s")
    elif now - last > 1.5:
        bot.log_everywhere(f"WARNING: Something is talking too long. Tick took {now - last}s.")
    last = time.time()
