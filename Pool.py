import random
import os
import json
from fuzzywuzzy import fuzz

MAX_MATCHES = 15


class TooManyMatches(Exception):
    def __init__(self, matches):
        self.matches = matches


class Pool:
    def __init__(self):
        with open(f'{os.getcwd()}/shadowverse-json/all.json', 'r') as f:
            self.p = json.load(f)

    def searchable(self, name):
        c = self.p[name]
        return f'{c["pp_"]}pp {c["rarity_"]} {c["craft_"]} {c["trait_"]} {c["type_"]} {c["expansion_"]} ' \
               f'{c["baseAtk_"]}/{c["baseDef_"]} {"Rotation" if c["rotation_"] else "Unlimited"} ' \
               f'{c["baseEffect_"]} {c["evoEffect_"]}'.lower()

    def pic(self, name, evo: bool):
        return f'https://sv.bagoum.com/cardF/en/{"e" if evo else "c"}/{self.p[name]["id_"]}'

    def get_random_card(self):
        return self.p[random.choice(list(self.p.keys()))]["name_"]

    def search_by_name(self, text, max_matches=MAX_MATCHES, similarity_threshold=70):
        text = text.lower()
        result = []
        fuzzy_result = []
        for i in self.p:
            similarity = fuzz.partial_ratio(text, i.lower())
            if text in i.lower():
                result.append(i)
            if similarity > similarity_threshold:
                fuzzy_result.append(i)
        if not result:
            return fuzzy_result
        if len(result) > max_matches:
            raise TooManyMatches(len(result))
        return result

    def search_by_attributes(self, attributes: str, max_matches=MAX_MATCHES):
        result = []
        for card in self.p:
            if all(attr in self.searchable(card) for attr in attributes.lower().split(' ')):
                result.append(card)
        if len(result) > max_matches:
            raise TooManyMatches(len(result))
        return result


def module_test():
    p = Pool()
    print(p.searchable("Robogoblin"))
    print(p.get_random_card())
    print(p.search_by_name("Vania"))
    print(p.search_by_name("Abominecion"))
    try:
        print(p.search_by_attributes("2/2"))
    except TooManyMatches as t:
        print(f'found {t.matches} matches')
    print(p.search_by_attributes("2/2 gold neutral banish"))
    print(p.pic("Goblin", True))
    print(p.search_by_attributes("7/4"))
    print(p.searchable("Hulking Dragonewt"))

# module_test()
