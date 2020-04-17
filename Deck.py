from Pool import *


class Deck:
    def __init__(self):
        self.cards = []
        # TODO: cube is a singleton format, but support for multiple copies of a card should be implemented.

    def __len__(self):
        return len(self.cards)

    def __contains__(self, item):
        return item in self.cards


def moduleTest():
    pool = Pool(expacs=["Basic", "Standard", "Darkness Evolved"], token=False)
