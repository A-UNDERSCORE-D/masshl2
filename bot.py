from connection import Connection
from config import Config
import time


class Bot:
    def __init__(self, selector):
        self.connections = []
        self.selector = selector
        self.config = Config()
        self.running = False

    def run(self):
        self.connections.append(Connection(config=self.config,
                                           selector=self.selector,
                                           bot=self))
        for connection in self.connections:
            connection.connect()

        self.running = True

        while self.running:
            event = self.selector.select(1)
            for file, _ in event:
                file.fileobj.read()

    def stop(self, reason):
        for connection in self.connections:
            connection.quit(reason)
            time.sleep(1)
            connection.close()
        self.running = False
