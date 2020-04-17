from Card import *
import random
import json


class Pool:
    def __init__(self, expacs=[''], token=True):
        try:
            sets = ["Basic", "Standard Card Pack", "Darkness Evolved", "Rage of Bahamut", "Tempest of the Gods",
                    "Wonderland Dreams", "Starforged Legends", "Chronogenesis", "Dawnbreak Nightedge",
                    "Brigade of the Sky", "Omen of the Ten", "Altersphere", "Steel Rebellion", "Rebirth of Glory",
                    "Verdant Conflict", "Ultimate Colosseum", "World Uprooted"]
            assert [i in sets + [''] for i in expacs]
        except AssertionError:
            print("Invalid expansion name!")

        self.cards = {}  # Key: card name - Value: the relative Card object.
        self.nameToIndex = {}  # One-to-one maps card names to integers.
        with open("en.json", 'r') as f:
            data = json.load(f)
            count = 0
            for i in data:
                if data[i]["expansion"] == 'Token' and not token \
                        or data[i]["expansion"] not in expacs and expacs != ['']:
                    pass
                else:
                    self.cards[data[i]["name"]] = Card(data[i])
                    self.nameToIndex[data[i]["name"]] = count
                    count += 1
        self.indexToName = {i: j for j, i in self.nameToIndex.items()}  # Reverses nameToIndex's mapping.
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

    def get_card_name(self, index):
        return self.indexToName[index]

    def get_card_index(self, name):
        return self.nameToIndex[name]

    def get_random_card(self):
        return self.cards[random.choice(list(self.cards.keys()))].name

    def search_by_name(self, text, maxMatches=99):
        text = text.lower()
        result = []
        for i in self.cards:
            if text in i.lower():
                result.append(i)
            if len(result) > maxMatches:
                return []
        return result

    def search_by_attributes(self, *attributes, maxMatches=99):
        attributes = list(attributes)
        result = []
        for i in self.cards:
            if False not in [j in self.cards[i].searchable for j in attributes]:
                result.append(i)
            if len(result) > maxMatches:
                return []
        return result


def moduleTest():
    def printFunctionTest(text, f, *args):
        print('\n' + text)
        print("inputs: {}\noutput: {}".format(list(args), f(*args)))
    p = Pool()
    printFunctionTest("", p.search_by_attributes, "devil", "of", "love")
    printFunctionTest("Random card:", p.get_random_card)
    printFunctionTest("Name search, single result:", p.search_by_name, "roly", 2)
    printFunctionTest("Name search, multiple result:", p.search_by_name, "tia", 99)
    printFunctionTest("Name search, results over threshold:", p.search_by_name, "a", 4)
    printFunctionTest("Search by attributes, single result:", p.search_by_attributes, "2/2", "blood", "gold", "bat")
    printFunctionTest("Search by attributes, multiple results:", p.search_by_attributes, "7/4")
    print("\n{}'s index: {}".format("Robogoblin", p.get_card_index("Robogoblin")))
    print("\nName of card #{}: {}".format(167, p.get_card_name(167)))
    print("\nLoading the database up to DE and printing the first 10 cards by index:")
    p = Pool(expacs=["Basic", "Standard", "Darkness Evolved"], token=False)
    for i in range(10):
        print("{} (from {})".format(p.get_card_name(i), p.cards[p.get_card_name(i)].expac))
