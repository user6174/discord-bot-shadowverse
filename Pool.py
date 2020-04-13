from Card import *
import random
import json


class Pool:

    def __init__(self):
        self.cards = {}
        with open("en.json", 'r') as f:
            data = json.load(f)
            for i in data:
                self.cards[data[i]["name"]] = Card(data[i])

    """
    data is a list of dictionaries (cards), whose key is the card name. Example:
    >>> data["Robogoblin"].keys()
        dict_keys(['name', '_name', 'id', 'faction', '_faction', 'rarity', '_rarity', 'race', 'expansion', '_expansion',
        'type', '_type', 'hasEvo', 'hasAlt', 'hasAlt2', 'manaCost', 'baseData', 'evoData', 'rot', 'searchableText'])
    Note that baseData and evoData are dictionaries themselves:
    >>> data["Robogoblin"]["evoData"].keys()
        dict_keys(['description', 'flair', 'attack', 'defense'])
    """

    def __getitem__(self, key):
        return self.cards[key]

    def __iter__(self):
        return enumerate(self.cards)

    def __contains__(self, item):
        return item in self.cards

    def get_random_card(self):
        return self.cards[random.choice(list(self.cards.keys()))].name

    def search(self, card, maxMatches):
        card = card.lower()
        result = []
        for i in self.cards:
            if card in i.lower():
                result.append(i)
            if len(result) > maxMatches:
                return []
        return result
