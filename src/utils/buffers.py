"""Thread-safe buffer utilities for data sharing between threads."""

import queue
from collections import deque
from typing import Any, Optional
import numpy as np


class DataQueue:
    """Thread-safe queue wrapper for passing data between threads."""

    def __init__(self, maxsize: int = 0):
        self._queue = queue.Queue(maxsize=maxsize)

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Put item in queue."""
        self._queue.put(item, block=block, timeout=timeout)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue."""
        return self._queue.get(block=block, timeout=timeout)

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()


class RollingBuffer:
    """Fixed-size rolling buffer for real-time display."""

    def __init__(self, maxlen: int):
        self.time = deque(maxlen=maxlen)
        self.ch0 = deque(maxlen=maxlen)
        self.ch1 = deque(maxlen=maxlen)
        self.maxlen = maxlen

    def append(self, time_val: float, ch0_val: float, ch1_val: float):
        """Append new data point."""
        self.time.append(time_val)
        self.ch0.append(ch0_val)
        self.ch1.append(ch1_val)

    def extend(self, time_arr: np.ndarray, ch0_arr: np.ndarray, ch1_arr: np.ndarray):
        """Extend buffer with arrays."""
        for t, c0, c1 in zip(time_arr, ch0_arr, ch1_arr):
            self.time.append(t)
            self.ch0.append(c0)
            self.ch1.append(c1)

    def get_arrays(self) -> tuple:
        """Get buffer contents as numpy arrays."""
        return (
            np.array(self.time),
            np.array(self.ch0),
            np.array(self.ch1)
        )

    def clear(self):
        """Clear buffer."""
        self.time.clear()
        self.ch0.clear()
        self.ch1.clear()
