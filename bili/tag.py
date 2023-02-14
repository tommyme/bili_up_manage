import pickle
import os
from typing import DefaultDict, Dict

class Addict(DefaultDict):
    def __init__(self, *args, **kwargs):
        super().__init__(Addict, *args, **kwargs)
        self.elements = []
# tree = lambda: collections.defaultdict(tree)


