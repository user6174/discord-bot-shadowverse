from Card import *
import random
import os
import json
from fuzzywuzzy import fuzz


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
        self.name_to_index = {}  # One-to-one maps card names to integers.
        with open("en.json", 'r') as f:
            data = json.load(f)
            count = 0
            for i in data:
                if data[i]["expansion"] == 'Token' and not token \
                        or data[i]["expansion"] not in expacs and expacs != ['']:
                    pass
                else:
                    self.cards[data[i]["name"]] = Card(data[i])
                    self.name_to_index[data[i]["name"]] = count
                    count += 1
        self.index_to_name = {i: j for j, i in self.name_to_index.items()}  # Reverses nameToIndex's mapping.

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
        return self.index_to_name[index]

    def get_card_index(self, name):
        return self.name_to_index[name]

    def get_random_card(self):
        return self.cards[random.choice(list(self.cards.keys()))].name

    def search_by_name(self, text, max_matches=99, similarity_threshold=70):
        text = text.lower()
        result = []
        fuzzy_result = []
        for i in self.cards:
            similarity = fuzz.partial_ratio(text, i.lower())
            if text in i.lower():
                result.append(i)
            if similarity > similarity_threshold:
                fuzzy_result.append(i)
        if not result:
            return fuzzy_result
        if len(result) > max_matches:
            return len(result)
        return result

    def search_by_attributes(self, *attributes: list, max_matches=99):
        result = []
        for i in self.cards:
            if False not in [j in self.cards[i].searchable for j in attributes]:
                result.append(i)
        if len(result) > max_matches:
            return len(result)
        return result


def assets_downloader():
    from urllib.request import urlretrieve
    p = Pool()
    for i in p.cards:
        if not os.path.exists("assets/{}.jpg".format(p[i].id)):
            urlretrieve(p[i].pic, "assets/{}.jpg".format(p[i].id))
            print(i)


def grid_merge(*images, scaling=200, row_length=4):
    from PIL import Image
    from time import time
    pool = Pool()
    images = [Image.open("assets/" + pool[i].id + ".jpg") for i in images]
    images = [i.resize((scaling, int(i.size[1] / i.size[0] * scaling))) for i in images]
    max_w = max([i.size[0] for i in images])
    max_h = max([i.size[1] for i in images])
    result_w = min(len(images), row_length) * max_w
    result_h = (len(images) // row_length + 1) * max_h
    result = Image.new('RGBA', (result_w, result_h))
    for i in range(len(images)):
        result.paste(im=images[i], box=((i % row_length) * max_w, (i // row_length) * max_h))
    filename = str(int(time()))
    result.save(filename + '.png')

    return filename + '.png'


def module_test():
    def print_function_test(text, f, *args):
        print('\n' + text)
        print("inputs: {}\noutput: {}".format(list(args), f(*args)))

    p = Pool()
    print("Testing Card.py:\n", p["Robogoblin"])
    print_function_test("Random card:", p.get_random_card)
    print_function_test("Name search, single result:", p.search_by_name, "roly", 2)
    print_function_test("Name search, single result, with typo:", p.search_by_name, "rolyy", 2)
    print_function_test("Name search, multiple results:", p.search_by_name, "tia", 99)
    print_function_test("Name search, multiple results, with typo:", p.search_by_name, "gablin", 99)
    print_function_test("Name search, results over threshold:", p.search_by_name, "a", 4)
    print_function_test("Search by attributes, single result:", p.search_by_attributes, "2/2", "blood", "gold", "bat")
    print_function_test("Search by attributes, multiple results:", p.search_by_attributes, "7/4")
    print("\n{}'s index: {}".format("Robogoblin", p.get_card_index("Robogoblin")))
    print("\nName of card #{}: {}".format(167, p.get_card_name(167)))
    print("\nLoading the database up to DE and printing the first 10 cards by index:")
    p = Pool(expacs=["Basic", "Standard", "Darkness Evolved"], token=False)
    for i in range(10):
        print("{} (from {})".format(p.get_card_name(i), p.cards[p.get_card_name(i)].expac))


# inmodule_test()
