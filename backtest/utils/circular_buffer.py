import numpy as np

class CircularBuffer:
    def __init__(self, size):
        self.buffer = np.empty(size)
        self.index = 0
        self.size = size
        self.full = False

    def append(self, value):
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.size
        if self.index == 0:
            self.full = True

    def latest(self):
        return self.buffer[(self.index - 1)] % self.size

    def to_array(self):
        if not self.full:
            return self.buffer[:self.index]
        return np.concatenate(self.buffer[self.index:], self.buffer[:self.index])

    def __getitem__(self, idx):
        if not self.full and idx >= self.index:
            raise IndexError("index out of range")
        return self.buffer[(idx + self.index) % self.size]