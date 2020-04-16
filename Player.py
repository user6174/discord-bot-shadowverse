from Deck import *


class Player:
    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.mainDeck = []
        self.sideBoard = []
        self.picks = []
