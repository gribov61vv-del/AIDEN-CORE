from .reasoning import Reasoning
from .memory import MemoryModule

class PikachuCore:
    def __init__(self):
        self.reasoning = Reasoning()
        self.memory = MemoryModule()

    def think(self, q):
        return self.reasoning.think(q)
