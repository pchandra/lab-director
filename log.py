import os
import sys
from datetime import datetime

class Logger:
    def __init__(self, name='log'):
        self.name = name
        self.pid = os.getpid()

    def info(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sys.stdout.write(f"[{timestamp}] [{self.name}-{self.pid}] {msg}\n")
        sys.stdout.flush()

    def warn(self, msg):
        self.info("WARN: " + msg)

    def debug(self, msg):
        self.info("DEBUG: " + msg)
