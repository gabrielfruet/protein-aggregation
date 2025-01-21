import logging
from typing import Literal
import time

str_to_resolution = {
    's': 10e-9,
    'ms': 10e-6,
    'ns': 1
}

class TimerLogger:
    def __init__(self, 
                 logger: logging.Logger,
                 level: int = logging.INFO,
                 msg: str = '{task} took {time}',
                 resolution: Literal['s', 'ms', 'ns'] = 's'):
        self.logger = logger
        self.level = level
        self.timers: dict[str, tuple[str,int]] = {}
        self.format_msg = msg
        self.resolution_str = resolution
        self.resolution = str_to_resolution[resolution]

    def start(self, task='[Not specified]', timer='base'):
        self.timers[timer] = (task, time.perf_counter_ns())

    def end(self, timer='base'):
        task, start = self.timers[timer]
        elapsed_time = (time.perf_counter_ns() - start) * self.resolution
        msg = self.format_msg.format(task=task, time=f'{elapsed_time:.2f} {self.resolution_str}')
        self.logger.log(self.level, msg)
